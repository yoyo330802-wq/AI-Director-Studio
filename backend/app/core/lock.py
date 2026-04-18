"""
漫AI - 分布式锁工具
用于支付回调等关键操作的并发控制
"""
import redis
import time
import uuid
from contextlib import contextmanager
from app.config import settings


class DistributedLock:
    """基于Redis的分布式锁"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    def acquire(self, lock_key: str, timeout: int = 10) -> str:
        """
        获取分布式锁
        
        Args:
            lock_key: 锁的key
            timeout: 锁的超时时间（秒）
            
        Returns:
            token: 锁的token，用于释放锁。如果获取失败返回None
        """
        token = str(uuid.uuid4())
        # NX: 只有当key不存在时才设置
        # EX: 设置过期时间
        acquired = self.redis_client.set(lock_key, token, nx=True, ex=timeout)
        return token if acquired else None
    
    def release(self, lock_key: str, token: str) -> bool:
        """
        释放分布式锁
        
        Args:
            lock_key: 锁的key
            token: 获取锁时返回的token
            
        Returns:
            bool: 是否释放成功
        """
        # 使用Lua脚本保证原子性
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = self.redis_client.eval(lua_script, 1, lock_key, token)
        return result == 1


@contextmanager
def lock_with_timeout(lock_key: str, timeout: int = 10, blocking: bool = True, blocking_timeout: int = 5):
    """
    上下文管理器形式的分布式锁

    Args:
        lock_key: 锁的key
        timeout: 锁的超时时间（秒）
        blocking: 是否阻塞等待
        blocking_timeout: 阻塞等待的最大时间（秒）

    Usage:
        with lock_with_timeout("order:123", timeout=10):
            # 执行业务逻辑
            pass
    """
    lock = DistributedLock()
    token = None
    start_time = time.time()

    try:
        # 尝试获取锁
        while True:
            token = lock.acquire(lock_key, timeout)
            if token:
                break

            if not blocking:
                raise Exception(f"无法获取锁: {lock_key}")

            if time.time() - start_time > blocking_timeout:
                raise Exception(f"获取锁超时: {lock_key}")

            # 使用asyncio兼容的sleep（实际是同步上下文，使用事件循环）
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.run_in_executor(None, time.sleep, 0.1)
                else:
                    loop.run_until_complete(asyncio.sleep(0.1))
            except RuntimeError:
                time.sleep(0.1)

        yield lock

    finally:
        if token:
            lock.release(lock_key, token)


# 便捷函数
def get_order_lock_key(order_no: str) -> str:
    """获取订单锁的key"""
    return f"lock:order:{order_no}"


def get_task_lock_key(task_id: str) -> str:
    """获取任务锁的key"""
    return f"lock:task:{task_id}"
