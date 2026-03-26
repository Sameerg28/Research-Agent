import logging
import json
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    """Configure logging — writes raw outputs and errors to /logs/"""
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # Root logger
    logging.basicConfig(level=logging.WARNING, format=log_format)

    # Raw outputs logger
    raw_logger = logging.getLogger("erisia.raw")
    raw_logger.setLevel(logging.DEBUG)
    raw_handler = logging.FileHandler(LOGS_DIR / "raw_outputs.log", encoding="utf-8")
    raw_handler.setFormatter(logging.Formatter(log_format))
    raw_logger.addHandler(raw_handler)

    # Error logger
    error_logger = logging.getLogger("erisia.errors")
    error_logger.setLevel(logging.WARNING)
    error_handler = logging.FileHandler(LOGS_DIR / "errors.log", encoding="utf-8")
    error_handler.setFormatter(logging.Formatter(log_format))
    error_logger.addHandler(error_handler)

    # API logger
    api_logger = logging.getLogger("core.api")
    api_logger.setLevel(logging.DEBUG)
    api_logger.addHandler(raw_handler)


def log_result(data: dict, paper_path: str, mode: str):
    """Log a successful result to raw_outputs.log"""
    logger = logging.getLogger("erisia.raw")
    logger.info(
        f"SUCCESS | paper={paper_path} | mode={mode} | title={data.get('paper_title', '?')}"
    )


def log_error(error: Exception, paper_path: str, attempt: int):
    """Log a failure to errors.log"""
    logger = logging.getLogger("erisia.errors")
    logger.error(
        f"FAILED | paper={paper_path} | attempt={attempt} | error={type(error).__name__}: {error}"
    )