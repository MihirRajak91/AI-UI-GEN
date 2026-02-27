import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGER_NAME = "uiagent"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 5


def _log_file_path() -> Path:
    tools_dir = Path(__file__).resolve().parents[2]
    log_dir = tools_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "uia.log"


def get_logger(name: str) -> logging.Logger:
    root_logger = logging.getLogger(_LOGGER_NAME)

    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            _log_file_path(),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.propagate = False

    return root_logger.getChild(name)
