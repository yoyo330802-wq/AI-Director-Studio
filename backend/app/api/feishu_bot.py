"""
漫AI - 飞书机器人 Webhook 集成

接收飞书事件推送，发送卡片消息
"""
import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feishu", tags=["feishu"])


# ============ 飞书 API 配置 ============

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
FEISHU_APP_ID = getattr(settings, 'FEISHU_APP_ID', 'cli_a92ee0821db8dcc4')
FEISHU_APP_SECRET = getattr(settings, 'FEISHU_APP_SECRET', 'q6nCESAMiE12vi8feEubth50FLPciC1I')


# ============ 数据模型 ============

class FeishuEventHeader(BaseModel):
    """飞书事件头"""
    event_id: str
    event_type: str
    create_time: str
    token: Optional[str] = None
    app_id: Optional[str] = None
    tenant_key: Optional[str] = None


class FeishuSender(BaseModel):
    """发送者"""
    sender_id: dict
    sender_type: str
    tenant_key: str


class FeishuMessage(BaseModel):
    """飞书消息"""
    message_id: str
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    create_time: str
    chat_id: str
    chat_type: str
    message_type: str
    content: str  # JSON string


class FeishuMessageEvent(BaseModel):
    """飞书消息事件"""
    sender: FeishuSender
    message: FeishuMessage


class FeishuWebhookRequest(BaseModel):
    """飞书 Webhook 请求"""
    schema_version: str = Field(default="2.0", alias="schema")
    header: FeishuEventHeader
    event: FeishuMessageEvent

    class Config:
        from_attributes = True
        populate_by_name = True


class FeishuCardMessage(BaseModel):
    """飞书卡片消息"""
    msg_type: str = "interactive"
    card: dict


# ============ 飞书 API 客户端 ============

class FeishuClient:
    """飞书 API 客户端"""

    def __init__(self):
        self._tenant_token: Optional[str] = None
        self._token_expire_at: float = 0

    async def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        # 检查缓存
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token

        url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json={
                    "app_id": FEISHU_APP_ID,
                    "app_secret": FEISHU_APP_SECRET,
                }
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                raise HTTPException(
                    status_code=502,
                    detail=f"Feishu API error: {data.get('msg')}"
                )

            self._tenant_token = data["tenant_access_token"]
            # token 有效期 2 小时，提前 1 分钟刷新
            self._token_expire_at = time.time() + data.get("expire", 7200) - 60

            return self._tenant_token

    async def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: dict,
        msg_id: Optional[str] = None
    ) -> dict:
        """发送消息"""
        token = await self.get_tenant_access_token()

        url = f"{FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content),
        }

        # 如果是回复消息，设置 root_id
        if msg_id:
            payload["root_id"] = msg_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_card_message(
        self,
        receive_id: str,
        card: dict,
        msg_id: Optional[str] = None
    ) -> dict:
        """发送卡片消息"""
        return await self.send_message(
            receive_id=receive_id,
            msg_type="interactive",
            content=card,
            msg_id=msg_id
        )

    async def reply_text_message(
        self,
        receive_id: str,
        text: str,
        msg_id: str
    ) -> dict:
        """回复文本消息"""
        return await self.send_message(
            receive_id=receive_id,
            msg_type="text",
            content={"text": text},
            msg_id=msg_id
        )


# 全局单例
feishu_client = FeishuClient()


# ============ 工具函数 ============

def verify_feishu_signature(
    signature: str,
    timestamp: str,
    body: str,
    app_secret: str = FEISHU_APP_SECRET
) -> bool:
    """
    验证飞书签名

    签名算法: HMAC-SHA256(app_secret, timestamp + "+" + body)
    """
    import hmac
    import hashlib

    # 构建签名字符串
    string_to_sign = f"{timestamp}+{body}"

    # 计算签名
    mac = hmac.new(
        app_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    )
    calculated_signature = mac.hexdigest()

    # 使用 timing safe 比较
    return hmac.compare_digest(signature, calculated_signature)


def build_task_progress_card(
    task_id: str,
    command: str,
    status: str,
    progress: int,
    phase: Optional[int] = None
) -> dict:
    """
    构建任务进度卡片

    模板: blue/green/red/orange/grey/purple
    """
    status_emoji = {
        "new": "🆕",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫",
    }.get(status, "📌")

    phase_text = f"Phase {phase}" if phase is not None else "初始化"

    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"{status_emoji} 漫AI 任务进度"
            },
            "template": "blue" if status == "completed" else "orange" if status == "in_progress" else "grey"
        },
        "elements": [
            {
                "tag": "div",
                "content": {
                    "tag": "lark_md",
                    "content": f"**任务ID**: `{task_id}`"
                }
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**状态**: {status}"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**进度**: {progress}%"
                        }
                    }
                ]
            },
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": f"**阶段**: {phase_text}"
                        }
                    }
                ]
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "content": {
                    "tag": "lark_md",
                    "content": f"**指令**: {command[:100]}{'...' if len(command) > 100 else ''}"
                }
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "由 漫AI Hermes 自动推送"
                    }
                ]
            }
        ]
    }

    return card


def build_task_complete_card(
    task_id: str,
    command: str,
    scores: Optional[dict] = None,
    result: Optional[dict] = None
) -> dict:
    """构建任务完成卡片"""
    score_text = ""
    if scores:
        score_items = [f"{k}: {v}" for k, v in scores.items()]
        score_text = "\n".join(score_items)

    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "✅ 漫AI 任务已完成"
            },
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "content": {
                    "tag": "lark_md",
                    "content": f"**任务ID**: `{task_id}`"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "content": {
                    "tag": "lark_md",
                    "content": f"**指令**: {command[:100]}{'...' if len(command) > 100 else ''}"
                }
            }
        ]
    }

    # 添加评分信息
    if scores:
        card["elements"].append({
            "tag": "div",
            "fields": [
                {
                    "is_short": False,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**评分**:\n{score_text}"
                    }
                }
            ]
        })

    # 添加结果摘要
    if result:
        status = result.get("final_status", "unknown")
        completed_phases = result.get("completed_phases", [])
        card["elements"].append({
            "tag": "div",
            "content": {
                "tag": "lark_md",
                "content": f"**最终状态**: {status}\n**完成阶段**: {', '.join(completed_phases) if completed_phases else 'N/A'}"
            }
        })

    card["elements"].append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": "由 漫AI Hermes 自动推送"
            }
        ]
    })

    return card


# ============ API 端点 ============

@router.post("/webhook", summary="飞书 Webhook 接收")
async def feishu_webhook(
    request: Request,
    x_lark_signature: Optional[str] = Header(None, alias="X-Lark-Signature"),
    x_lark_request_timestamp: Optional[str] = Header(None, alias="X-Lark-Request-Timestamp"),
):
    """
    接收飞书事件推送

    支持的事件类型:
    - im.message.receive_v1: 接收消息事件

    验证方式:
    1. 飞书签名验证 (X-Lark-Signature)
    2. 时间戳验证 (X-Lark-Request-Timestamp, 5分钟内有效)
    """
    # 获取原始请求体
    body = await request.body()
    body_str = body.decode("utf-8")

    # 记录请求
    logger.info(f"Feishu webhook received: {body_str[:200]}")

    # 签名验证
    if x_lark_signature and x_lark_request_timestamp:
        # 检查时间戳（5分钟有效期）
        try:
            timestamp = int(x_lark_request_timestamp)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                logger.warning(f"Feishu webhook timestamp expired: {timestamp}")
                # 时间戳过期，但仍处理（兼容某些场景）
        except ValueError:
            pass

        # 验证签名
        if not verify_feishu_signature(x_lark_signature, x_lark_request_timestamp or "", body_str):
            logger.warning("Feishu webhook signature verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid signature"
            )

    # 解析请求体
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Feishu webhook body: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON"
        )

    # 构建请求模型
    try:
        webhook_request = FeishuWebhookRequest(**payload)
    except Exception as e:
        logger.error(f"Failed to validate Feishu webhook request: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request format: {e}"
        )

    # 处理事件
    event_type = webhook_request.header.event_type

    if event_type == "im.message.receive_v1":
        await _handle_message_event(webhook_request)
    else:
        logger.info(f"Unhandled event type: {event_type}")

    return {"code": 0, "msg": "success"}


async def _handle_message_event(event: FeishuWebhookRequest):
    """处理接收消息事件"""
    message = event.event.message
    sender = event.event.sender

    # 只处理文本消息
    if message.message_type != "text":
        logger.info(f"Ignored message type: {message.message_type}")
        return

    # 解析消息内容
    try:
        content = json.loads(message.content)
        text = content.get("text", "").strip()
    except json.JSONDecodeError:
        logger.error(f"Failed to parse message content: {message.content}")
        return

    if not text:
        return

    logger.info(f"Feishu message from {sender.sender_id}: {text[:100]}")

    # 异步处理消息（不阻塞飞书回调）
    asyncio.create_task(_process_user_message(
        user_id=sender.sender_id.get("open_id", ""),
        text=text,
        msg_id=message.message_id,
        chat_id=message.chat_id
    ))


async def _process_user_message(user_id: str, text: str, msg_id: str, chat_id: str):
    """
    处理用户消息

    流程:
    1. 解析用户指令
    2. 创建 Hermes 任务
    3. 订阅 WebSocket 进度
    4. 完成后发送飞书卡片消息
    """
    from app.hermes.state import hermes_state
    from app.hermes.models import HermesTaskCreate, HermesEventType

    # 简单指令解析（实际可接入 NLP）
    command = text

    try:
        # 创建 Hermes 任务
        # 注意：飞书用户需要绑定到漫AI用户，这里简化处理
        # 实际应该通过 open_id 查找或创建关联用户
        task_data = HermesTaskCreate(command=command)

        # 路由判定
        from app.hermes.router import task_router
        agent_type = task_router.route(command)
        sprint = task_router.get_sprint_from_command(command)

        # 创建任务（user_id=0 表示飞书匿名用户，实际需要绑定）
        task = await hermes_state.create_task(
            command=command,
            agent_type=agent_type,
            sprint=sprint,
            user_id=0,  # TODO: 飞书用户绑定
        )

        logger.info(f"Feishu created Hermes task: {task.id}")

        # 发送初始确认
        card = build_task_progress_card(
            task_id=task.id,
            command=command,
            status="new",
            progress=0
        )

        try:
            await feishu_client.send_card_message(
                receive_id=user_id,
                card=card,
                msg_id=msg_id
            )
        except Exception as e:
            logger.error(f"Failed to send initial card: {e}")

        # 启动任务执行（异步）
        asyncio.create_task(_monitor_and_notify(
            task_id=task.id,
            user_id=user_id,
            command=command,
            msg_id=msg_id
        ))

    except Exception as e:
        logger.error(f"Failed to process Feishu message: {e}")
        # 发送错误消息
        try:
            await feishu_client.reply_text_message(
                receive_id=user_id,
                text=f"❌ 处理失败: {str(e)}",
                msg_id=msg_id
            )
        except Exception:
            pass


async def _monitor_and_notify(task_id: str, user_id: str, command: str, msg_id: str):
    """监控任务进度并发送飞书通知"""
    from app.hermes.state import hermes_state
    from app.hermes.models import HermesTaskStatus

    last_progress = -1

    # 订阅任务事件
    pubsub = await hermes_state.subscribe_events(task_id)

    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=30.0
                )

                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    event_type = data.get("event")
                    progress = data.get("progress", 0)

                    # 只在进度变化时发送卡片
                    if progress != last_progress and progress % 20 == 0:
                        card = build_task_progress_card(
                            task_id=task_id,
                            command=command,
                            status=data.get("data", {}).get("status", "in_progress"),
                            progress=progress,
                            phase=data.get("phase")
                        )

                        try:
                            await feishu_client.send_card_message(
                                receive_id=user_id,
                                card=card
                            )
                        except Exception as e:
                            logger.error(f"Failed to send progress card: {e}")

                        last_progress = progress

                    # 任务完成或失败
                    if event_type in ("task_completed", "task_failed"):
                        task = await hermes_state.get_task(task_id)

                        if task:
                            if event_type == "task_completed":
                                card = build_task_complete_card(
                                    task_id=task_id,
                                    command=command,
                                    scores=task.get_scores(),
                                    result=task.get_result()
                                )
                            else:
                                card = build_task_progress_card(
                                    task_id=task_id,
                                    command=command,
                                    status="failed",
                                    progress=data.get("progress", 0)
                                )

                            try:
                                await feishu_client.send_card_message(
                                    receive_id=user_id,
                                    card=card
                                )
                            except Exception as e:
                                logger.error(f"Failed to send final card: {e}")

                        break

            except asyncio.TimeoutError:
                # 超时，检查任务状态
                task = await hermes_state.get_task(task_id)
                if task and task.status in (HermesTaskStatus.COMPLETED, HermesTaskStatus.FAILED):
                    break

    finally:
        await pubsub.unsubscribe(f"hermes:events:{task_id}")


# ============ 管理 API ============

@router.get("/card_preview", summary="卡片预览")
async def card_preview():
    """预览卡片格式（测试用）"""
    card = build_task_progress_card(
        task_id="preview-task-id",
        command="开发一个登录功能",
        status="in_progress",
        progress=50,
        phase=4
    )

    return card


@router.post("/send_test_card", summary="发送测试卡片")
async def send_test_card(
    open_id: str,
):
    """发送测试卡片（测试飞书连接）"""
    card = build_task_complete_card(
        task_id="test-task-123",
        command="这是一个测试任务",
        scores={"Sprint 1": 8.5},
        result={"final_status": "PASS", "completed_phases": ["Phase 0", "Phase 1", "Phase 2"]}
    )

    try:
        result = await feishu_client.send_card_message(
            receive_id=open_id,
            card=card
        )
        return {"code": 0, "msg": "success", "data": result}
    except Exception as e:
        logger.error(f"Failed to send test card: {e}")
        raise HTTPException(status_code=502, detail=str(e))
