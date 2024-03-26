"""Cut worker for read task queue."""

from typing import BinaryIO

from app.internal.repository.rabbitmq.cut_task import CutTaskRepository
from app.internal.repository.rabbitmq.cut_response import CutRespRepository
from app.internal.services import AmazonS3Service
from app.pkg.models import CutResponseCmd
from app.pkg.logger import get_logger
from app.pkg.settings import settings

logger = get_logger(__name__)

class CutWorker:
    """Model worker for read task queue."""

    task_repository: CutTaskRepository
    resp_repository: CutRespRepository
    file_service: AmazonS3Service


    def __init__(
        self,
        task_repository: CutTaskRepository,
        resp_repository: CutRespRepository,
        file_service: AmazonS3Service,
        clothes_model,
    ):
        self.task_repository = task_repository
        self.resp_repository = resp_repository
        self.file_service = file_service
    
        self.clothes_model = clothes_model

    async def listen_queue(self):
        logger.info("Starting listen queue...")

        async for message in self.task_repository.read():
            logger.info("New message [%s]", message)

            clothes_image = self.file_service.read(
                file_name=message.clothes_id,
                folder=message.clothes_dir,
            )

            logger.info(
                "Starting try on pipeline clothes id: [%s]",
                message.clothes_id,
            )
            # Model pipeline           
            # cutted_clothes = self.pipeline(clothes_image=clothes_image)
            cutted_clothes = clothes_image

            # Save result
            res_file_name = message.clothes_id
            res_file_dir = settings.ML.CUT_DIR

            self.file_service.upload(
                file=cutted_clothes,
                file_name=res_file_name,
                folder=res_file_dir,
            )
            
            logger.info(
                "Cut result file name [%s], dir [%s]",
                res_file_name,
                res_file_dir,
            )
            cmd = CutResponseCmd(
                **message.dict(),
                result_dir=res_file_dir,
            )
            await self.resp_repository.create(cmd=cmd)

    def pipeline(self, clothes_image: BinaryIO) -> BinaryIO:
        # Remove model background
        cutted_clothes = self.clothes_model.consistent_forward(clothes_image)
        logger.debug("End removed background, result: [%s].", cutted_clothes["cloth"])
        
        return cutted_clothes["cloth"]