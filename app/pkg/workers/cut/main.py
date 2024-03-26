"""Main module for start cut model task worker."""

import asyncio

from app.internal.repository.rabbitmq.cut_task import CutTaskRepository
from app.internal.repository.rabbitmq.cut_response import CutRespRepository
from app.pkg.workers.cut.worker import CutWorker
from app.internal.services import AmazonS3Service
from app.pkg.logger import get_logger

logger = get_logger(__name__)

__all__ = ["start_worker"]


def start_worker():
    logger.info("Starting initialization...")
    task_repository = CutTaskRepository()
    resp_repository = CutRespRepository()
    file_service = AmazonS3Service()

    # clothes_model = ClothProcessor()
    clothes_model = None

    model_worker = CutWorker(
        task_repository=task_repository,
        resp_repository=resp_repository,
        file_service=file_service,
        clothes_model=clothes_model,
    )
    logger.info("Successfuly initializated.")
    asyncio.run(model_worker.listen_queue())


if __name__ == "__main__":
    start_worker()