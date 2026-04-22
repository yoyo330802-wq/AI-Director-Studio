# Sprint 8 进度报告 — Hermes API 收尾

**日期**: 2026-04-19
**Sprint**: S8
**状态**: ✅ 完成

---

## S8-F1: WebSocket 任务归属验证 ✅

**问题**：`/events/{task_id}` WebSocket 未验证任务归属，任意用户可订阅他人任务

**修复**：
```python
# backend/app/api/hermes.py 第361-363行
task = await hermes_state.get_task(task_id, user_id=user_id)
if not task:
    await websocket.close(code=4003, reason="Task not found")
```

---

## S8-F2: Docker Agent 镜像构建 ⚠️

**状态**: Dockerfile 存在于 `hermes-company/Dockerfile`，构建超时（网络/资源问题）

**后续建议**: 在有网络的机器上执行：
```bash
docker build -t manai/hermes-agent:latest hermes-company/
```

---

## S8-F3: 辅助修复 ✅

1. **HermesTask Base 注册**：确保 `HermesTask` 表加入 `Base.metadata`
2. **cache.py logger**：添加缺失的 logger 实例

---

## Git 发布

- Sprint 7 完整发布: `dc288d8f`
- Sprint 7 Phase 4 修复: `fc8da0bb` (user_id 隔离 + task_id 映射)
- Sprint 8 修复已并入以上提交

---

## Sprint 9 建议

1. **高优**: WebSocket 端点的 JWT token 验证完善（目前 token 在 query param，建议改为 header）
2. **中优**: Docker Agent 镜像正式构建并测试
3. **中优**: 端到端 API 测试（WebSocket 完整流程）
4. **低优**: HermesTask 表注册架构统一（建议 review）

---

## CHANGELOG v0.6.0

```markdown
## [0.6.0] - 2026-04-19
### Added
- Hermes REST API: POST/GET/DELETE /api/v1/hermes/tasks
- WebSocket 实时推送 Phase 0-8 进度
- GAN Runner 集成（Engineering 任务走完整 Phase 0-8）
- Evolution Engine（基于历史日志的优化建议）

### Fixed
- Security: HermesTask 添加 user_id 隔离（所有查询按用户过滤）
- Security: WebSocket 端点添加任务归属验证
- Bug: task_id 响应字段映射错误
- Bug: stats/agents 端点缺少认证
- Bug: HermesTask 未注册进 Base.metadata
```
