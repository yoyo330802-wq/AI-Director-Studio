# ComfyUI / Wan2.1 客户端
# 对接 Wan2.1 Colab ComfyUI 服务器 (端口 8188)

import httpx
import asyncio
from typing import Optional, Dict, Any, List
from app.config import settings


class ComfyUIClient:
    """
    Wan2.1 ComfyUI API 客户端

    对接格式: ComfyUI API (ngrok 暴露的 Colab 服务器)
    - GET  /system_stats        - 系统状态
    - POST /api/prompt          - 提交工作流
    - GET  /history/{prompt_id} - 获取执行结果
    """

    def __init__(self):
        self.base_url: str = settings.WAN21_COMFYUI_URL or "http://localhost:8188"
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
            print(f"[ComfyUI] system_stats error: {e}")
            return {"error": str(e), "status": "unavailable"}

    async def is_available(self) -> bool:
        """检查 Wan2.1 服务是否可用"""
        stats = await self.get_system_stats()
        return "error" not in stats

    async def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        """提交工作流到 ComfyUI 队列"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/prompt",
                    json={"prompt": prompt},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                prompt_id = data.get("prompt_id")
                print(f"[ComfyUI] Prompt queued: {prompt_id}")
                return prompt_id
        except httpx.HTTPStatusError as e:
            print(f"[ComfyUI] queue_prompt HTTP error: {e.response.status_code} {e.response.text[:200]}")
            return None
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
        except Exception as e:
            print(f"[ComfyUI] get_history error: {e}")
            return {}

    async def get_queue(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/queue")
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return {"queue_running": [], "queue_pending": []}

    def build_wan21_workflow(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        negative_prompt: str = "低质量, 模糊, 变形, 文字, 水印, 错误",
        resolution: str = "720p",
        seed: int = -1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        构建 Wan2.1 ComfyUI 工作流 JSON

        使用正确的 ComfyUI Wan2.1 节点结构
        """
        # 分辨率映射
        size_map = {
            "480p": {"16:9": "848x480", "9:16": "480x848", "1:1": "480x480"},
            "720p": {"16:9": "1280x720", "9:16": "720x1280", "1:1": "720x720"},
            "1080p": {"16:9": "1920x1080", "9:16": "1080x1920", "1:1": "1080x1080"},
        }
        size = size_map.get(resolution, size_map["720p"]).get(aspect_ratio, "1280x720")

        # Wan2.1 T2V 工作流 - 使用正确的 ComfyUI 节点类型
        return {
            "3": {
                "class_type": "CheckpointLoader",
                "inputs": {
                    "ckpt_name": "Wan2.1_T2V_1.3B_bf16.safetensors"
                }
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["3", 0]
                }
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["3", 1]
                }
            },
            "6": {
                "class_type": "WanVideo",
                "inputs": {
                    "model": ["3", 0],
                    "prompt": ["4", 0],
                    "negative_prompt": ["5", 0],
                    "video_length": duration * 16,  # 16fps
                    "size": size,
                    "seed": seed if seed > 0 else -1,
                    "guidance_scale": kwargs.get("guidance_scale", 7.5),
                    "num_inference_steps": kwargs.get("steps", 50),
                }
            },
            "7": {
                "class_type": "SaveVideo",
                "inputs": {
                    "video": ["6", 0],
                    "filename_prefix": "manai_wan21"
                }
            }
        }

    async def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Wan2.1 文本生视频 via ComfyUI

        1. 构建工作流
        2. 提交到队列
        3. 轮询直到完成
        4. 返回视频路径
        """
        # 构建工作流
        workflow = self.build_wan21_workflow(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            negative_prompt=kwargs.get("negative_prompt", "低质量, 模糊, 变形, 文字, 水印"),
            resolution=kwargs.get("resolution", "720p"),
            seed=kwargs.get("seed", -1),
            guidance_scale=kwargs.get("guidance_scale", 7.5),
            steps=kwargs.get("steps", 50),
        )

        # 提交到队列
        prompt_id = await self.queue_prompt(workflow)
        if not prompt_id:
            return {"error": "Failed to queue prompt"}

        # 轮询等待完成
        max_wait = 60  # 最多等60次 × 5秒 = 300秒
        for i in range(max_wait):
            await asyncio.sleep(5)

            history = await self.get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})

                # 查找 SaveVideo 节点的输出
                for node_id, node_output in outputs.items():
                    if isinstance(node_output, dict) and "video_path" in node_output:
                        video_path = node_output["video_path"]
                        # 转换为 URL
                        video_url = f"{self.base_url}/view?filename={video_path}"
                        return {
                            "prompt_id": prompt_id,
                            "video_url": video_url,
                            "node_id": node_id,
                            "status": "completed",
                        }

                # 如果有输出但还没保存视频，检查是否有错误
                if outputs:
                    print(f"[ComfyUI] Outputs: {outputs}")

            if i % 6 == 0:
                print(f"[ComfyUI] Waiting for completion... ({i*5}s)")

        return {"error": "Timeout waiting for video generation", "prompt_id": prompt_id}


# 全局单例
comfyui_client = ComfyUIClient()
