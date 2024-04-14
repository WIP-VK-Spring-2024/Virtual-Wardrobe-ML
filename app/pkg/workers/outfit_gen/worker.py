"""Rec sys worker for read task queue."""

from io import BytesIO
from typing import BinaryIO, List, Dict
from uuid import uuid4

import pydantic

from app.internal.repository.rabbitmq.outfit_gen_task import OutfitGenTaskRepository
from app.internal.repository.rabbitmq.outfit_gen_response import OutfitGenRespRepository
from app.internal.services import AmazonS3Service
from app.pkg.models import OutfitGenClothes, OutfitGenResponseCmd, ImageCategoryAutoset, OutfitGenClothes, Outfit
from app.pkg.logger import get_logger
from app.pkg.ml.auto_clothing_set.autoset import LocalRecSys
from app.pkg.settings import settings

logger = get_logger(__name__)

class OutfitGenWorker:
    """Model worker for read task queue."""

    task_repository: OutfitGenTaskRepository
    resp_repository: OutfitGenRespRepository
    file_service: AmazonS3Service
    outfit_gen_model: LocalRecSys


    def __init__(
        self,
        task_repository: OutfitGenTaskRepository,
        resp_repository: OutfitGenRespRepository,
        file_service: AmazonS3Service,
        outfit_gen_model: LocalRecSys
    ):
        self.task_repository = task_repository
        self.resp_repository = resp_repository
        self.file_service = file_service
    
        self.outfit_gen_model = outfit_gen_model

    async def listen_queue(self):
        logger.info("Starting listen queue...")

        async for message in self.task_repository.read():
            logger.info("New message [%s]", message)

            data = self.read_clothes(
                message.clothes,
                folder=settings.CUT_DIR,
            )

            logger.info("Starting try on pipeline")
            # Model pipeline           
            outfits = self.pipeline(
                data=data,
                prompt=message.prompt,
                amount=message.amount,
            )
            logger.debug("End pipeline, result: [%s]", outfits)

            cmd = OutfitGenResponseCmd(
                user_id=message.user_id,
                outfits=outfits,
            )
            logger.info("Result model: [%s]", cmd)

            await self.resp_repository.create(cmd=cmd)

    def read_clothes(
        self,
        clothes: List[OutfitGenClothes],
        folder: str
    ) -> Dict[ImageCategoryAutoset, List[Dict[Dict[str, uuid4], Dict[str, BytesIO]]]]:
        """Read clothes from file service in correct order"""
        result = {
            ImageCategoryAutoset.UPPER_BODY: [],
            ImageCategoryAutoset.LOWER_BODY: [],
            ImageCategoryAutoset.DRESSES: [],
            ImageCategoryAutoset.OUTWEAR: [],
        }

        for clothe in clothes:
            category = ImageCategoryAutoset(clothe.category)
            image = self.file_service.read(
                file_name=clothe.clothes_id,
                folder=folder,
            )
            clothe = {
                'cloth': image,
                'clothes_id': clothe.clothes_id,
            }

            result[category].append(clothe)
    
        return result
    

    def pipeline(
        self,
        data: Dict[ImageCategoryAutoset, List[Dict[Dict[str, uuid4], Dict[str, BytesIO]]]],
        prompt: str = None,
        amount: int = 10,
    ) -> List[OutfitGenClothes]:
        # Local autoset gen

        outfits = self.outfit_gen_model.forward(
            upper_clothes=data[ImageCategoryAutoset.UPPER_BODY],
            lower_clothes=data[ImageCategoryAutoset.LOWER_BODY],
            dresses_clothes=data[ImageCategoryAutoset.DRESSES],
            outerwear_clothes=data[ImageCategoryAutoset.OUTWEAR],
            prompt=prompt,
            sample_amount=amount,
        )
        logger.debug("End autoset gen, result: [%s]", outfits)

        result_outfits = []
        for outfit in outfits:
            clothes = []
            for cloth in outfit['clothes']:
                outfit_gen_clothes = OutfitGenClothes(
                    clothes_id=cloth['clothes_id'],
                )
                clothes.append(outfit_gen_clothes)

            cur_outfit = Outfit(clothes=clothes)
            result_outfits.append(cur_outfit)

        return result_outfits