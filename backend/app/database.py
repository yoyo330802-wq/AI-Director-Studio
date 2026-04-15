# 数据库连接配置

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from app.config import settings

# 判断是否异步数据库
is_async_db = "+aiosqlite" in settings.DATABASE_URL or "+asyncpg" in settings.DATABASE_URL

if is_async_db:
    from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
    _async_engine: AsyncEngine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
    )
    AsyncSessionLocal = sessionmaker(
        _async_engine, class_=AsyncSession, expire_on_commit=False
    )
    engine = None
    SessionLocal = None
else:
    # 同步引擎 (支持 SQLite for dev)
    engine = create_engine(
        settings.DATABASE_URL.replace("sqlite:///", "sqlite:///"),
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _async_engine = None
    AsyncSessionLocal = None


async def init_db():
    """初始化数据库 - 创建所有表"""
    from app.models.user import User
    from app.models.task import GenerationTask
    # Sprint 3-5 models
    from app.models.database import (Base, Package, Order, Task as VideoTask,
                                     Video, PaymentTransaction, ChannelConfig,
                                     SystemConfig, VideoTemplate)

    if is_async_db:
        async with _async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        with engine.begin() as conn:
            Base.metadata.create_all(bind=conn)
    print("✅ Database tables created")


async def close_db():
    """关闭数据库连接"""
    if is_async_db:
        await _async_engine.dispose()
    else:
        engine.dispose()


async def get_session() -> Generator[Session, None, None]:
    """获取数据库会话 - 依赖注入使用"""
    if is_async_db:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

