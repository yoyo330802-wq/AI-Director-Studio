# Sprint Contract — Sprint 7: Hermes API 集成验收

**日期**: 2026-04-18
**Phase**: Phase 2 Sprint Contract
**基于**: SPEC.md（sprint7-hermes-api.md）+ `hermes.py` 代码审查

---

## 一、交付物清单

### S7-F1: API 完整性 ✅ 代码已有
| 端点 | 方法 | 验收标准 |
|------|------|---------|
| `/hermes/tasks` | POST | 提交任务返回 task_id，状态 NEW |
| `/hermes/tasks` | GET | 分页列出当前用户任务 |
| `/hermes/tasks/{id}` | GET | 返回完整任务详情（含 scores/result） |
| `/hermes/tasks/{id}` | DELETE | 取消进行中任务 |
| `/hermes/agents` | GET | 返回 agent 列表及配置 |
| `/hermes/stats` | GET | 返回执行统计 |
| `/hermes/evolution/suggestions` | GET | 返回优化建议 |
| `/hermes/events/{id}` | WS | 实时推送事件流 |

**验收方法**：
```bash
# 1. 注册 + 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/register -d '{"username":"test","password":"xxx"}'
curl -X POST http://localhost:8000/api/v1/auth/login -d '{"username":"test","password":"xxx"}'
# → 获得 access_token

# 2. 提交 Hermes 任务
curl -X POST http://localhost:8000/api/v1/hermes/tasks \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"command": "调研 SiliconFlow 最新模型", "sprint": 1}'

# 3. WebSocket 订阅进度
wscat -c "ws://localhost:8000/api/v1/hermes/events/{task_id}?token=$token"

# 4. 验证事件推送（应有 PHASE_STARTED → ... → TASK_COMPLETED）
```

---

### S7-F2: 路由逻辑正确 ⚠️ 需验证
**验收标准**：
- 含"开发/代码/系统/网站" → `agent_type = "engineer"`
- 含"调研/分析/竞品/资料" → `agent_type = "researcher"`
- 含"方案/文案/脚本/创作" → `agent_type = "creator"`

**验收方法**：
```python
from app.hermes.router import task_router
assert task_router.route("开发登录功能") == "engineer"
assert task_router.route("调研竞品动态") == "researcher"
assert task_router.route("写一个视频脚本") == "creator"
```

---

### S7-F3: GAN Runner 集成 ✅ 代码已有
**验收标准**：
- Engineering 任务触发 `GANRunner.run_full(auto=True)`
- Phase 0-8 进度正确映射到 `overall_progress`
- 评分结果写入 `HermesTask.scores`

**验收方法**：
```bash
# 提交开发任务，观察 WebSocket 是否收到 Phase 0-8 完整进度推送
# 最终 event 应为 TASK_COMPLETED，含 scores
```

---

### S7-F4: WebSocket 事件完整 ⚠️ 需验证
**验收标准**：推送以下所有事件类型
- `connected`（连接时初始状态）
- `heartbeat`（每30秒）
- `PHASE_STARTED`（每个 Phase 开始）
- `TASK_PROGRESS`（进度更新）
- `AGENT_MESSAGE`（Agent 输出）
- `TASK_COMPLETED`（任务完成）
- `TASK_FAILED`（任务失败）

---

### S7-F5: 分布式锁服务化 ⚠️ 需确认
**验收标准**：
- `core/lock.py` 的 `DistributedLock` 可被 `hermes.py` 和 `payment.py` 共用
- Redis 连接失败时有降级处理（打印警告，不阻塞）

---

## 二、Phase 0 PRD 质疑（代码审查发现）

### Q1: `hermes_router.py` 的 `get_sprint_from_command()` 逻辑是什么？
**状态**：代码已写，待验证实现正确性

### Q2: `GANRunner.run_full(auto=True)` 如果 Phase 3 评分 < 7.0，是否自动进入 Phase 4 修复循环？
**状态**：需要确认修复循环是否已集成

### Q3: `main.py` 是否已注册 `hermes_router`？
**状态**：需要确认 `app/main.py` 有 `app.include_router(hermes_router)`

---

## 三、当前 Sprint 状态

| Sprint | 状态 | 评分 |
|--------|------|------|
| S1 视频生成API | ✅ 完成 | 9.05 |
| S2 支付闭环 | ✅ 完成 | - |
| S3 前端体验 | ✅ 完成 | - |
| S4 运营增强 | ✅ 完成 | - |
| S5 性能商业化 | ✅ 完成 | - |
| S6 PRD缺口修复 | ✅ 完成 | - |
| **S7 Hermes API** | 🔄 **Phase 3 待评分** | - |

---

## 四、验收门槛

**Phase 3 GAN 评分 < 7.0** → 返回 Phase 4 修复（最多3次循环）

**Critical Issues（任一出现直接 FAIL）**：
- WebSocket 连接后不推送任何事件
- REST API 返回 500
- JWT 认证未生效（未登录用户可访问）
- GAN Runner 未执行任何 Phase
