"""
漫AI - Vidu API客户端
生数科技视频生成API
"""
import httpx
import asyncio
import time
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

VIDU_API_BASE = "https://api.vidu.cn/v1"


class ViduClient:
    """
    Vidu视频生成客户端
    生数科技联合清华大学发布
    动漫风格效果突出
    """
    
    PRICE_PER_SECOND = 0.050  # 元/秒
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("VIDU_API_KEY", "")
        self.base_url = os.getenv("VIDU_API_BASE", VIDU_API_BASE)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    async def text_to_video(
        self,
        prompt: str,
        style: str = "anime",
        duration: int = 5,
        resolution: str = "720p",
        **kwargs
    ) -> Dict:
        """
        文生视频（动漫风格优化）
        
        Args:
            prompt: 提示词
            style: 风格 (anime/standard)
            duration: 时长（秒）
            resolution: 分辨率
        
        Returns:
            {
                "task_id": "xxx",
                "video_url": "https://...",
                "duration": 5,
                "cost": 0.25,
                "channel": "vidu",
                "generation_time": 45.0
            }
        """
        
        # 选择模型
        model = "vidu-anime" if style == "anime" else "vidu-standard"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
        }
        
        async with httpx.AsyncClient() as client:
            # 提交任务
            try:
                resp = await client.post(
                    f"{self.base_url}/generate/text2video",
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                resp.raise_for_status()
                result = resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Vidu API错误: {e.response.text}")
                raise Exception(f"Vidu API错误: {e.response.status_code}")
            
            task_id = result.get("task_id")
            if not task_id:
                raise ValueError(f"提交失败: {result}")
            
            # 轮询结果
            start_time = time.time()
            max_wait = 120  # 最多等2分钟
            
            while time.time() - start_time < max_wait:
                await asyncio.sleep(5)
                
                try:
                    status_resp = await client.get(
                        f"{self.base_url}/tasks/{task_id}",
                        headers=self.headers,
                        timeout=10.0
                    )
                    status = status_resp.json()
                except Exception as e:
                    logger.warning(f"查询状态失败: {e}")
                    continue
                
                status_str = status.get("status", "").lower()
                
                if status_str == "completed":
                    return {
                        "task_id": task_id,
                        "video_url": status.get("video_url"),
                        "cover_url": status.get("cover_url"),
                        "duration": duration,
                        "cost": duration * self.PRICE_PER_SECOND,
                        "channel": "vidu",
                        "generation_time": time.time() - start_time,
                    }
                elif status_str == "failed":
                    raise Exception(f"生成失败: {status.get('error', '未知错误')}")
                
                logger.info(f"Vidu任务进行中: {task_id}, status={status_str}")
            
            raise TimeoutError("Vidu生成超时，请稍后重试")
    
    async def image_to_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        **kwargs
    ) -> Dict:
        """
        图生视频
        
        Args:
            image_url: 参考图片URL
            prompt: 运动描述
            duration: 时长
        """
        
        payload = {
            "model": "vidu-i2v",
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/generate/image2video",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            resp.raise_for_status()
            result = resp.json()
            
            task_id = result.get("task_id")
            
            # 轮询（同上）
            # ...
            
            return {
                "task_id": task_id,
                "video_url": result.get("video_url"),
                "duration": duration,
                "cost": duration * self.PRICE_PER_SECOND,
                "channel": "vidu",
            }
    
    async def refer_to_video(
        self,
        reference_url: str,
        prompt: str,
        duration: int = 5,
        **kwargs
    ) -> Dict:
        """
        参考生视频（多主体参考）
        Vidu全球首个"多主体参考"功能
        
        Args:
            reference_url: 参考图URL
            prompt: 提示词
            duration: 时长
        """
        
        payload = {
            "model": "vidu-refer",
            "reference_url": reference_url,
            "prompt": prompt,
            "duration": duration,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/generate/refer2video",
                headers=self.headers,
                json=payload,
                timeout=60.0
            )
            resp.raise_for_status()
            result = resp.json()
            
            return {
                "task_id": result.get("task_id"),
                "video_url": result.get("video_url"),
                "duration": duration,
                "cost": duration * self.PRICE_PER_SECOND,
                "channel": "vidu",
            }
    
    async def enhance(
        self,
        video_url: str,
        **kwargs
    ) -> Dict:
        """
        智能超清
        将视频提升到1080P、24帧
        仅支持Vidu生成的视频
        
        Args:
            video_url: 原始视频URL
        """
        
        payload = {
            "model": "vidu-enhance",
            "video_url": video_url,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/generate/enhance",
                headers=self.headers,
                json=payload,
                timeout=120.0  # 超清可能需要更长时间
            )
            resp.raise_for_status()
            result = resp.json()
            
            return {
                "task_id": result.get("task_id"),
                "video_url": result.get("video_url"),
                "channel": "vidu",
                "enhance": True,
            }
    
    async def health_check(self) -> Dict:
        """健康检查"""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers,
                    timeout=5.0
                )
                return {"status": "healthy" if resp.status_code == 200 else "unhealthy"}
            except Exception as e:
                return {"status": "down", "error": str(e)}
