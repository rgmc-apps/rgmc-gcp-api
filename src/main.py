import os
import time
from src.logger import logger
from typing import Any, Callable
from fastapi import FastAPI, Request
from src import __version__, __project_id__

api = FastAPI(title=f"RGMC API Swagger: {__project_id__}", version=__version__)

@api.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable) -> Any:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@api.get("/index")
def index():
    logger.info("Index endpoint called")
    return {"status": "Api is running"}