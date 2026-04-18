"""
漫AI - Wan2.1自建集群客户端
支持14B和1.3B双模型
"""
import httpx
import asyncio
import logging
from typing import Optional, Literal, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class Wan21Client:
    """
    Wan2.1自建集群客户端
    支持14B/1.3B双模型自动切换
    """
    
    # 成本配置（元/秒）
    COSTS = {
        "14b": 0.025,
        "1.3b": 0.012
    }
    
    def __init__(
        self,
        model_size: Literal["14b", "1.3b"] = "14b",
        base_url: str = None,
        api_key: str = None,
        timeout: int = 300
    ):
        self.model_size = model_size
        self.base_url = base_url or "http://wan21.internal.manai.com"
        self.api_key = api_key
        self.timeout = timeout
        self.cost_per_second = self.COSTS.get(model_size, 0.025)
    
    def _get_endpoint(self) -> str:
        """获取API端点"""
        return f"{self.base_url}/v1/generate/{self.model_size}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def text_to_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: Literal[5, 10] = 5,
        resolution: Literal["480p", "720p", "1080p"] = "720p",
        aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9",
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        文生视频
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            duration: 视频时长（秒）
            resolution: 分辨率
            aspect_ratio: 宽高比
            seed: 随机种子（可选）
        
        Returns:
            {
                "task_id": "xxx",
                "video_url": "https://...",
                "duration": 5,
                "cost": 0.125,
                "channel": "wan21_14b",
                "generation_time": 28.5
            }
        """
        
        # 参数校验
        if self.model_size == "1.3b" and duration > 5:
            raise ValueError("1.3B模型仅支持5秒视频")
        
        if self.model_size == "1.3b" and resolution == "1080p":
            logger.warning("1.3B模型推荐720p，1080p可能质量下降")
        
        payload = {
            "prompt": self._optimize_prompt(prompt),
            "negative_prompt": negative_prompt or "低质量, 模糊, 变形, 文字, 水印",
            "size": self._format_size(resolution, aspect_ratio),
            "frame_num": duration * 16,  # 16fps
            "seed": seed or -1,
            "guidance_scale": kwargs.get("guidance_scale", 7.5),
            "num_inference_steps": kwargs.get("steps", 50),
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()

            try:
                response = await client.post(
                    self._get_endpoint(),
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()

                generation_time = time.time() - start_time
                
                return {
                    "task_id": result.get("task_id", result.get("id")),
                    "video_url": result.get("video_url", result.get("output", {}).get("video")),
                    "duration": duration,
                    "cost": duration * self.cost_per_second,
                    "channel": f"wan21_{self.model_size}",
                    "generation_time": generation_time,
                    "seed": result.get("seed"),
                }
                
            except httpx.TimeoutException:
                logger.error(f"Wan2.1生成超时: {payload}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"Wan2.1 API错误: {e.response.text}")
                raise
    
    async def image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: Literal[5, 10] = 5,
        **kwargs
    ) -> Dict:
        """
        图生视频
        
        Args:
            image_url: 图片URL或本地路径
            prompt: 运动描述（可选）
            duration: 时长
        """
        
        if self.model_size == "1.3b":
            raise ValueError("1.3B模型不支持图生视频")
        
        # 如果是本地路径，先上传
        if image_url.startswith("/") or image_url.startswith("./"):
            image_url = await self._upload_image(image_url)
        
        payload = {
            "image_url": image_url,
            "prompt": prompt or "保持风格，自然运动",
            "duration": duration,
            "mode": "image2video"
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_endpoint(),
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "task_id": result.get("task_id", result.get("id")),
                "video_url": result.get("video_url", result.get("output", {}).get("video")),
                "duration": duration,
                "cost": duration * self.cost_per_second,
                "channel": f"wan21_{self.model_size}",
            }
    
    def _optimize_prompt(self, prompt: str) -> str:
        """
        针对Wan2.1优化提示词
        自动添加动漫风格关键词
        """
        anime_keywords = ["高质量", "动漫风格", "细节丰富", "流畅运动"]
        
        # 如果用户prompt已包含"动漫"，不重复添加
        if "动漫" not in prompt and "anime" not in prompt.lower():
            prompt = f"{prompt}, {', '.join(anime_keywords)}"
        
        return prompt
    
    def _format_size(self, resolution: str, aspect_ratio: str) -> str:
        """格式化分辨率参数"""
        size_map = {
            ("480p", "16:9"): "848x480",
            ("720p", "16:9"): "1280x720",
            ("1080p", "16:9"): "1920x1080",
            ("480p", "9:16"): "480x848",
            ("720p", "9:16"): "720x1280",
            ("1080p", "9:16"): "1080x1920",
            ("480p", "1:1"): "480x480",
            ("720p", "1:1"): "720x720",
            ("1080p", "1:1"): "1080x1080",
        }
        return size_map.get((resolution, aspect_ratio), "1280x720")
    
    async def _upload_image(self, local_path: str) -> str:
        """上传本地图片到OSS（简化实现）"""
        # TODO: 实现OSS上传
        logger.warning("本地图片上传未实现，请使用远程URL")
        return local_path
    
    async def health_check(self) -> Dict:
        """健康检查"""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                return {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "model": self.model_size
                }
            except Exception as e:
                return {"status": "down", "error": str(e)}


# 客户端工厂函数
def create_wan21_client(channel: str, **kwargs):
    """根据渠道创建客户端"""
    if "1.3b" in channel:
        return Wan21Client(model_size="1.3b", **kwargs)
    else:
        return Wan21Client(model_size="14b", **kwargs)
