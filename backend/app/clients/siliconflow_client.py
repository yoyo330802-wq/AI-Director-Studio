# 硅基流动 API 客户端 (Vidu/可灵)

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class SiliconFlowClient:
    """硅基流动 API 客户端 (Vidu/可灵)"""

    BASE_URL = "https://api.siliconflow.cn/v1"

    def __init__(self):
        self.api_key = settings.SILICONFLOW_API_KEY
        self.timeout = 180.0

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_video(
        self,
        model: str,  # "vidu" | "kling"
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9"
    ) -> Optional[str]:
        """提交视频生成任务

        Returns:
            task_id 如果成功提交，否则 None
        """
        if not self.api_key:
            print("[SiliconFlow] No API key configured")
            return None

        # SiliconFlow 统一 endpoint - 视频生成
        endpoint = f"{self.BASE_URL}/video/submit"

        payload = {
            "model": model,  # "vidu" or "kling"
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "with_text": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    endpoint,
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                # SiliconFlow 返回格式: {"task_id": "xxx", ...}
                task_id = result.get("task_id") or result.get("id")
                print(f"[SiliconFlow] Task submitted: {task_id}")
                return task_id
        except httpx.HTTPStatusError as e:
            print(f"[SiliconFlow] HTTP error: {e.response.status_code} {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"[SiliconFlow] Error: {e}")
            return None

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态

        Returns:
            {"status": "pending"|"processing"|"completed"|"failed", "video_url": str|null, "progress": int}
        """
        if not self.api_key:
            return {"status": "failed", "video_url": None, "progress": 0, "error": "No API key"}

        endpoint = f"{self.BASE_URL}/video/submit/{task_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(endpoint, headers=self._headers())
                resp.raise_for_status()
                result = resp.json()

                status = result.get("status", "unknown")
                video_url = result.get("video_url") or result.get("output", {}).get("video") or result.get("url")

                # SiliconFlow 进度映射
                progress = 0
                if status == "completed":
                    progress = 100
                elif status == "processing":
                    progress = 50
                elif status == "pending":
                    progress = 10

                return {
                    "status": status,
                    "video_url": video_url,
                    "progress": progress,
                }
        except httpx.HTTPStatusError as e:
            return {"status": "failed", "video_url": None, "progress": 0, "error": str(e)}
        except Exception as e:
            return {"status": "failed", "video_url": None, "progress": 0, "error": str(e)}

    async def is_available(self) -> bool:
        """检查 API 是否可用"""
        if not self.api_key:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/balance",
                    headers=self._headers(),
                )
                return resp.status_code == 200
        except Exception:
            return False


# 全局单例
siliconflow_client = SiliconFlowClient()
