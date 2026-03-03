import logging

from fastapi import FastAPI

from .db import Base, engine
from .routes import api_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="NetZero AI Self-Assessment Backend",
        version="0.1.0",
    )

    # In dev we auto-create tables. For production, use migrations instead.
    @app.on_event("startup")
    def on_startup() -> None:  # noqa: D401
        """
        Application startup hook for dev environment.
        """
        logger.info("Creating database tables (dev-only).")
        Base.metadata.create_all(bind=engine)

    @app.get("/")
    def root() -> dict:
        return {"message": "NetZero AI backend running"}

    app.include_router(api_router)

    return app


app = create_app()

