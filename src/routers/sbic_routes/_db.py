"""Shared SBIC DB engine."""
from src.db.dbconn import DbConn
from src.logger import logger

_sbic_engine = None


def get_sbic_engine():
    global _sbic_engine
    if _sbic_engine is None:
        _sbic_engine = DbConn(logger, 'sbic').main()
    return _sbic_engine
