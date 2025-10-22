import importlib.metadata
import os
from pathlib import Path

APP_NAME = "AutoCana"
VERSION = importlib.metadata.version(APP_NAME.lower())
CONFIG_PATH = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME.lower()
CONFIG_FILE_PATH = CONFIG_PATH / "config.yaml"

TEMPLATE_PATH = "autocana/templates/invoice.docx"
