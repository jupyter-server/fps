import logging

from fastapi import FastAPI

from fps.config import Config, FPSConfig
from fps.logging import configure_logger
from fps.plugins import load_configurations, load_routers


def create_app():

    logging.getLogger("fps")
    configure_logger(logging.root.manager.loggerDict.keys())

    load_configurations()

    fps_config = Config(FPSConfig)
    app = FastAPI(**fps_config.__dict__)

    load_routers(app)

    return app


app = create_app()
