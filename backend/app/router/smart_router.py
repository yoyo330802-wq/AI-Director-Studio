"""
漫AI - 智能路由引擎
多维度智能路由算法
"""
from typing import Dict, Literal, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class Channel:
    """上游渠道配置"""
    name: str
    cost_per_second: float  # 实际成本
    quality_score: int      # 质量评分 1-10
    avg_generation_time: int  # 平均生成时间（秒）
    max_queue_size: int    # 最大队列长度
    features: list          # 支持的功能
    max_resolution: str
    max_duration: int
    success_rate: float = 0.99  # 历史成功率
    current_load: float = 0.0    # 当前负载 0-1


class SmartRouter:
    """
    多维度智能路由引擎
    决策因素：成本、质量、负载、用户等级、历史偏好
    """
    
    # 可用渠道配置
    CHANNELS: Dict[str, Channel] = {
        "wan21_1.3b": Channel(
            name="Wan2.1-1.3B(自建)",
            cost_per_second=0.012,
            quality_score=6,
            avg_generation_time=15,
            max_queue_size=100,
            features=["text2video"],
            max_resolution="720p",
            max_duration=5,
        ),
        "wan21_14b": Channel(
            name="Wan2.1-14B(自建)",
            cost_per_second=0.025,
            quality_score=7,
            avg_generation_time=30,
            max_queue_size=50,
            features=["text2video", "image2video"],
            max_resolution="1080p",
            max_duration=10,
        ),
        "vidu": Channel(
            name="Vidu(硅基流动)",
            cost_per_second=0.050,
            quality_score=8,
            avg_generation_time=45,
            max_queue_size=30,
            features=["text2video", "image2video", "anime_style"],
            max_resolution="1080p",
            max_duration=10,
            success_rate=0.98,
        ),
        "kling": Channel(
            name="可灵(硅基流动)",
            cost_per_second=0.070,
            quality_score=9,
            avg_generation_time=60,
            max_queue_size=20,
            features=["text2video", "image2video", "motion_brush", "camera_control"],
            max_resolution="1080p",
            max_duration=10,
            success_rate=0.98,
        ),
    }
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def route(self, request) -> Dict:
        """
        核心路由决策算法
        
        优先级：
        1. 强制指定（企业用户）
        2. 质量优先模式 → 可灵
        3. 成本优先模式 → Wan2.1-1.3B
        4. 智能平衡模式（默认）
        """
        
        # 第1层：强制规则
        if request.force_channel:
            if request.user_level == "enterprise":
                return self._route_to_channel(request.force_channel)
            else:
                raise PermissionError("仅企业用户可指定渠道")
        
        # 第2层：质量优先
        if request.quality_priority:
            if self._check_channel_available("kling"):
                return self._route_to_channel("kling")
            if self._check_channel_available("vidu"):
                return self._route_to_channel("vidu")
            return self._route_to_channel("wan21_14b")
        
        # 第3层：成本优先
        if request.cost_priority:
            # 优先尝试1.3B小模型
            if request.duration <= 5 and not request.image_url:
                if self._check_channel_available("wan21_1.3b"):
                    return self._route_to_channel("wan21_1.3b")
            
            # 其次尝试14B
            if self._check_channel_available("wan21_14b"):
                return self._route_to_channel("wan21_14b")
        
        # 第4层：特殊功能需求
        if request.style in ["anime", "guofeng", "chinese_ink", "xianxia"]:
            if self._check_channel_available("vidu"):
                return self._route_to_channel("vidu")
        
        if request.camera_control or request.motion_brush:
            # 仅可灵支持高级功能
            if self._check_channel_available("kling"):
                return self._route_to_channel("kling")
        
        # 第5层：智能平衡模式
        return self._smart_balance_route(request)
    
    def _smart_balance_route(self, request) -> Dict:
        """
        智能平衡算法：综合成本、质量、负载
        
        评分公式：
        Score = w1*cost + w2*quality + w3*load + w4*speed
        
        用户等级权重：
        - free: 成本权重高 (0.6/0.2/0.1/0.1)
        - basic: 平衡 (0.4/0.3/0.2/0.1)
        - pro: 质量权重高 (0.2/0.5/0.2/0.1)
        - enterprise: 速度权重高 (0.1/0.3/0.2/0.4)
        """
        
        # 权重配置
        WEIGHTS = {
            "free": {"cost": 0.6, "quality": 0.2, "load": 0.1, "speed": 0.1},
            "basic": {"cost": 0.4, "quality": 0.3, "load": 0.2, "speed": 0.1},
            "pro": {"cost": 0.2, "quality": 0.5, "load": 0.2, "speed": 0.1},
            "enterprise": {"cost": 0.1, "quality": 0.3, "load": 0.2, "speed": 0.4},
        }
        w = WEIGHTS.get(request.user_level, WEIGHTS["basic"])
        
        # 候选渠道评分
        scores = {}
        for channel_id, channel in self.CHANNELS.items():
            # 检查是否满足基本需求
            if request.duration > channel.max_duration:
                continue
            if request.image_url and "image2video" not in channel.features:
                continue
            
            # 获取实时负载
            load = self._get_channel_load(channel_id)
            if load >= 0.95:  # 超载跳过
                continue
            
            # 归一化成本（0-10，越低越好）
            cost_normalized = (channel.cost_per_second / 0.1) * 10
            
            # 归一化速度（0-10，越快越好）
            speed_normalized = 10 * (1 - channel.avg_generation_time / 120)
            
            # 计算总分
            score = (
                w["cost"] * (10 - cost_normalized) +
                w["quality"] * channel.quality_score +
                w["load"] * (1 - load) * 10 +
                w["speed"] * speed_normalized
            )
            
            scores[channel_id] = score
        
        # 选择最高分
        if not scores:
            raise Exception("所有渠道不可用，请稍后重试")
        
        best_channel = max(scores, key=scores.get)
        
        # 记录路由决策
        self._log_routing_decision(request, best_channel, scores)
        
        return self._route_to_channel(best_channel)
    
    def _get_channel_load(self, channel_id: str) -> float:
        """获取渠道实时负载"""
        queue_key = f"channel:queue:{channel_id}"
        queue_length = self.redis.zcard(queue_key)
        max_size = self.CHANNELS[channel_id].max_queue_size
        return min(queue_length / max_size, 1.0) if max_size > 0 else 0.0
    
    def _check_channel_available(self, channel_id: str) -> bool:
        """检查渠道是否可用"""
        if channel_id not in self.CHANNELS:
            return False
        
        # 检查健康状态
        health_key = f"health:{channel_id}"
        health = self.redis.get(health_key)
        if health == "down":
            return False
        
        # 检查负载
        load = self._get_channel_load(channel_id)
        return load < 0.9
    
    def _route_to_channel(self, channel_id: str) -> Dict:
        """执行路由到指定渠道"""
        channel = self.CHANNELS[channel_id]
        load = self._get_channel_load(channel_id)
        
        # 预估等待时间
        estimated_wait = int(load * channel.avg_generation_time)
        
        return {
            "channel": channel_id,
            "channel_name": channel.name,
            "estimated_cost": channel.cost_per_second,
            "estimated_time": channel.avg_generation_time + estimated_wait,
            "quality_score": channel.quality_score,
            "queue_position": int(load * channel.max_queue_size),
        }
    
    def _log_routing_decision(self, request, channel: str, scores: Dict):
        """记录路由决策用于后续优化"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request, 'request_id', 'unknown'),
            "selected_channel": channel,
            "all_scores": scores,
            "user_level": getattr(request, 'user_level', 'unknown'),
        }
        self.redis.lpush("routing_logs", json.dumps(log_data))
        self.redis.ltrim("routing_logs", 0, 9999)  # 保留最近1万条
    
    def get_channel_health(self, channel_id: str) -> Dict:
        """获取渠道健康状态"""
        if channel_id not in self.CHANNELS:
            return {"status": "unknown", "error": "Channel not found"}
        
        channel = self.CHANNELS[channel_id]
        load = self._get_channel_load(channel_id)
        
        return {
            "channel": channel_id,
            "name": channel.name,
            "status": "healthy" if load < 0.9 else "busy",
            "current_load": round(load, 2),
            "queue_size": int(load * channel.max_queue_size),
            "max_queue_size": channel.max_queue_size,
            "avg_generation_time": channel.avg_generation_time,
        }
    
    def list_channels(self) -> list:
        """列出所有渠道状态"""
        return [self.get_channel_health(cid) for cid in self.CHANNELS.keys()]
