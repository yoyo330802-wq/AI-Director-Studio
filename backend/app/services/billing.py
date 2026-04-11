"""
漫AI - 计费服务
"""
import json
import logging
from datetime import datetime
from typing import Optional
import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Redis连接
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class BillingService:
    """计费服务"""
    
    @staticmethod
    def deduct_balance(
        user_id: int,
        amount: float,
        task_id: str,
        is_precharge: bool = False,
        description: str = None
    ) -> bool:
        """
        扣除用户余额
        
        Args:
            user_id: 用户ID
            amount: 扣除金额
            task_id: 任务ID
            is_precharge: 是否预扣（生成完成后确认）
            description: 描述
        
        Returns:
            bool: 是否成功
        """
        try:
            # 获取用户
            user_data = redis_client.get(f"user:id:{user_id}")
            if not user_data:
                logger.error(f"用户不存在: {user_id}")
                return False
            
            user = json.loads(user_data)
            current_balance = user.get("balance", 0.0)
            
            # 检查余额
            if current_balance < amount:
                logger.warning(f"余额不足: user={user_id}, balance={current_balance}, need={amount}")
                return False
            
            # 扣除余额
            new_balance = current_balance - amount
            user["balance"] = new_balance
            user["total_spent"] = user.get("total_spent", 0.0) + amount
            user["total_generated"] = user.get("total_generated", 0) + 1
            
            # 保存
            redis_client.set(f"user:id:{user_id}", json.dumps(user))
            
            # 更新用户名索引
            username = user.get("username")
            if username:
                redis_client.set(f"user:{username}", json.dumps(user))
            
            # 记录交易
            tx_type = "deduct_precharge" if is_precharge else "deduct"
            BillingService._record_transaction(
                user_id=user_id,
                type_=tx_type,
                amount=-amount,  # 负数表示支出
                balance_after=new_balance,
                description=description or f"视频生成任务 {task_id}"
            )
            
            logger.info(f"扣除余额成功: user={user_id}, amount={amount}, new_balance={new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"扣除余额失败: {e}")
            return False
    
    @staticmethod
    def confirm_deduction(task_id: str, actual_cost: float) -> bool:
        """
        确认扣除（实际成本与预扣不一致时调整）
        
        Args:
            task_id: 任务ID
            actual_cost: 实际成本
        
        Returns:
            bool: 是否成功
        """
        try:
            task_data = redis_client.get(f"task:{task_id}")
            if not task_data:
                return False
            
            task = json.loads(task_data)
            user_id = task.get("user_id")
            precharged = task.get("estimated_cost", 0)
            
            diff = actual_cost - precharged
            
            if abs(diff) < 0.01:
                # 成本一致，无需调整
                return True
            
            if diff > 0:
                # 实际成本更高，需要额外扣除
                BillingService.deduct_balance(
                    user_id=user_id,
                    amount=diff,
                    task_id=task_id,
                    description=f"视频生成成本调整 {task_id}"
                )
            else:
                # 实际成本更低，需要退款
                BillingService.refund(
                    user_id=user_id,
                    amount=abs(diff),
                    task_id=task_id,
                    description=f"视频生成退款 {task_id}"
                )
            
            # 更新任务成本记录
            task["actual_cost"] = actual_cost
            redis_client.set(f"task:{task_id}", json.dumps(task))
            
            return True
            
        except Exception as e:
            logger.error(f"确认扣除失败: {e}")
            return False
    
    @staticmethod
    def refund(
        user_id: int,
        amount: float,
        task_id: str,
        description: str = None
    ) -> bool:
        """
        退款
        
        Args:
            user_id: 用户ID
            amount: 退款金额
            task_id: 任务ID
            description: 描述
        
        Returns:
            bool: 是否成功
        """
        try:
            # 获取用户
            user_data = redis_client.get(f"user:id:{user_id}")
            if not user_data:
                return False
            
            user = json.loads(user_data)
            current_balance = user.get("balance", 0.0)
            
            # 退还余额
            new_balance = current_balance + amount
            user["balance"] = new_balance
            
            # 保存
            redis_client.set(f"user:id:{user_id}", json.dumps(user))
            
            # 更新用户名索引
            username = user.get("username")
            if username:
                redis_client.set(f"user:{username}", json.dumps(user))
            
            # 记录交易
            BillingService._record_transaction(
                user_id=user_id,
                type_="refund",
                amount=amount,  # 正数表示收入
                balance_after=new_balance,
                description=description or f"退款任务 {task_id}"
            )
            
            logger.info(f"退款成功: user={user_id}, amount={amount}, new_balance={new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"退款失败: {e}")
            return False
    
    @staticmethod
    def recharge(
        user_id: int,
        amount: float,
        order_id: str,
        payment_method: str = "unknown"
    ) -> bool:
        """
        充值
        
        Args:
            user_id: 用户ID
            amount: 充值金额
            order_id: 订单ID
            payment_method: 支付方式
        
        Returns:
            bool: 是否成功
        """
        try:
            # 获取用户
            user_data = redis_client.get(f"user:id:{user_id}")
            if not user_data:
                logger.error(f"用户不存在: {user_id}")
                return False
            
            user = json.loads(user_data)
            current_balance = user.get("balance", 0.0)
            
            # 增加余额
            new_balance = current_balance + amount
            user["balance"] = new_balance
            
            # 保存
            redis_client.set(f"user:id:{user_id}", json.dumps(user))
            
            # 更新用户名索引
            username = user.get("username")
            if username:
                redis_client.set(f"user:{username}", json.dumps(user))
            
            # 记录交易
            BillingService._record_transaction(
                user_id=user_id,
                type_="recharge",
                amount=amount,
                balance_after=new_balance,
                description=f"充值 {amount} 元 ({payment_method})"
            )
            
            # 标记订单已完成
            redis_client.set(f"order:{order_id}:status", "completed")
            
            logger.info(f"充值成功: user={user_id}, amount={amount}, new_balance={new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"充值失败: {e}")
            return False
    
    @staticmethod
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
    
    @staticmethod
    def calculate_cost(channel: str, duration: int) -> float:
        """
        计算生成成本
        
        Args:
            channel: 渠道ID
            duration: 时长（秒）
        
        Returns:
            float: 成本
        """
        cost_per_second = settings.COSTS.get(channel, 0.05)
        return cost_per_second * duration
    
    @staticmethod
    def get_user_balance(user_id: int) -> float:
        """获取用户余额"""
        user_data = redis_client.get(f"user:id:{user_id}")
        if user_data:
            user = json.loads(user_data)
            return user.get("balance", 0.0)
        return 0.0
