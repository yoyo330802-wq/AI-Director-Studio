"""
漫AI - 支付服务
支付宝/微信支付集成
"""
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, quote
import base64

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db import get_db
from app.models.database import User, Order, OrderStatus, PaymentMethod, PaymentTransaction, Package
from app.models.schemas import RechargeRequest, RechargeResponse, OrderResponse, PackageResponse
from app.core.security import get_current_user

router = APIRouter()


def generate_order_no() -> str:
    """生成订单号"""
    return f"MANAI{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def generate_transaction_no() -> str:
    """生成交易流水号"""
    return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


# ============ 支付宝 ============

class AlipayService:
    """支付宝服务"""
    
    def __init__(self):
        self.app_id = settings.ALIPAY_APP_ID
        self.private_key = settings.ALIPAY_PRIVATE_KEY
        self.alipay_public_key = settings.ALIPAY_PUBLIC_KEY
        self.gateway = "https://openapi.alipay.com/gateway.do"
        self.notify_url = settings.ALIPAY_NOTIFY_URL
        self.return_url = settings.ALIPAY_RETURN_URL
    
    def sign(self, params: dict) -> str:
        """RSA2签名"""
        # 排序并拼接参数
        sorted_params = sorted(params.items())
        unsigned_string = "&".join([
            f"{k}={v}" for k, v in sorted_params if v
        ])
        
        # RSA2签名
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.backends import default_backend
        import rsa
        
        private_key = rsa.PrivateKey.load_pkcs1(self.private_key.encode())
        signature = rsa.sign(
            unsigned_string.encode(),
            private_key,
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def create_order(
        self, 
        out_trade_no: str, 
        total_amount: float, 
        subject: str,
        body: str = ""
    ) -> dict:
        """创建支付宝订单"""
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.notify_url,
            "return_url": self.return_url,
            "biz_content": json.dumps({
                "out_trade_no": out_trade_no,
                "total_amount": f"{total_amount:.2f}",
                "subject": subject,
                "body": body,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "timeout_express": "30m"
            })
        }
        
        # 签名
        params["sign"] = self.sign(params)
        
        # 生成支付链接
        pay_url = f"{self.gateway}?{urlencode(params)}"
        
        return {
            "qr_code": pay_url,  # 实际应该返回二维码
            "pay_url": pay_url,
            "trade_no": out_trade_no
        }
    
    def verify_signature(self, params: dict, sign: str) -> bool:
        """验证支付宝回调签名"""
        # 移除sign和sign_type
        params_copy = {k: v for k, v in params.items() 
                      if k not in ["sign", "sign_type"]}
        
        # 排序并拼接
        sorted_params = sorted(params_copy.items())
        unsigned_string = "&".join([
            f"{k}={v}" for k, v in sorted_params if v
        ])
        
        # 验签
        import rsa
        from cryptography.hazmat.primitives import hashes
        
        try:
            public_key = rsa.PublicKey.load_pkcs1(
                self.alipay_public_key.encode()
            )
            rsa.verify(
                unsigned_string.encode(),
                base64.b64decode(sign),
                public_key,
                hashes.SHA256()
            )
            return True
        except:
            return False


class WechatPayService:
    """微信支付服务"""
    
    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL
        self.api_base = "https://api.mch.weixin.qq.com"
    
    def generate_nonce(self) -> str:
        """生成随机字符串"""
        return uuid.uuid4().hex
    
    def sign(self, params: dict) -> str:
        """MD5签名"""
        sorted_params = sorted(params.items())
        string_a = "&".join([
            f"{k}={v}" for k, v in sorted_params if v
        ])
        string_sign_temp = f"{string_a}&key={self.api_key}"
        return hashlib.md5(
            string_sign_temp.encode('utf-8')
        ).hexdigest().upper()
    
    def create_order(
        self,
        out_trade_no: str,
        total_fee: int,  # 单位：分
        body: str,
        trade_type: str = "NATIVE"
    ) -> dict:
        """创建微信订单"""
        url = f"{self.api_base}/pay/unifiedorder"
        
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self.generate_nonce(),
            "body": body,
            "out_trade_no": out_trade_no,
            "total_fee": total_fee,
            "spbill_create_ip": "127.0.0.1",
            "notify_url": self.notify_url,
            "trade_type": trade_type
        }
        
        params["sign"] = self.sign(params)
        
        # 转换为XML
        xml_data = "<xml>" + "".join([
            f"<{k}><![CDATA[{v}]]></{k}>" 
            for k, v in params.items()
        ]) + "</xml>"
        
        # 发送请求
        response = httpx.post(url, content=xml_data.encode('utf-8'))
        
        # 解析响应
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        result = {child.tag: child.text for child in root}
        
        if result.get("return_code") == "SUCCESS":
            return {
                "code_url": result.get("code_url"),
                "trade_no": out_trade_no
            }
        else:
            raise Exception(result.get("return_msg", "微信下单失败"))


# 初始化支付服务
alipay_service = AlipayService() if hasattr(settings, 'ALIPAY_APP_ID') else None
wechat_service = WechatPayService() if hasattr(settings, 'WECHAT_APP_ID') else None


# ============ 订单API ============

@router.post("/create", response_model=RechargeResponse)
def create_order(
    request: RechargeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建充值订单"""
    
    # 获取套餐信息
    package = None
    if request.package_id:
        package = db.query(Package).filter(
            Package.id == request.package_id,
            Package.is_active == True
        ).first()
        
        if not package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="套餐不存在"
            )
        amount = package.price
    else:
        amount = request.amount
    
    # 创建订单
    order = Order(
        order_no=generate_order_no(),
        user_id=current_user.id,
        package_id=package.id if package else None,
        amount=amount,
        actual_amount=amount,
        discount=0.0,
        status=OrderStatus.PENDING,
        expired_at=datetime.utcnow() + timedelta(minutes=30)
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 创建交易记录
    transaction = PaymentTransaction(
        order_id=order.id,
        transaction_no=generate_transaction_no(),
        payment_method=PaymentMethod.ALIPAY if request.payment_method == "alipay" 
                       else PaymentMethod.WECHAT,
        amount=amount,
        net_amount=amount,
        status="pending"
    )
    db.add(transaction)
    db.commit()
    
    # 调用支付服务
    if request.payment_method == "alipay" and alipay_service:
        result = alipay_service.create_order(
            out_trade_no=order.order_no,
            total_amount=amount,
            subject=f"漫AI-{package.name if package else '余额充值'}"
        )
    elif request.payment_method == "wechat" and wechat_service:
        result = wechat_service.create_order(
            out_trade_no=order.order_no,
            total_fee=int(amount * 100),
            body=f"漫AI-{package.name if package else '余额充值'}"
        )
    else:
        # 余额支付
        result = {
            "qr_code": None,
            "pay_url": None,
            "trade_no": order.order_no
        }
    
    return RechargeResponse(
        order_id=order.id,
        order_no=order.order_no,
        amount=amount,
        payment_method=request.payment_method,
        qr_code=result.get("qr_code"),
        pay_url=result.get("pay_url"),
        expired_at=order.expired_at
    )


@router.post("/notify/alipay")
def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """支付宝异步回调
    
    验签流程:
    1. 解析 POST body 中的表单数据
    2. 提取 sign 和 sign_type
    3. 使用支付宝公钥验签
    4. 验签通过后处理订单（幂等）
    """
    try:
        # 解析表单数据
        form_data = dict(request.form())
        if not form_data:
            # 尝试解析 JSON
            form_data = dict(request.json())
    except Exception:
        return {"status": "fail", "msg": "Invalid request body"}
    
    # 提取签名
    sign = form_data.get("sign")
    sign_type = form_data.get("sign_type", "RSA2")
    
    if not sign:
        return {"status": "fail", "msg": "Missing signature"}
    
    # 支付宝回调参数
    trade_status = form_data.get("trade_status", "")
    out_trade_no = form_data.get("out_trade_no", "")  # 商户订单号
    trade_no = form_data.get("trade_no", "")  # 支付宝交易号
    total_amount = form_data.get("total_amount", "0")
    
    # 验签
    if alipay_service and alipay_service.alipay_public_key:
        if not alipay_service.verify_signature(form_data, sign):
            print(f"[Alipay Notify] Signature verification failed for order {out_trade_no}")
            return {"status": "fail", "msg": "Signature verification failed"}
    
    # 只处理交易成功的回调
    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        print(f"[Alipay Notify] Trade status not success: {trade_status}")
        return {"status": "success"}  # 返回success避免重复通知
    
    # 幂等处理：检查订单是否已处理
    order = db.query(Order).filter(Order.order_no == out_trade_no).first()
    if not order:
        print(f"[Alipay Notify] Order not found: {out_trade_no}")
        return {"status": "fail", "msg": "Order not found"}
    
    if order.status == OrderStatus.PAID:
        # 订单已处理，直接返回成功（幂等）
        print(f"[Alipay Notify] Order already paid: {out_trade_no}")
        return {"status": "success"}
    
    # 更新订单状态
    order.status = OrderStatus.PAID
    order.payment_method = PaymentMethod.ALIPAY
    order.payment_no = trade_no
    order.paid_at = datetime.utcnow()
    
    # 获取用户并增加余额
    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        amount = float(total_amount) if total_amount else order.actual_amount
        user.balance = (user.balance or 0) + amount
        user.total_balance = (user.total_balance or 0) + amount
        print(f"[Alipay Notify] Added {amount} to user {user.id} balance. New balance: {user.balance}")
    
    # 更新交易记录状态
    transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id == order.id
    ).order_by(PaymentTransaction.created_at.desc()).first()
    if transaction:
        transaction.status = "success"
        transaction.third_party_transaction_id = trade_no
        transaction.paid_at = datetime.utcnow()
    
    db.commit()
    print(f"[Alipay Notify] Successfully processed payment for order {out_trade_no}")
    
    return {"status": "success"}


@router.post("/notify/wechat")
def wechat_notify(request: Request, db: Session = Depends(get_db)):
    """微信支付异步回调
    
    验签流程:
    1. 解析 XML body
    2. 提取 sign 字段
    3. 使用微信平台证书/商户API密钥验签
    4. 验签通过后处理订单（幂等）
    """
    try:
        # 解析 XML body
        xml_data = request.body().decode("utf-8")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        params = {child.tag: child.text for child in root}
    except Exception as e:
        print(f"[Wechat Notify] Failed to parse XML: {e}")
        return {"status": "FAIL", "msg": "Invalid XML"}
    
    # 提取关键字段
    return_code = params.get("return_code", "")
    result_code = params.get("result_code", "")
    out_trade_no = params.get("out_trade_no", "")  # 商户订单号
    transaction_id = params.get("transaction_id", "")  # 微信订单号
    total_fee = params.get("total_fee", "0")  # 订单金额(分)
    
    # 返回给微信服务器
    def wechat_reply(success: bool, msg: str = ""):
        if success:
            return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"
        else:
            return f"<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[{msg}]]></return_msg></xml>"
    
    # 只处理成功的支付回调
    if return_code != "SUCCESS" or result_code != "SUCCESS":
        print(f"[Wechat Notify] Payment not success: return_code={return_code}, result_code={result_code}")
        return wechat_reply(False, "Payment not success")
    
    # 验签
    if wechat_service and wechat_service.api_key:
        received_sign = params.get("sign", "")
        # 构造待验签字符串（排除sign字段）
        sign_params = {k: v for k, v in params.items() if k != "sign" and v}
        calculated_sign = wechat_service.sign(sign_params)
        if calculated_sign != received_sign:
            print(f"[Wechat Notify] Signature verification failed for order {out_trade_no}")
            print(f"[Wechat Notify] Received: {received_sign}, Calculated: {calculated_sign}")
            return wechat_reply(False, "Signature verification failed")
    
    # 幂等处理：检查订单是否已处理
    order = db.query(Order).filter(Order.order_no == out_trade_no).first()
    if not order:
        print(f"[Wechat Notify] Order not found: {out_trade_no}")
        return wechat_reply(False, "Order not found")
    
    if order.status == OrderStatus.PAID:
        # 订单已处理，直接返回成功（幂等）
        print(f"[Wechat Notify] Order already paid: {out_trade_no}")
        return wechat_reply(True)
    
    # 更新订单状态
    order.status = OrderStatus.PAID
    order.payment_method = PaymentMethod.WECHAT
    order.payment_no = transaction_id
    order.paid_at = datetime.utcnow()
    
    # 获取用户并增加余额
    user = db.query(User).filter(User.id == order.user_id).first()
    if user:
        # 微信支付金额单位是分，转换为元
        amount = float(total_fee) / 100.0 if total_fee else order.actual_amount
        user.balance = (user.balance or 0) + amount
        user.total_balance = (user.total_balance or 0) + amount
        print(f"[Wechat Notify] Added {amount} to user {user.id} balance. New balance: {user.balance}")
    
    # 更新交易记录状态
    transaction = db.query(PaymentTransaction).filter(
        PaymentTransaction.order_id == order.id
    ).order_by(PaymentTransaction.created_at.desc()).first()
    if transaction:
        transaction.status = "success"
        transaction.third_party_transaction_id = transaction_id
        transaction.paid_at = datetime.utcnow()
    
    db.commit()
    print(f"[Wechat Notify] Successfully processed payment for order {out_trade_no}")
    
    return wechat_reply(True)


@router.get("/status/{order_no}")
def get_order_status(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询订单状态"""
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    return {
        "order_no": order.order_no,
        "status": order.status.value,
        "amount": order.actual_amount,
        "paid_at": order.paid_at
    }


@router.get("/list")
def get_orders(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    query = db.query(Order).filter(Order.user_id == current_user.id)
    
    if status:
        try:
            order_status = OrderStatus(status)
            query = query.filter(Order.status == order_status)
        except:
            pass
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "items": [OrderResponse.model_validate(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ============ 套餐API ============

@router.get("/packages", response_model=list[PackageResponse])
def get_packages(db: Session = Depends(get_db)):
    """获取套餐列表"""
    packages = db.query(Package).filter(
        Package.is_active == True
    ).order_by(Package.sort_order).all()
    
    return [PackageResponse.model_validate(p) for p in packages]


@router.get("/packages/{package_id}", response_model=PackageResponse)
def get_package(
    package_id: int,
    db: Session = Depends(get_db)
):
    """获取套餐详情"""
    package = db.query(Package).filter(
        Package.id == package_id,
        Package.is_active == True
    ).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    return PackageResponse.model_validate(package)
