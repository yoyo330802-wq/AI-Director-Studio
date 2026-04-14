# 智能路由服务

from enum import Enum
from typing import Tuple


class QualityMode(str, Enum):
    COST = "cost"        # 成本优先
    BALANCED = "balanced"  # 智能平衡
    QUALITY = "quality"    # 质量优先


class ExecutionPath(str, Enum):
    COMFYUI_WAN21 = "comfyui_wan21"           # Wan2.1 via ComfyUI
    SILICONFLOW_VIDU = "siliconflow_vidu"     # Vidu via 硅基流动
    SILICONFLOW_KLING = "siliconflow_kling"   # 可灵 via 硅基流动


# 路由策略
# balanced模式: 70% Wan2.1 + 30% Vidu (按生成时长比例)
# 这里简化为: 30秒以内用Wan2.1，超过用Vidu
BALANCED_DURATION_THRESHOLD = 30  # 秒


def get_execution_path(quality_mode: str, duration: int) -> Tuple[str, str]:
    """根据quality_mode和duration确定执行路径
    
    Returns:
        (execution_path, upstream_name)
    """
    if quality_mode == QualityMode.COST:
        return ExecutionPath.COMFYUI_WAN21.value, "Wan2.1-1.3B"
    
    elif quality_mode == QualityMode.QUALITY:
        return ExecutionPath.SILICONFLOW_VIDU.value, "Vidu"
    
    else:  # balanced
        if duration <= BALANCED_DURATION_THRESHOLD:
            return ExecutionPath.COMFYUI_WAN21.value, "Wan2.1-1.3B"
        else:
            return ExecutionPath.SILICONFLOW_VIDU.value, "Vidu"


def is_comfyui_path(execution_path: str) -> bool:
    """判断是否为ComfyUI执行路径"""
    return execution_path == ExecutionPath.COMFYUI_WAN21.value


def is_siliconflow_path(execution_path: str) -> bool:
    """判断是否为硅基流动执行路径"""
    return execution_path in [
        ExecutionPath.SILICONFLOW_VIDU.value,
        ExecutionPath.SILICONFLOW_KLING.value,
    ]
