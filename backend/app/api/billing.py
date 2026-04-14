"""
漫AI - 计费API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db import get_db
from app.models.database import User, PaymentTransaction, Order, Package, PaymentMethod, OrderStatus
from app.models.schemas import (
    BalanceResponse, RechargeRequest, RechargeResponse, TransactionResponse
)
from app.core.security import get_current_user

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取余额"""
    return BalanceResponse(
        balance=current_user.balance or 0.0,
        video_quota=current_user.video_quota or 0,
        video_used=current_user.video_used or 0,
        video_remaining=(current_user.video_quota or 0) - (current_user.video_used or 0)
    )


@router.post("/recharge", response_model=RechargeResponse)
def recharge(
    request: RechargeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """充值 - 直接到账"""
    # 创建充值订单
    order_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{str(current_user.id)[-4:].upper()}"
    
    # 获取支付方式枚举
    payment_method = PaymentMethod.ALIPAY if request.payment_method == "alipay" else PaymentMethod.WECHAT
    
    # 创建订单
    order = Order(
        order_no=order_no,
        user_id=current_user.id,
        package_id=None,
        amount=request.amount,
        actual_amount=request.amount,
        discount=0.0,
        payment_method=payment_method,
        status=OrderStatus.PAID,  # 直接到账
        paid_at=datetime.utcnow()
    )
    db.add(order)
    db.flush()
    
    # 更新用户余额
    old_balance = current_user.balance or 0.0
    current_user.balance = old_balance + request.amount
    
    # 创建交易记录
    tx = PaymentTransaction(
        order_id=order.id,
        transaction_no=f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}{str(current_user.id)[-4:].upper()}",
        payment_method=payment_method,
        amount=request.amount,
        fee=0.0,
        net_amount=request.amount,
        status="success",
        paid_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()
    
    # 生成支付信息（模拟）
    qr_code = f"https://pay.example.com/qr/{order.id}"
    
    return RechargeResponse(
        order_id=str(order.id),
        order_no=order_no,
        amount=request.amount,
        payment_method=request.payment_method,
        qr_code=qr_code,
        expired_at=datetime.utcnow() + timedelta(hours=24)
    )


@router.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取交易记录"""
    # 查询用户的支付交易
    transactions = db.query(PaymentTransaction).join(Order).filter(
        Order.user_id == current_user.id,
        PaymentTransaction.status == "success"
    ).order_by(PaymentTransaction.created_at.desc()).limit(limit).all()
    
    return [
        TransactionResponse(
            id=tx.id,
            transaction_no=tx.transaction_no,
            payment_method=tx.payment_method.value if hasattr(tx.payment_method, 'value') else str(tx.payment_method),
            amount=tx.amount,
            fee=tx.fee or 0.0,
            net_amount=tx.net_amount,
            status=tx.status,
            created_at=tx.created_at,
            paid_at=tx.paid_at
        )
        for tx in transactions
    ]


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
