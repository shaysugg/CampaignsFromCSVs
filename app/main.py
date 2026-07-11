from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app import routes as campaign_routes
from app.db import create_tables, get_redis
from app.tasks import c


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    get_redis().close()


app = FastAPI(lifespan=lifespan)

app.include_router(campaign_routes.router)


@app.get("/status/{task_id}")
def task_status(task_id: str):
    from celery.result import AsyncResult

    r: AsyncResult = c.AsyncResult(task_id)

    return JSONResponse(content={"id": task_id, "status": r.state})


# create campaigns
