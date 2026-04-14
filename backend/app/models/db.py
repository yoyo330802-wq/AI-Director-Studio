"""
数据库连接管理 - 统一入口
委托给 app.database
"""
from app.database import get_session, init_db, close_db

# 兼容旧代码: get_db -> get_session
get_db = get_session

__all__ = ["get_session", "get_db", "init_db", "close_db"]
