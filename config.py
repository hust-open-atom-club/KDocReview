from loguru import logger
import rtoml


logger.add("logs/latest.log", level="DEBUG")

with open("data/config.toml", "r") as f:
    config : dict = rtoml.loads(f.read())

API_URL = config["common"]["api"]
