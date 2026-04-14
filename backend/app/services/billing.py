# 计费服务

from typing import Tuple

# 单价表 (元/秒)
PRICING = {
    "cost": 0.04,      # Wan2.1-1.3B, ~15秒出片
    "balanced": 0.06,   # 智能路由
    "quality": 0.09,    # Vidu/可灵
}

# 预估生成时间 (秒)
ESTIMATED_TIME = {
    "cost": 15,       # Wan2.1 快
    "balanced": 30,   # 混合
    "quality": 60,    # Vidu 慢
}


def calculate_cost(duration: int, quality_mode: str) -> float:
    """计算生成费用"""
    price_per_second = PRICING.get(quality_mode, PRICING["balanced"])
    return duration * price_per_second


def calculate_cost_tokens(duration: int, quality_mode: str) -> int:
    """计算Token消耗 (1 Token = 0.01元)"""
    cost_yuan = calculate_cost(duration, quality_mode)
    return int(cost_yuan * 100)


def get_estimated_time(quality_mode: str) -> int:
    """获取预估生成时间"""
    return ESTIMATED_TIME.get(quality_mode, 30)


def validate_balance(balance: int, duration: int, quality_mode: str) -> Tuple[bool, str]:
    """验证余额是否足够
    
    Returns:
        (is_valid, error_message)
    """
    required_tokens = calculate_cost_tokens(duration, quality_mode)
    if balance < required_tokens:
        return False, f"Insufficient token balance. Required: {required_tokens} tokens, Available: {balance} tokens"
    return True, ""


# 默认初始Token
DEFAULT_INITIAL_TOKENS = 100
TOKENS_PER_YUAN = 100  # 1元 = 100 Token
