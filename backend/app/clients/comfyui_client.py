# ComfyUI 客户端

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class ComfyUIClient:
    """ComfyUI API 客户端"""
    
    def __init__(self):
        self.base_url = settings.COMFYUI_URL
        self.timeout = 300.0  # 5分钟超时
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取ComfyUI系统状态"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.base_url}/system_stats")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e), "status": "unavailable"}
    
    async def is_available(self) -> bool:
        """检查ComfyUI是否可用"""
        stats = await self.get_system_stats()
        return "error" not in stats
    
    async def queue_prompt(self, prompt: Dict[str, Any]) -> Optional[str]:
        """提交工作流到队列
        
        Args:
            prompt: ComfyUI格式的工作流JSON
            
        Returns:
            prompt_id 如果成功，否则 None
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/prompt",
                    json={"prompt": prompt}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("prompt_id")
            except Exception as e:
                print(f"ComfyUI queue_prompt error: {e}")
                return None
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """获取执行历史"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{self.base_url}/history/{prompt_id}")
                response.raise_for_status()
                return response.json()
            except Exception:
                return {}
    
    def build_wan21_prompt(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """构建Wan2.1工作流prompt
        
        这里构建一个简单的Wan2.1视频生成工作流
        实际节点ID需要从ComfyUI的node_types表获取
        """
        # 简化版 - 实际需要根据ComfyUI的节点图结构构建
        return {
            " Wan21Video": {  # 节点class name
                "class_type": "Wan21Video",
                "inputs": {
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                }
            }
        }


# 全局单例
comfyui_client = ComfyUIClient()
