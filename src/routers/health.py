from datetime import datetime

from fastapi import APIRouter

from src.config import __version__
from src.logger import logger
from src.types_py import HealthcheckResponse

healthrouter = APIRouter()


@healthrouter.get("/healthcheck", response_model=HealthcheckResponse, tags=["health"])
def healthcheck() -> HealthcheckResponse:
    message = "We're on the air."
    time = datetime.now()
    logger.info(msg=message, extra={"version": __version__, "time": time})
    return HealthcheckResponse(
        message=message, version=__version__, time=datetime.now()
    )