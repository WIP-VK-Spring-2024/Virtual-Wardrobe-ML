"""Try on worker for read task queue."""

from typing import BinaryIO

from app.internal.repository.rabbitmq.try_on_task import TryOnTaskRepository
from app.internal.repository.rabbitmq.try_on_response import TryOnRespRepository
from app.internal.services import AmazonS3Service
from app.pkg.models import TryOnResponseCmd, ImageCategory
from app.pkg.logger import get_logger
from app.pkg.settings import settings

logger = get_logger(__name__)

class TryOnWorker:
    """Model worker for read task queue."""

    task_repository: TryOnTaskRepository
    resp_repository: TryOnRespRepository
    file_service: AmazonS3Service


    def __init__(
        self,
        task_repository: TryOnTaskRepository,
        resp_repository: TryOnRespRepository,
        file_service: AmazonS3Service,
        clothes_model: None,
        human_model,
        try_on_model,
    ):
        self.task_repository = task_repository
        self.resp_repository = resp_repository
        self.file_service = file_service
    
        self.clothes_model = clothes_model
        self.human_model = human_model
        self.try_on_model = try_on_model

    async def listen_queue(self):
        logger.info("Starting listen queue...")

        async for message in self.task_repository.read():
            logger.info("New message [%s]", message)

            user_image = self.file_service.read(
                file_name=message.user_image_id,
                folder=message.user_image_dir,
            )

            clothes_image = self.file_service.read(
                file_name=message.clothes_id,
                folder=message.clothes_dir,
            )

            logger.info(
                "Starting try on pipeline clothes id: [%s]",
                message.clothes_id,
            )
            # Model pipeline           
            try_on = self.pipeline(
                category=message.category,
                clothes_image=clothes_image,
                user_image=user_image,
            )

            # Save result
            res_file_name = f"{message.clothes_id}"
            res_file_dir = f"{settings.ML.TRY_ON_DIR}/{message.user_image_id}"

            self.file_service.upload(
                file=try_on,
                file_name=res_file_name,
                folder=res_file_dir,
            )
            
            logger.info(
                "Try on result file name [%s], dir [%s]",
                res_file_name,
                res_file_dir,
            )
            cmd = TryOnResponseCmd(
                **message.dict(),
                try_on_result_id=res_file_name,
                try_on_result_dir=res_file_dir,
            )
            await self.resp_repository.create(cmd=cmd)

    def pipeline(self, category: ImageCategory, clothes_image: BinaryIO, user_image: BinaryIO) -> BinaryIO:
        """ Try on model pipeline
        Attributes:
            category: ImageCategory, category of clothes image to try on
            clothes_image: BinaryIO, cutted image for processing
            user_image: BinaryIO, user image for processing
        """
        # # Human processing
        # processed_user = self.human_model.consistent_forward(user_image)
        # logger.debug("End human processing, result: [%s]", processed_user["parse_orig"])
        
        # # Try on
        # processed_user.update(
        #     {
        #         "category": category.value,
        #         "cloth": clothes_image,
        #     }
        # )
        # try_on = self.try_on_model(processed_user)
        # logger.info("End try on, result: [%s]", try_on)

        return clothes_image