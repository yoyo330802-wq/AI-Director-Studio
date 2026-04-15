"""
漫AI - Redis缓存服务
Sprint 5: S5-F1 Redis缓存
"""
import json
import hashlib
from typing import Optional, Any, List
from datetime import timedelta
import redis.asyncio as redis
from app.config import settings


class CacheService:
    """Redis缓存服务"""
    
    # 缓存键前缀
    PREFIX = "manai:"
    
    # 默认过期时间
    DEFAULT_TTL = 300  # 5分钟
    SHORT_TTL = 60     # 1分钟
    LONG_TTL = 3600    # 1小时
    DAY_TTL = 86400    # 1天
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """建立Redis连接"""
        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis.ping()
            self._connected = True
            print("✅ Redis connected successfully")
            return True
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def _key(self, *parts) -> str:
        """生成缓存键"""
        return self.PREFIX + ":".join(str(p) for p in parts)
    
    # ========== 通用操作 ==========
    
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self._connected:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            return None
    
    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL) -> bool:
        """设置缓存值"""
        if not self._connected:
            return False
        try:
            await self._redis.setex(key, ttl, value)
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected:
            return False
        try:
            return await self._redis.exists(key) > 0
        except Exception:
            return False
    
    # ========== JSON操作 ==========
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取JSON缓存"""
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """设置JSON缓存"""
        try:
            data = json.dumps(value, ensure_ascii=False, default=str)
            return await self.set(key, data, ttl)
        except (TypeError, ValueError):
            return False
    
    # ========== 用户相关缓存 ==========
    
    async def cache_user(self, user_id: int, user_data: dict, ttl: int = SHORT_TTL) -> bool:
        """缓存用户信息"""
        key = self._key("user", user_id)
        return await self.set_json(key, user_data, ttl)
    
    async def get_cached_user(self, user_id: int) -> Optional[dict]:
        """获取缓存的用户信息"""
        key = self._key("user", user_id)
        return await self.get_json(key)
    
    async def invalidate_user(self, user_id: int) -> bool:
        """清除用户缓存"""
        key = self._key("user", user_id)
        return await self.delete(key)
    
    # ========== 任务相关缓存 ==========
    
    async def cache_task_status(self, task_id: str, status_data: dict, ttl: int = SHORT_TTL) -> bool:
        """缓存任务状态"""
        key = self._key("task", task_id)
        return await self.set_json(key, status_data, ttl)
    
    async def get_cached_task_status(self, task_id: str) -> Optional[dict]:
        """获取缓存的任务状态"""
        key = self._key("task", task_id)
        return await self.get_json(key)
    
    async def invalidate_task(self, task_id: str) -> bool:
        """清除任务缓存"""
        key = self._key("task", task_id)
        return await self.delete(key)
    
    # ========== 套餐相关缓存 ==========
    
    async def cache_packages(self, packages: List[dict], ttl: int = LONG_TTL) -> bool:
        """缓存套餐列表"""
        key = self._key("packages", "all")
        return await self.set_json(key, packages, ttl)
    
    async def get_cached_packages(self) -> Optional[List[dict]]:
        """获取缓存的套餐列表"""
        key = self._key("packages", "all")
        return await self.get_json(key)
    
    async def cache_package(self, package_id: int, package_data: dict, ttl: int = LONG_TTL) -> bool:
        """缓存单个套餐"""
        key = self._key("package", package_id)
        return await self.set_json(key, package_data, ttl)
    
    async def get_cached_package(self, package_id: int) -> Optional[dict]:
        """获取缓存的套餐"""
        key = self._key("package", package_id)
        return await self.get_json(key)
    
    async def invalidate_packages(self) -> bool:
        """清除套餐缓存"""
        if not self._connected:
            return False
        try:
            # 删除所有套餐相关缓存
            pattern = self._key("package", "*")
            keys = []
            async for key in self._redis.scan_iter(pattern):
                keys.append(key)
            if keys:
                await self._redis.delete(*keys)
            return True
        except Exception:
            return False
    
    # ========== 路由缓存 ==========
    
    async def cache_route_decision(self, mode: str, duration: int, decision: dict, ttl: int = SHORT_TTL) -> bool:
        """缓存路由决策"""
        key = self._key("route", mode, str(duration))
        return await self.set_json(key, decision, ttl)
    
    async def get_cached_route_decision(self, mode: str, duration: int) -> Optional[dict]:
        """获取缓存的路由决策"""
        key = self._key("route", mode, str(duration))
        return await self.get_json(key)
    
    # ========== 限流 ==========
    
    async def rate_limit(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """限流检查
        
        Returns:
            (is_allowed, remaining) - 是否允许请求，剩余次数
        """
        if not self._connected:
            return True, limit
        
        try:
            cache_key = self._key("ratelimit", key)
            current = await self._redis.get(cache_key)
            
            if current is None:
                await self._redis.setex(cache_key, window, 1)
                return True, limit - 1
            
            current_count = int(current)
            if current_count >= limit:
                return False, 0
            
            await self._redis.incr(cache_key)
            return True, limit - current_count - 1
        except Exception:
            return True, limit
    
    # ========== 会话缓存 ==========
    
    async def cache_session(self, session_id: str, session_data: dict, ttl: int = DAY_TTL) -> bool:
        """缓存会话数据"""
        key = self._key("session", session_id)
        return await self.set_json(key, session_data, ttl)
    
    async def get_cached_session(self, session_id: str) -> Optional[dict]:
        """获取缓存的会话"""
        key = self._key("session", session_id)
        return await self.get_json(key)
    
    async def invalidate_session(self, session_id: str) -> bool:
        """清除会话缓存"""
        key = self._key("session", session_id)
        return await self.delete(key)
    
    # ========== 视频缓存 ==========
    
    async def cache_video(self, video_id: int, video_data: dict, ttl: int = LONG_TTL) -> bool:
        """缓存视频信息"""
        key = self._key("video", video_id)
        return await self.set_json(key, video_data, ttl)
    
    async def get_cached_video(self, video_id: int) -> Optional[dict]:
        """获取缓存的视频"""
        key = self._key("video", video_id)
        return await self.get_json(key)
    
    async def invalidate_video(self, video_id: int) -> bool:
        """清除视频缓存"""
        key = self._key("video", video_id)
        return await self.delete(key)
    
    # ========== 统计计数 ==========
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数"""
        if not self._connected:
            return 0
        try:
            cache_key = self._key("counter", key)
            return await self._redis.incrby(cache_key, amount)
        except Exception:
            return 0
    
    async def get_counter(self, key: str) -> int:
        """获取计数"""
        if not self._connected:
            return 0
        try:
            cache_key = self._key("counter", key)
            value = await self._redis.get(cache_key)
            return int(value) if value else 0
        except Exception:
            return 0
    
    # ========== 锁 ==========
    
    async def acquire_lock(self, lock_name: str, ttl: int = 10) -> bool:
        """获取分布式锁"""
        if not self._connected:
            return True  # 无Redis时默认获取成功
        try:
            lock_key = self._key("lock", lock_name)
            result = await self._redis.set(lock_key, "1", nx=True, ex=ttl)
            return result is not None
        except Exception:
            return False
    
    async def release_lock(self, lock_name: str) -> bool:
        """释放分布式锁"""
        if not self._connected:
            return True
        try:
            lock_key = self._key("lock", lock_name)
            await self._redis.delete(lock_key)
            return True
        except Exception:
            return False


# 全局缓存服务实例
cache_service = CacheService()
