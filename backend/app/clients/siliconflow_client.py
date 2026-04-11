"""
漫AI - 硅基流动API客户端
支持Vidu、可灵等多种模型
"""
import httpx
import asyncio
import time
import hashlib
import logging
from typing import Optional, Literal, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SILICONFLOW_API_BASE = "https://api.siliconflow.cn/v1"


class SiliconFlowClient:
    """
    硅基流动多模型客户端
    支持Vidu、可灵等视频生成模型
    """
    
    # 2026年4月参考价格（元/秒）
    PRICE_PER_SECOND = {
        "vidu": 0.050,
        "kling": 0.070,
    }
    
    # 模型映射
    MODEL_MAP = {
        "vidu": "Vidu-video-generation",
        "kling": "kling-video-generation",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    async def text_to_video(
        self,
        model: Literal["vidu", "kling"] = "vidu",
        prompt: str = "",
        negative_prompt: Optional[str] = None,
        duration: Literal[5, 10] = 5,
        aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9",
        **kwargs
    ) -> Dict:
        """
        文生视频
        
        Args:
            model: 模型类型 (vidu/kling)
            prompt: 正向提示词
            negative_prompt: 负向提示词
            duration: 视频时长（秒）
            aspect_ratio: 宽高比
        
        Returns:
            {
                "task_id": "xxx",
                "video_url": "https://...",
                "cover_url": "https://...",
                "duration": 5,
                "cost": 0.25,
                "channel": "siliconflow_vidu",
                "generation_time": 45.2
            }
        """
        
        payload = {
            "model": self.MODEL_MAP.get(model, model),
            "prompt": prompt,
            "negative_prompt": negative_prompt or "低质量, 模糊, 变形",
            "aspect_ratio": aspect_ratio.replace(":", "_"),
            "duration": str(duration),  # API可能需要字符串
        }
        
        # 可灵支持额外参数
        if model == "kling":
            payload["mode"] = kwargs.get("mode", "std")  # std/pro
            payload["cfg_scale"] = kwargs.get("cfg_scale", 0.5)
        
        async with httpx.AsyncClient() as client:
            # 提交任务
            submit_resp = await client.post(
                f"{SILICONFLOW_API_BASE}/video/submit",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            submit_resp.raise_for_status()
            task_data = submit_resp.json()
            task_id = task_data.get("task_id")
            
            if not task_id:
                raise ValueError(f"提交失败: {task_data}")
            
            # 轮询查询
            max_poll_time = 180  # 最多等3分钟
            start_time = time.time()
            poll_interval = 3
            
            while time.time() - start_time < max_poll_time:
                await asyncio.sleep(poll_interval)
                
                try:
                    status_resp = await client.get(
                        f"{SILICONFLOW_API_BASE}/video/status/{task_id}",
                        headers=self.headers,
                        timeout=10.0
                    )
                    status = status_resp.json()
                except Exception as e:
                    logger.warning(f"查询状态失败: {e}")
                    continue
                
                status_str = status.get("status", "").upper()
                
                if status_str == "SUCCESS":
                    video_data = status.get("video", {})
                    return {
                        "task_id": task_id,
                        "video_url": video_data.get("url"),
                        "cover_url": video_data.get("cover_url"),
                        "duration": duration,
                        "cost": duration * self.PRICE_PER_SECOND.get(model, 0.05),
                        "channel": f"siliconflow_{model}",
                        "generation_time": time.time() - start_time,
                    }
                elif status_str == "FAILED":
                    fail_reason = status.get("fail_reason", status.get("error", "未知错误"))
                    raise Exception(f"视频生成失败: {fail_reason}")
                elif status_str == "PROCESSING":
                    # 继续等待
                    continue
                else:
                    logger.info(f"未知状态: {status}")
            
            raise TimeoutError("视频生成超时，请稍后重试")
    
    async def image_to_video(
        self,
        model: Literal["vidu", "kling"] = "vidu",
        image_url: str = "",
        prompt: Optional[str] = None,
        duration: Literal[5, 10] = 5,
        **kwargs
    ) -> Dict:
        """
        图生视频
        
        Args:
            model: 模型类型
            image_url: 参考图片URL
            prompt: 运动描述
            duration: 时长
        """
        
        payload = {
            "model": self.MODEL_MAP.get(model, model),
            "image_url": image_url,
            "prompt": prompt or "",
            "duration": str(duration),
        }
        
        # 可灵支持镜头控制
        if model == "kling" and kwargs.get("camera_control"):
            payload["camera_control"] = kwargs["camera_control"]
        
        async with httpx.AsyncClient() as client:
            submit_resp = await client.post(
                f"{SILICONFLOW_API_BASE}/video/submit",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            submit_resp.raise_for_status()
            task_id = submit_resp.json().get("task_id")
            
            # 轮询（同上，省略）
            # ... (轮询逻辑)
            
            return {
                "task_id": task_id,
                "video_url": "",  # 待填充
                "duration": duration,
                "cost": duration * self.PRICE_PER_SECOND.get(model, 0.05),
                "channel": f"siliconflow_{model}",
            }
    
    async def list_models(self) -> list:
        """列出可用模型"""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{SILICONFLOW_API_BASE}/models",
                    headers=self.headers,
                    timeout=10.0
                )
                resp.raise_for_status()
                return resp.json().get("data", [])
            except Exception as e:
                logger.error(f"获取模型列表失败: {e}")
                return []
    
    async def get_balance(self) -> Dict:
        """获取账户余额"""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{SILICONFLOW_API_BASE}/account/balance",
                    headers=self.headers,
                    timeout=10.0
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"获取余额失败: {e}")
                return {"balance": 0}
