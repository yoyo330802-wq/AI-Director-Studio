"""
漫AI - 计费API
"""
from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from datetime import datetime
import uuid
import json
import redis

from app.config import settings
from app.models.schemas import (
    BalanceResponse, RechargeRequest, RechargeResponse, Transaction
)

router = APIRouter()

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/balance", response_model=BalanceResponse)
def get_balance(token: str):
    """获取余额"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    user_data = redis_client.get(f"user:{username}")
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user = json.loads(user_data)
    
    return BalanceResponse(
        balance=user.get("balance", 0.0),
        total_spent=user.get("total_spent", 0.0),
        total_generated=user.get("total_generated", 0)
    )


@router.post("/recharge", response_model=RechargeResponse)
async def recharge(request: RechargeRequest, token: str):
    """充值"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    # 创建订单
    order_id = str(uuid.uuid4())
    order_data = {
        "order_id": order_id,
        "user_id": user_id,
        "username": username,
        "amount": request.amount,
        "payment_method": request.payment_method,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    redis_client.set(f"order:{order_id}", json.dumps(order_data))
    
    # 生成支付二维码（简化版，实际应调用支付接口）
    qr_code = f"https://pay.example.com/qr/{order_id}"
    
    return RechargeResponse(
        order_id=order_id,
        amount=request.amount,
        qr_code=qr_code
    )


@router.post("/recharge/{order_id}/callback")
async def recharge_callback(order_id: str):
    """支付回调"""
    order_data = redis_client.get(f"order:{order_id}")
    if not order_data:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    order = json.loads(order_data)
    
    if order["status"] != "pending":
        return {"message": "订单已处理"}
    
    # 更新订单状态
    order["status"] = "completed"
    order["paid_at"] = datetime.utcnow().isoformat()
    redis_client.set(f"order:{order_id}", json.dumps(order))
    
    # 增加用户余额
    user_data = redis_client.get(f"user:{order['username']}")
    if user_data:
        user = json.loads(user_data)
        user["balance"] = user.get("balance", 0.0) + order["amount"]
        redis_client.set(f"user:{order['username']}", json.dumps(user))
        redis_client.set(f"user:id:{order['user_id']}", json.dumps(user))
        
        # 记录交易
        _record_transaction(
            order["user_id"],
            "recharge",
            order["amount"],
            user["balance"],
            f"充值 {order['amount']} 元"
        )
    
    return {"message": "success"}


@router.get("/transactions", response_model=list[Transaction])
def get_transactions(token: str, limit: int = 20):
    """获取交易记录"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的token")
    
    transactions = redis_client.zrevrange(
        f"user:transactions:{user_id}",
        0,
        limit - 1
    )
    
    result = []
    for tx_data in transactions:
        tx = json.loads(tx_data)
        result.append(Transaction(
            id=tx["id"],
            type=tx["type"],
            amount=tx["amount"],
            balance_after=tx["balance_after"],
            description=tx["description"],
            created_at=datetime.fromisoformat(tx["created_at"])
        ))
    
    return result


def _record_transaction(
    user_id: int,
    type_: str,
    amount: float,
    balance_after: float,
    description: str
):
    """记录交易"""
    tx_id = redis_client.incr("tx_id_counter")
    tx_data = {
        "id": tx_id,
        "type": type_,
        "amount": amount,
        "balance_after": balance_after,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }
    redis_client.zadd(
        f"user:transactions:{user_id}",
        {json.dumps(tx_data): datetime.utcnow().timestamp()}
    )


@router.get("/packages")
def get_packages():
    """获取套餐列表"""
    return [
        {
            "id": "experience",
            "name": "体验包",
            "price": 39.0,
            "minutes": 10,
            "features": ["基础功能", "社区模板"]
        },
        {
            "id": "creator",
            "name": "创作者月卡",
            "price": 399.0,
            "minutes": 100,
            "features": ["优先队列", "高级模板", "无水印"]
        },
        {
            "id": "studio",
            "name": "工作室季卡",
            "price": 1799.0,
            "minutes": 500,
            "features": ["API接入", "批量生成", "专属客服"]
        },
        {
            "id": "enterprise",
            "name": "企业年卡",
            "price": 9999.0,
            "minutes": 3000,
            "features": ["SLA 99.5%", "私有部署", "定制开发"]
        }
    ]
