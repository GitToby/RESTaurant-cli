from pathlib import Path
from typing import Annotated

from loguru import logger
from pydantic import BaseModel, Field

APP_ROOT = Path(__file__).parent.parent

APP_NAME = "rqstr"
DEFAULT_OUT_DIR = APP_ROOT.parent / "out"

if not DEFAULT_OUT_DIR.exists():
    logger.info(f"Creating default output directory: {DEFAULT_OUT_DIR}")
    DEFAULT_OUT_DIR.mkdir()

RESOURCES_DIR = APP_ROOT / "resources"


class GlobalConfig(BaseModel):
    output_dir: Annotated[Path, Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))]
