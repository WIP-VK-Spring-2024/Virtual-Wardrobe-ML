"""Main module for start try on model task worker."""

import asyncio

from app.internal.repository.rabbitmq.try_on_task import TryOnTaskRepository
from app.internal.repository.rabbitmq.try_on_response import TryOnRespRepository
from app.pkg.workers.try_on.worker import TryOnWorker
from app.internal.services import AmazonS3Service
from app.pkg.logger import get_logger

logger = get_logger(__name__)

__all__ = ["start_worker"]


def start_worker():
    logger.info("Starting initialization...")
    task_repository = TryOnTaskRepository()
    resp_repository = TryOnRespRepository()
    file_service = AmazonS3Service()

    # clothes_model = ClothProcessor()
    # human_model = HumanProcessor()
    # try_on_model = LadyVtonAggregator()

    clothes_model = None
    human_model = None
    try_on_model = None

    model_worker = TryOnWorker(
        task_repository=task_repository,
        resp_repository=resp_repository,
        file_service=file_service,
        clothes_model=clothes_model,
        human_model=human_model,
        try_on_model=try_on_model,
    )
    logger.info("Successfuly initializated.")
    asyncio.run(model_worker.listen_queue())


if __name__ == "__main__":
    start_worker()