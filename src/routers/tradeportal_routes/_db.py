"""Shared Trade Portal DB engine."""
from src.db.dbconn import DbConn
from src.logger import logger

_tp_engine = None


def get_tp_engine():
    global _tp_engine
    if _tp_engine is None:
        _tp_engine = DbConn(logger, 'tradeportal').main()
    return _tp_engine
