# Sprint 5 Progress

## Sprint 5: 数据库索引优化 + Redis缓存 + 完整套餐体系

**日期**: 2026-04-15
**目标**: 性能优化 + 完整商业化套餐

---

## 已完成

### S5-F1: Redis缓存

**文件**: `/home/wj/workspace/manai/backend/app/services/cache.py` (新文件)

**实现内容**:

1. **CacheService 类**
   - 异步 Redis 客户端 (redis.asyncio)
   - 自动连接/断开管理
   - 缓存降级处理 (Redis 不可用时不影响业务)

2. **缓存操作**
   - `get/set/delete` - 基础缓存操作
   - `get_json/set_json` - JSON 数据缓存
   - `exists` - 键存在检查

3. **业务缓存**
   - `cache_user/get_cached_user` - 用户信息缓存
   - `cache_task_status/get_cached_task_status` - 任务状态缓存
   - `cache_packages/get_cached_packages` - 套餐列表缓存
   - `cache_video/get_cached_video` - 视频信息缓存
   - `cache_route_decision` - 路由决策缓存

4. **限流服务**
   - `rate_limit` - 分布式限流
   - 支持滑动窗口算法

5. **会话缓存**
   - `cache_session/get_cached_session` - 会话数据
   - `acquire_lock/release_lock` - 分布式锁

**配置项** (`config.py`):
```python
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_CACHE_ENABLED: bool = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
REDIS_CACHE_TTL_DEFAULT: int = 300  # 5分钟
REDIS_CACHE_TTL_SHORT: int = 60     # 1分钟
REDIS_CACHE_TTL_LONG: int = 3600    # 1小时
```

**验收标准**:
- ✅ Redis 缓存服务已创建
- ✅ 用户/任务/套餐缓存支持
- ✅ 限流和分布式锁支持
- ✅ 缓存降级处理

---

### S5-F2: 数据库索引优化

**文件**: `/home/wj/workspace/manai/backend/app/services/index_optimization.py` (新文件)

**实现内容**:

1. **IndexOptimizer 类**
   - 支持 PostgreSQL 和 SQLite
   - PostgreSQL 使用 CONCURRENTLY 创建索引避免锁表
   - 索引存在性检查

2. **索引清单** (38个):
   
   **用户表 (users)**:
   - `idx_users_email` - 邮箱查询
   - `idx_users_phone` - 手机号查询
   - `idx_users_level` - 等级筛选
   - `idx_users_is_active` - 活跃用户筛选
   - `idx_users_is_vip` - VIP筛选
   - `idx_users_level_active` - 复合:等级+状态
   - `idx_users_vip_expires` - VIP过期查询
   - `idx_users_oauth` - 第三方登录

   **订单表 (orders)**:
   - `idx_orders_user_status` - 用户订单状态
   - `idx_orders_user_created` - 用户订单排序
   - `idx_orders_package_status` - 套餐订单查询

   **任务表 (tasks)**:
   - `idx_tasks_user_status` - 用户任务筛选
   - `idx_tasks_user_created` - 用户任务排序
   - `idx_tasks_status_created` - 状态+时间排序
   - `idx_tasks_channel_status` - 渠道任务统计

   **视频表 (videos)**:
   - `idx_videos_user_created` - 用户视频列表
   - `idx_videos_public_created` - 公开视频列表
   - `idx_videos_featured_public` - 精选视频
   - `idx_videos_category_public` - 分类视频

   **支付交易表**:
   - `idx_payment_transactions_order_status` - 订单交易查询

3. **模型级复合索引** (`models/database.py`):
   - User: `idx_users_level_active`, `idx_users_vip_expires`, `idx_users_oauth`
   - Order: `idx_orders_user_status`, `idx_orders_user_created`, `idx_orders_package_status`
   - Task: `idx_tasks_user_status`, `idx_tasks_user_created`, `idx_tasks_status_created`, `idx_tasks_channel_status`
   - Video: `idx_videos_featured_public`, `idx_videos_category_public`
   - PaymentTransaction: `idx_payment_transactions_order_status`

**验收标准**:
- ✅ 索引优化服务已创建
- ✅ 38个索引定义完成
- ✅ 模型层复合索引添加
- ✅ 支持在线创建索引

---

### S5-F3: 完整套餐体系

**文件**: 
- `/home/wj/workspace/manai/backend/app/services/package.py` (新文件)
- `/home/wj/workspace/manai/backend/app/api/packages.py` (新文件)

**实现内容**:

1. **PackageService 类**:

   **套餐数据** (4个默认套餐):
   | 套餐 | 价格 | 时长 | 主要权益 |
   |------|------|------|---------|
   | 体验包 | ¥39 | 10分钟 | 基础功能、720p |
   | 创作者月卡 | ¥399 | 100分钟 | 优先队列、无水印、1080p |
   | 工作室季卡 | ¥1799 | 500分钟 | API接入、批量生成、4K |
   | 企业年卡 | ¥9999 | 3000分钟 | SLA 99.5%、私有部署 |

   **核心功能**:
   - `get_all_packages` - 获取所有套餐 (支持缓存)
   - `get_package_by_id` - 获取单个套餐
   - `get_package_by_level` - 按等级获取套餐
   - `create_package` - 创建套餐
   - `update_package` - 更新套餐
   - `activate_package_for_user` - 开通套餐
   - `calculate_video_cost` - 计算视频Token消耗
   - `validate_user_quota` - 验证用户配额
   - `record_video_usage` - 记录视频使用
   - `init_default_packages` - 初始化默认套餐

2. **套餐API** (`/api/v1/packages`):

   | 端点 | 方法 | 说明 |
   |------|------|------|
   | `/packages` | GET | 获取所有套餐 |
   | `/packages/recommended` | GET | 获取推荐套餐 |
   | `/packages/{id}` | GET | 获取套餐详情 |
   | `/packages/level/{level}` | GET | 按等级获取套餐 |
   | `/packages/activate/{id}` | POST | 开通套餐 |
   | `/packages/quota/calculate` | GET | 计算Token消耗 |
   | `/packages/quota/check` | GET | 检查配额 |
   | `/packages/admin/init` | POST | 初始化默认套餐 |
   | `/packages/admin/cache/clear` | POST | 清除缓存 |

3. **套餐Token计算**:
   ```python
   # 基础: 1秒 = 1 Token
   # 质量模式乘数:
   # - fast: 1.0x
   # - balanced: 1.5x
   # - premium: 2.5x
   ```

**验收标准**:
- ✅ 套餐服务已创建
- ✅ 4个默认套餐配置
- ✅ 套餐API端点完成
- ✅ 配额计算和验证
- ✅ 套餐缓存支持

---

## 代码变更

### Backend
```
backend/app/config.py                    # S5-F1 Redis配置
backend/app/main.py                       # S5-F1 缓存初始化, S5-F3 套餐路由
backend/app/services/cache.py            # S5-F1 Redis缓存 (新文件)
backend/app/services/package.py           # S5-F3 套餐服务 (新文件)
backend/app/services/index_optimization.py # S5-F2 索引优化 (新文件)
backend/app/api/packages.py               # S5-F3 套餐API (新文件)
backend/app/models/database.py            # S5-F2 复合索引
```

---

## 技术说明

### 依赖
- **redis**: `redis[hiredis]` (异步支持)
- **sqlalchemy**: PostgreSQL 索引创建

### 环境变量
```bash
# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=true

# 缓存TTL
REDIS_CACHE_TTL_DEFAULT=300
REDIS_CACHE_TTL_SHORT=60
REDIS_CACHE_TTL_LONG=3600
```

### 索引创建
```bash
# 在数据库迁移时执行
python -m app.services.index_optimization
```

---

## 验收状态

| 任务 | 模块 | 状态 |
|------|------|------|
| S5-F1 | Redis缓存 | ✅ 完成 |
| S5-F2 | 数据库索引 | ✅ 完成 |
| S5-F3 | 完整套餐体系 | ✅ 完成 |

---

## 下一步

- [ ] 执行数据库索引创建脚本
- [ ] 连接真实 Redis 服务
- [ ] 套餐前端页面集成
- [ ] 配额扣费逻辑完善
- [ ] 套餐购买支付流程
