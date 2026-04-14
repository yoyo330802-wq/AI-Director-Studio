# 数据库连接配置

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """初始化数据库 - 创建所有表"""
    from app.models.workflow import Workflow
    from app.models.node_type import NodeType
    from app.models.user import User
    from app.models.task import GenerationTask

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Database tables created")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话 - 依赖注入使用"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
