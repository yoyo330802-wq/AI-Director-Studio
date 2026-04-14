# 硅基流动 API 客户端

import httpx
from typing import Optional, Dict, Any
from app.config import settings


class SiliconFlowClient:
    """硅基流动 API 客户端 (Vidu/可灵)"""
    
    BASE_URL = "https://api.siliconflow.cn/v1"
    
    async def generate_video(
        self,
        model: str,  # "vidu" | "kling"
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9"
    ) -> Optional[str]:
        """生成视频
        
        Returns:
            task_id 如果成功提交，否则 None
        """
        # 实际API调用 (这里用mock，因为没有真实API key)
        # TODO: 接入真实API
        return None
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态
        
        Returns:
            {"status": "pending" | "processing" | "completed" | "failed", "video_url": str|null}
        """
        # Mock返回值
        return {
            "status": "processing",
            "video_url": None,
            "progress": 50
        }
    
    async def is_available(self) -> bool:
        """检查API是否可用"""
        # TODO: 接入真实API后检查
        return True


# 全局单例
siliconflow_client = SiliconFlowClient()
