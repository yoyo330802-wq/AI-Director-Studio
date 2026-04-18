# Sprint 9 Contract — 飞书机器人集成 + E2E测试

**日期**: 2026-04-19
**Sprint**: S9
**状态**: 🔍 In Progress

---

## 任务清单（按优先级）

| ID | 任务 | 优先级 | 估计 | 状态 |
|----|------|--------|------|------|
| S9-F1 | 飞书机器人 Webhook 集成 | P0 | 4h | 🔄 |
| S9-F2 | 端到端 API 测试自动化 | P0 | 3h | ⏳ |
| S9-F3 | 飞书机器人接入漫AI工作流 | P1 | 3h | ⏳ |
| S9-F4 | WebSocket JWT 优化 | P1 | 1h | ⏳ |

---

## S9-F1: 飞书机器人 Webhook 集成

**负责人**: coder
**截止**: 2026-04-19

### 实现检查点
- [ ] `backend/app/api/feishu_bot.py` 创建
- [ ] `POST /api/v1/feishu/webhook` 端点实现
- [ ] 飞书签名验证 (HMAC-SHA256)
- [ ] 飞书卡片消息发送函数
- [ ] `app/config.py` 添加飞书配置
- [ ] `app/main.py` 注册路由

### 验收测试
```bash
# 本地测试验签
curl -X POST http://localhost:8000/api/v1/feishu/webhook \
  -H "Content-Type: application/json" \
  -H "X-Lark-Signature: <signature>" \
  -H "X-Lark-Request-Timestamp: <timestamp>" \
  -d @test_fixtures/feishu_message.json
```

---

## S9-F2: 端到端 API 测试自动化

**负责人**: coder
**截止**: 2026-04-19

### 实现检查点
- [ ] `backend/tests/hermes_e2e_test.py` 创建
- [ ] 测试用例1: 注册 → 登录 → 创建任务
- [ ] 测试用例2: WebSocket 连接测试
- [ ] 测试用例3: 用户隔离验证
- [ ] 测试报告输出

### 验收测试
```bash
cd backend
python -m pytest tests/hermes_e2e_test.py -v
```

---

## S9-F3: 飞书机器人接入漫AI工作流

**负责人**: coder
**截止**: 2026-04-19

### 实现检查点
- [ ] 消息文本解析（提取用户指令）
- [ ] Hermes 任务创建（调用现有 API）
- [ ] WebSocket 进度订阅
- [ ] 完成后飞书卡片消息回复

### 流程
```
飞书消息 → Webhook → 解析指令 → 创建Hermes任务 → 
WebSocket监听 → 进度更新 → 任务完成 → 飞书卡片回复
```

---

## S9-F4: WebSocket JWT 优化

**负责人**: coder
**截止**: 2026-04-19

### 实现检查点
- [ ] `hermes.py` WebSocket端点支持 `Authorization` header
- [ ] 优先从header获取token，fallback到query param
- [ ] 更新文档注释

### 代码变更
```python
# 修改前
async def hermes_websocket_events(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
):

# 修改后
async def hermes_websocket_events(
    websocket: WebSocket,
    task_id: str,
    token: Optional[str] = Query(None),
):
    # 从 header 获取
    auth_header = websocket.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    # fallback to query param
    if not token:
        token = Query(...)
```

---

## 资源依赖

- 飞书应用（已有）: app_id=cli_a92ee0821db8dcc4
- 后端服务: localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 飞书网络不可达 | 中 | 添加超时和重试 |
| WebSocket header解析兼容性问题 | 低 | 保留query param向后兼容 |

---

## Definition of Done

- [ ] 所有代码通过 code review
- [ ] E2E 测试全部通过
- [ ] CHANGELOG.md 已更新
- [ ] Git tag 已打
- [ ] 已 push 到远程
