# ManAI 项目 P0 问题修复报告

**修复日期**: 2026-04-18  
**修复人**: OpenClaw Agent  
**问题来源**: Claude Code 代码检验报告

---

## 修复摘要

| 优先级 | 问题 | 状态 | 修复文件 |
|--------|------|------|----------|
| P0 | 支付回调缺少幂等性保护 | ✅ 已修复 | `app/core/lock.py`, `app/api/payment.py` |
| P0 | 任务取消后未退款 | ✅ 已修复 | `app/api/generate.py` |
| P0 | 硬编码 SECRET_KEY | ✅ 已修复 | `app/config.py` |

---

## 详细修复内容

### 1. 支付回调幂等性保护 ✅

**问题描述**: 支付回调（支付宝/微信）在高并发场景下可能重复处理，导致重复充值

**解决方案**: 添加基于 Redis 的分布式锁

**新增文件**: `app/core/lock.py`
- 实现 `DistributedLock` 类
- 支持获取锁、释放锁、超时自动释放
- 提供上下文管理器 `lock_with_timeout`

**修改文件**: `app/api/payment.py`
- 支付宝回调：`alipay_notify()` 添加分布式锁保护
- 微信回调：`wechat_notify()` 添加分布式锁保护
- 锁的 key 格式：`lock:order:{order_no}`
- 锁超时时间：10秒
- 阻塞等待时间：5秒

**代码示例**:
```python
from app.core.lock import lock_with_timeout, get_order_lock_key

# 分布式锁保护
lock_key = get_order_lock_key(out_trade_no)
try:
    with lock_with_timeout(lock_key, timeout=10, blocking_timeout=5):
        # 处理支付逻辑
        pass
except Exception as e:
    db.rollback()
    return {"status": "fail", "msg": str(e)}
```

---

### 2. 任务取消未退款 ✅

**问题描述**: 用户取消视频生成任务后，已扣除的 Token 没有退还

**解决方案**: 
1. 任务创建时立即扣减 Token
2. 任务取消时退还 Token

**修改文件**: `app/api/generate.py`

**变更1 - 创建任务时扣减Token**:
```python
# 5. 扣减用户Token余额（立即扣除）
current_user.token_balance -= token_cost
await session.commit()
```

**变更2 - 取消任务时退款**:
```python
# 退还Token到用户余额
refund_tokens = task.token_cost or 0
if refund_tokens > 0:
    user.token_balance += refund_tokens
    
return {
    "message": "Task cancelled successfully",
    "task_id": task_id,
    "refund_tokens": refund_tokens,
    "current_balance": user.token_balance
}
```

**退款流程**:
1. 检查任务状态（只有 queued/pending 可取消）
2. 获取任务 token_cost
3. 将 token_cost 加回用户余额
4. 更新任务状态为 cancelled
5. 返回退款金额和当前余额

---

### 3. 硬编码 SECRET_KEY ✅

**问题描述**: `config.py` 中有默认的 SECRET_KEY，生产环境如果使用默认值存在安全风险

**解决方案**: 强制要求设置环境变量，未设置时发出警告并使用随机临时key

**修改文件**: `app/config.py`

**变更**:
```python
# 修改前
SECRET_KEY: str = os.getenv(
    "SECRET_KEY", 
    "manai-secret-key-change-in-production-2026"
)

# 修改后
SECRET_KEY: str = os.getenv("SECRET_KEY", "")

def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if not self.SECRET_KEY:
        import warnings
        warnings.warn(
            "WARNING: SECRET_KEY is not set! "
            "Please set the SECRET_KEY environment variable for production. "
            "Using a default key is insecure and should only be used for development.",
            RuntimeWarning
        )
        # 开发环境使用临时key
        self.SECRET_KEY = "dev-secret-key-" + os.urandom(16).hex()
```

**生产环境要求**:
```bash
# 必须设置环境变量
export SECRET_KEY="your-production-secret-key-at-least-32-characters"
```

---

## 测试建议

### 1. 支付回调幂等性测试

```bash
# 模拟并发支付回调
# 使用工具如 Apache Bench 或自定义脚本
# 同一订单号并发请求10次，验证只处理一次
```

**预期结果**:
- 只有第一个请求成功处理
- 其他请求返回 "Order already paid"
- 用户余额只增加一次

### 2. 任务取消退款测试

```bash
# 1. 创建任务（扣减Token）
# 2. 取消任务
# 3. 验证Token已退还
```

**预期结果**:
- 取消任务后返回 refund_tokens
- 用户余额恢复

### 3. SECRET_KEY 验证

```bash
# 未设置环境变量时启动
python -c "from app.config import settings; print(settings.SECRET_KEY)"
# 应看到警告信息

# 设置环境变量后启动
export SECRET_KEY="my-secret-key"
python -c "from app.config import settings; print(settings.SECRET_KEY)"
# 应显示设置的key
```

---

## 部署注意事项

### 必须配置的环境变量

```bash
# 安全（必须）
export SECRET_KEY="your-production-secret-key"

# Redis（用于分布式锁）
export REDIS_URL="redis://localhost:6379/0"

# 数据库
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/manai"
```

### 启动顺序

1. 确保 Redis 服务已启动
2. 确保数据库已迁移
3. 设置所有环境变量
4. 启动应用

---

## 后续优化建议

1. **添加支付回调日志表** - 记录所有回调请求，便于审计和排查
2. **实现退款审计日志** - 记录所有退款操作
3. **添加监控告警** - 支付异常、退款异常时告警
4. **完善单元测试** - 覆盖支付和退款流程

---

## 验证清单

- [ ] 支付宝回调分布式锁生效
- [ ] 微信支付回调分布式锁生效
- [ ] 任务取消Token退款正常
- [ ] 未设置SECRET_KEY时有警告
- [ ] 生产环境SECRET_KEY已配置

---

**修复完成时间**: 2026-04-18  
**下次代码审查建议**: 2026-04-25
