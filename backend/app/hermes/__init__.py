"""
Hermes - 多Agent协作编排模块

提供:
- HermesTask 生命周期管理
- Agent Executor (Docker容器方式)
- GAN Workflow Python API
- 进化机制
"""
from app.hermes.models import HermesTask, HermesTaskStatus, HermesEvent
from app.hermes.state import HermesStateManager
from app.hermes.router import TaskRouter
from app.hermes.executor import DockerAgentExecutor, get_executor
from app.hermes.gan_runner import GANRunner

__all__ = [
    "HermesTask",
    "HermesTaskStatus",
    "HermesEvent",
    "HermesStateManager",
    "TaskRouter",
    "DockerAgentExecutor",
    "get_executor",
    "GANRunner",
]
