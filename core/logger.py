from __future__ import annotations
import logging


def get_logger(logger_name: str) -> logging.Logger:
    
    log = logging.getLogger(logger_name)
    log.setLevel(logging.DEBUG)

    if not log.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(filename)s::%(funcName)s:%(lineno)d — %(message)s")
        handler.setFormatter(formatter)
        log.addHandler(handler)

    log.propagate = False

    return log


log = get_logger("Playblast")
