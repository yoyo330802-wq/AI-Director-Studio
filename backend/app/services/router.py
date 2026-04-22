# 智能路由服务

import logging
from enum import Enum
from typing import Tuple, Optional

from app.clients.comfyui_client import comfyui_client
from app.clients.siliconflow_client import siliconflow_client

logger = logging.getLogger(__name__)


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


# 降级链路顺序
FALLBACK_CHAIN = [
    ExecutionPath.COMFYUI_WAN21.value,      # 第一级：ComfyUI Wan2.1
    ExecutionPath.SILICONFLOW_VIDU.value,   # 第二级：硅基流动 Vidu
    ExecutionPath.SILICONFLOW_KLING.value,   # 第三级：硅基流动 可灵
]


async def execute_with_fallback(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    negative_prompt: str = "低质量, 模糊, 变形, 文字, 水印, 错误",
    resolution: str = "720p",
    **kwargs
) -> Tuple[bool, str, Optional[dict]]:
    """多级降级执行视频生成
    
    降级顺序: comfyui_wan21 → siliconflow_vidu → siliconflow_kling
    
    Returns:
        (success, execution_path, result_dict)
        - success: 是否成功
        - execution_path: 最终执行的路径
        - result_dict: 成功时返回结果，失败时返回 None
    """
    
    last_error = None
    
    for i, execution_path in enumerate(FALLBACK_CHAIN):
        path_display = execution_path
        
        try:
            if execution_path == ExecutionPath.COMFYUI_WAN21.value:
                # 第一级：ComfyUI Wan2.1
                logger.warning(f"[Router] Trying comfyui_wan21 (primary)")
                
                # 检查服务可用性
                if not await comfyui_client.is_available():
                    logger.warning(f"[Router] comfyui_wan21 unavailable, falling back to next")
                    last_error = "ComfyUI Wan2.1 unavailable"
                    continue
                
                # 执行生成
                result = await comfyui_client.generate_video(
                    prompt=prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    negative_prompt=negative_prompt,
                    resolution=resolution,
                    **kwargs
                )
                
                if result and "error" not in result:
                    logger.warning(f"[Router] comfyui_wan21 succeeded")
                    return True, execution_path, result
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    logger.warning(f"[Router] comfyui_wan21 failed: {error_msg}, falling back to next")
                    last_error = error_msg
                    continue
                    
            elif execution_path == ExecutionPath.SILICONFLOW_VIDU.value:
                # 第二级：硅基流动 Vidu
                logger.warning(f"[Router] Trying siliconflow_vidu (fallback 1)")
                
                # 检查服务可用性
                if not await siliconflow_client.is_available():
                    logger.warning(f"[Router] siliconflow_vidu unavailable, falling back to next")
                    last_error = "SiliconFlow Vidu unavailable"
                    continue
                
                # 提交任务
                task_id = await siliconflow_client.generate_video(
                    model="Wan-AI/Wan2.2-T2V-A14B",
                    prompt=prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                )
                
                if not task_id:
                    logger.warning(f"[Router] siliconflow_vidu submit failed, falling back to next")
                    last_error = "SiliconFlow Vidu submit failed"
                    continue
                
                # 轮询等待结果
                result = await _wait_siliconflow_task(task_id)
                
                if result and result.get("status") == "completed":
                    logger.warning(f"[Router] siliconflow_vidu succeeded")
                    return True, execution_path, result
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    logger.warning(f"[Router] siliconflow_vidu failed: {error_msg}, falling back to next")
                    last_error = error_msg
                    continue
                    
            elif execution_path == ExecutionPath.SILICONFLOW_KLING.value:
                # 第三级：硅基流动 可灵
                logger.warning(f"[Router] Trying siliconflow_kling (fallback 2)")
                
                # 检查服务可用性
                if not await siliconflow_client.is_available():
                    logger.warning(f"[Router] siliconflow_kling unavailable, no more fallbacks")
                    last_error = "SiliconFlow Kling unavailable"
                    continue
                
                # 提交任务
                task_id = await siliconflow_client.generate_video(
                    model="Wan-AI/Wan2.2-T2V-A14B",
                    prompt=prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                )
                
                if not task_id:
                    logger.warning(f"[Router] siliconflow_kling submit failed, no more fallbacks")
                    last_error = "SiliconFlow Kling submit failed"
                    continue
                
                # 轮询等待结果
                result = await _wait_siliconflow_task(task_id)
                
                if result and result.get("status") == "completed":
                    logger.warning(f"[Router] siliconflow_kling succeeded")
                    return True, execution_path, result
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No response"
                    logger.warning(f"[Router] siliconflow_kling failed: {error_msg}, no more fallbacks")
                    last_error = error_msg
                    continue
                    
        except Exception as e:
            logger.warning(f"[Router] {execution_path} exception: {str(e)}, falling back to next")
            last_error = str(e)
            continue
    
    # 三级全部失败
    logger.error(f"[Router] All fallback paths failed. Last error: {last_error}")
    return False, "", None


async def _wait_siliconflow_task(task_id: str, max_wait: int = 60) -> Optional[dict]:
    """轮询等待 SiliconFlow 任务完成
    
    Args:
        task_id: 任务ID
        max_wait: 最大等待次数（每次5秒，共300秒）
    
    Returns:
        任务结果字典
    """
    import asyncio
    
    for i in range(max_wait):
        await asyncio.sleep(5)
        
        status_result = await siliconflow_client.get_task_status(task_id)
        
        if status_result.get("status") == "completed":
            return {
                "status": "completed",
                "video_url": status_result.get("video_url"),
                "progress": 100,
            }
        elif status_result.get("status") == "failed":
            return {
                "status": "failed",
                "error": status_result.get("error", "Task failed"),
            }
        
        if i % 6 == 0:
            logger.info(f"[Router] SiliconFlow task {task_id} waiting... ({i*5}s)")
    
    return {"status": "timeout", "error": "Task timeout"}
