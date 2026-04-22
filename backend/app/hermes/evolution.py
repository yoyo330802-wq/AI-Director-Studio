"""
Hermes - 进化机制

提供:
1. 执行日志记录
2. 决策库存储和检索
3. Prompt版本管理
4. 自动优化建议
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlmodel import Field, SQLModel

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ExecutionLog(SQLModel, table=True):
    """执行日志"""
    __tablename__ = "hermes_execution_logs"

    id: int = Field(primary_key=True)
    task_id: str = Field(index=True)
    phase: int
    agent_type: str = Field(index=True)
    input_text: str
    output_text: str
    score: Optional[float] = None
    duration_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Decision(SQLModel, table=True):
    """决策库"""
    __tablename__ = "hermes_decisions"

    id: int = Field(primary_key=True)
    context_hash: str = Field(index=True)
    context_text: str
    decision: str
    outcome: str  # success/failure
    confidence: float = Field(default=0.5)
    used_count: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentPrompt(SQLModel, table=True):
    """Agent Prompt版本管理"""
    __tablename__ = "hermes_agent_prompts"

    id: int = Field(primary_key=True)
    agent_type: str = Field(index=True)
    version: int
    prompt_text: str
    avg_score: Optional[float] = None
    sample_count: int = Field(default=0)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvolutionEngine:
    """
    进化引擎

    分析历史执行，提取模式，优化未来决策
    """

    def __init__(self):
        self._db_initialized = False

    async def _ensure_tables(self):
        """确保数据库表存在"""
        if self._db_initialized:
            return

        async with AsyncSessionLocal() as session:
            # 创建表（如果不存在）
            # 注意: 生产环境应该使用alembic迁移
            from app.database import engine
            from sqlmodel.sql.metadata import BoundMetaData

            metadata = BoundMetaData(bind=engine)
            ExecutionLog.__table__.create_if_not_exists(metadata)
            Decision.__table__.create_if_not_exists(metadata)
            AgentPrompt.__table__.create_if_not_exists(metadata)

            self._db_initialized = True

    async def log_execution(
        self,
        task_id: str,
        phase: int,
        agent_type: str,
        input_text: str,
        output_text: str,
        score: Optional[float] = None,
        duration_ms: int = 0
    ):
        """记录一次执行"""
        await self._ensure_tables()

        async with AsyncSessionLocal() as session:
            log = ExecutionLog(
                task_id=task_id,
                phase=phase,
                agent_type=agent_type,
                input_text=input_text,
                output_text=output_text,
                score=score,
                duration_ms=duration_ms,
            )
            session.add(log)
            await session.commit()

            # 如果评分高，更新prompt版本
            if score and score >= 7.5:
                await self._update_prompt_candidate(agent_type, input_text, score)

    async def record_decision(
        self,
        context_text: str,
        decision: str,
        outcome: str,  # success/failure
    ):
        """记录一个决策"""
        await self._ensure_tables()

        context_hash = hashlib.md5(context_text.encode()).hexdigest()

        async with AsyncSessionLocal() as session:
            # 检查是否已存在相同上下文
            result = await session.execute(
                select(Decision).where(Decision.context_hash == context_hash)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新现有决策
                existing.used_count += 1
                if outcome == "success":
                    # 增量更新成功率
                    total = existing.used_count
                    old_successes = existing.success_rate * (total - 1)
                    existing.success_rate = (old_successes + 1) / total
                existing.updated_at = datetime.utcnow()
                await session.commit()
            else:
                # 创建新决策
                new_decision = Decision(
                    context_hash=context_hash,
                    context_text=context_text[:500],  # 限制长度
                    decision=decision,
                    outcome=outcome,
                    confidence=0.5,
                    used_count=1,
                    success_rate=1.0 if outcome == "success" else 0.0,
                )
                session.add(new_decision)
                await session.commit()

    async def find_similar_decision(self, context_text: str) -> Optional[dict]:
        """查找相似的历史决策"""
        await self._ensure_tables()

        context_hash = hashlib.md5(context_text.encode()).hexdigest()

        async with AsyncSessionLocal() as session:
            # 查找相同hash的决策
            result = await session.execute(
                select(Decision).where(Decision.context_hash == context_hash)
            )
            decision = result.scalar_one_or_none()

            if decision:
                return {
                    "context_hash": decision.context_hash,
                    "decision": decision.decision,
                    "confidence": decision.confidence,
                    "success_rate": decision.success_rate,
                    "used_count": decision.used_count,
                }

            # 查找相似上下文的决策（成功率高的）
            result = await session.execute(
                select(Decision)
                .where(Decision.success_rate >= 0.7)
                .order_by(Decision.success_rate.desc())
                .limit(5)
            )
            similar = result.scalars().all()

            # 返回成功率最高的
            if similar:
                best = similar[0]
                return {
                    "context_hash": best.context_hash,
                    "decision": best.decision,
                    "confidence": best.confidence,
                    "success_rate": best.success_rate,
                    "used_count": best.used_count,
                    "note": "Similar context decision"
                }

            return None

    async def _update_prompt_candidate(
        self,
        agent_type: str,
        prompt_text: str,
        score: float
    ):
        """更新Prompt候选"""
        async with AsyncSessionLocal() as session:
            # 检查是否已有相同prompt
            result = await session.execute(
                select(AgentPrompt)
                .where(
                    AgentPrompt.agent_type == agent_type,
                    AgentPrompt.prompt_text == prompt_text
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 更新分数
                total = existing.sample_count + 1
                old_avg = existing.avg_score or 0
                existing.avg_score = (old_avg * existing.sample_count + score) / total
                existing.sample_count = total
            else:
                # 创建新版本
                result = await session.execute(
                    select(func.max(AgentPrompt.version))
                    .where(AgentPrompt.agent_type == agent_type)
                )
                max_version = result.scalar() or 0

                new_prompt = AgentPrompt(
                    agent_type=agent_type,
                    version=max_version + 1,
                    prompt_text=prompt_text[:2000],
                    avg_score=score,
                    sample_count=1,
                    is_active=False,
                )
                session.add(new_prompt)

            await session.commit()

    async def get_best_prompt(self, agent_type: str) -> Optional[str]:
        """获取最佳Prompt"""
        await self._ensure_tables()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentPrompt)
                .where(
                    AgentPrompt.agent_type == agent_type,
                    AgentPrompt.avg_score >= 7.5,
                    AgentPrompt.sample_count >= 3
                )
                .order_by(AgentPrompt.avg_score.desc())
                .limit(1)
            )
            best = result.scalar_one_or_none()

            if best:
                return best.prompt_text

            # 如果没有高评分候选，返回默认
            from app.hermes.executor import AGENT_CONFIGS
            if agent_type in AGENT_CONFIGS:
                return AGENT_CONFIGS[agent_type].prompt

            return None

    async def generate_optimization_suggestion(
        self,
        agent_type: str,
        recent_failures: list[dict]
    ) -> Optional[str]:
        """生成Prompt优化建议"""
        if not recent_failures:
            return None

        # 分析失败模式
        failure_patterns = []
        for failure in recent_failures[-10:]:  # 最近10次
            if "error" in failure.get("message", "").lower():
                failure_patterns.append("执行错误")
            if "timeout" in failure.get("message", "").lower():
                failure_patterns.append("超时")
            if "validation" in failure.get("message", "").lower():
                failure_patterns.append("验证失败")

        if not failure_patterns:
            return None

        # 生成建议
        from collections import Counter
        most_common = Counter(failure_patterns).most_common(1)[0]

        suggestions = {
            "执行错误": f"建议增强{agent_type}的错误处理和边界情况考虑",
            "超时": f"建议增加{agent_type}的超时时间或简化任务复杂度",
            "验证失败": f"建议在{agent_type}中添加更严格的前置条件检查",
        }

        return suggestions.get(most_common[0], "建议检查任务描述的清晰度和完整性")


# 全局单例
evolution_engine = EvolutionEngine()
