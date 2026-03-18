import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .routes import api_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NetZero AI Self-Assessment Backend",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # In dev we auto-create tables. For production, use migrations instead.
    @app.on_event("startup")
    def on_startup() -> None:  # noqa: D401
        """
        Application startup hook for dev environment.
        """
        env = settings.ENVIRONMENT
        logger.info("Application startup in environment=%s", env)
        if env in ("development", "local"):
            logger.info("Creating DB tables (development only)")
            Base.metadata.create_all(bind=engine)
        else:
            logger.info("Skipping automatic table creation; managed externally.")

    @app.get("/")
    def root() -> dict:
        return {"message": "NetZero AI backend running"}

    app.include_router(api_router)

    return app


app = create_app()

