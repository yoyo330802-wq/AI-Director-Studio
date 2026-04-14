# ComfyUI / Wan2.1 客户端
# 对接 Wan2.1 Colab FastAPI 服务器 (端口 8188)

import httpx
import asyncio
from typing import Optional, Dict, Any
from app.config import settings


class ComfyUIClient:
    """
    Wan2.1 ComfyUI API 客户端

    对接格式: Wan2.1 FastAPI 服务器
    - GET  /system_stats        - 系统状态
    - POST /v1/generate/{model} - 文本生视频
    - POST /v1/generate/i2v     - 图片生视频
    """

    # 默认 Wan2.1 模型端点
    DEFAULT_BASE_URL = "http://localhost:8188"

    def __init__(self):
        self.base_url: str = settings.WAN21_COMFYUI_URL or self.DEFAULT_BASE_URL
        self.api_key: str = settings.WAN21_COMFYUI_API_KEY or ""
        self.timeout = 300.0

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "unavailable"}

    async def is_available(self) -> bool:
        """检查 Wan2.1 服务是否可用"""
        stats = await self.get_system_stats()
        return "error" not in stats

    async def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        """
        提交工作流到 ComfyUI 队列

        注意: Wan2.1 FastAPI 使用 /v1/generate/text2video 端点
        此方法仅用于兼容 ComfyUI 原始 API 格式
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/prompt",
                    json={"prompt": prompt},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("prompt_id")
        except Exception as e:
            print(f"[ComfyUI] queue_prompt error: {e}")
            return None

    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """获取执行历史"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}/history/{prompt_id}")
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {}

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        model_size: str = "1.3b",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Wan2.1 文本生视频

        直接调用 Wan2.1 FastAPI 端点
        """
        resolution = kwargs.get("resolution", "720p")

        # 格式化尺寸
        size_map = {
            "480p": "848x480",
            "720p": "1280x720",
            "1080p": "1920x1080"
        }
        if aspect_ratio == "9:16":
            size_map = {
                "480p": "480x848",
                "720p": "720x1280",
                "1080p": "1080x1920"
            }
        elif aspect_ratio == "1:1":
            size_map = {
                "480p": "480x480",
                "720p": "720x720",
                "1080p": "1080x1080"
            }

        size = size_map.get(resolution, "1280x720")

        payload = {
            "prompt": prompt,
            "negative_prompt": kwargs.get("negative_prompt", "低质量, 模糊, 变形, 文字, 水印"),
            "size": size,
            "frame_num": duration * 16,  # 16fps
            "seed": kwargs.get("seed", -1),
            "guidance_scale": kwargs.get("guidance_scale", 7.5),
            "num_inference_steps": kwargs.get("steps", 50),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/generate/{model_size}",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                result = resp.json()

                return {
                    "task_id": result.get("task_id", result.get("id")),
                    "video_url": result.get("video_url") or result.get("output", {}).get("video"),
                    "duration": duration,
                    "channel": f"wan21_{model_size}",
                }
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}

    def build_wan21_prompt(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """
        构建 Wan2.1 ComfyUI 工作流 JSON

        用于 ComfyUI 原始 API (/api/prompt) 提交
        节点 ID 需要从 ComfyUI node_types 表获取，这里使用标准 Wan2.1 节点结构
        """
        # ComfyUI 节点结构 - 标准 Wan2.1 T2V 工作流
        # 节点 ID 为任意唯一值，只要不循环引用即可
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "Wan2.1_T2V_1.3B_bf16.safetensors"
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 0]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "低质量, 模糊, 变形, 文字, 水印",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "Wan21Video",
                "inputs": {
                    "model": ["1", 0],
                    "prompt": ["2", 0],
                    "negative_prompt": ["3", 0],
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                }
            },
            "5": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["4", 0],
                    "vae": ["1", 2]
                }
            }
        }


# 全局单例
comfyui_client = ComfyUIClient()
