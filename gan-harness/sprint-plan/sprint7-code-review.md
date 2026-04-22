# Sprint 7 Hermes API - Phase 5 代码审查报告

**审查日期**: 2026-04-18
**审查人**: Hermes Agent
**Sprint**: S7 Hermes API 集成

---

## 审查范围

| 文件 | 路径 | 审查状态 |
|------|------|---------|
| HermesTask 模型 | `backend/app/hermes/models.py` | ✅ 已审查 |
| 状态管理器 | `backend/app/hermes/state.py` | ✅ 已审查 |
| REST/WebSocket API | `backend/app/api/hermes.py` | ✅ 已审查 |

---

## Phase 4 修复验证

### ✅ P0-1: HermesTask 添加 user_id 字段

**位置**: `backend/app/hermes/models.py:46`

```python
user_id: int = Field(foreign_key="users.id", index=True, description="所属用户ID")
```

**审查结果**: 
- 外键约束正确指向 `users.id`
- 已建立索引 `index=True`
- 字段描述清晰

---

### ✅ P0-2: list_tasks() 添加 user_id 过滤

**位置**: `backend/app/hermes/state.py:139-177`

```python
async def list_tasks(
    self,
    user_id: Optional[int] = None,  # 新增参数
    ...
):
    query = select(HermesTask)
    if user_id is not None:
        query = query.where(HermesTask.user_id == user_id)
```

**审查结果**: 
- 参数传递正确
- 过滤逻辑正确
- 总数查询也正确应用了 user_id 过滤

---

### ✅ P0-3: get_task() 添加 user_id 验证

**位置**: `backend/app/hermes/state.py:69-76`

```python
async def get_task(self, task_id: str, user_id: Optional[int] = None):
    query = select(HermesTask).where(HermesTask.id == task_id)
    if user_id is not None:
        query = query.where(HermesTask.user_id == user_id)
```

**审查结果**: 过滤逻辑正确

---

### ✅ P0-4: API 层 user_id 传递

| API 端点 | 位置 | user_id 传递 | 验证方式 |
|----------|------|--------------|----------|
| POST /tasks | api/hermes.py:76 | ✅ `user_id=current_user.id` | 创建时绑定 |
| GET /tasks | api/hermes.py:278 | ✅ `user_id=current_user.id` | 过滤查询 |
| GET /tasks/{id} | api/hermes.py:299 | ✅ `user_id=current_user.id` | 过滤查询 |
| DELETE /tasks/{id} | api/hermes.py:312 | ✅ 双重验证 | get_task + 显式检查 |

---

### ✅ P1-5: HermesTaskResponse task_id → id 修复

**位置**: `backend/app/hermes/models.py:138-140`, `api/hermes.py:37`

```python
class HermesTaskResponse(SQLModel):
    id: str  # 而非 task_id
```

**审查结果**: 字段名已正确修复

---

### ✅ P2-6: cancel_hermes_task 添加 response_model

**审查结果**: 正确

---

### ✅ P2-7: list_agents 和 get_stats 添加认证

**审查结果**: 
- `/agents` - ✅ 有 `Depends(get_current_user)`
- `/stats` - ✅ 有 `Depends(get_current_user)`

---

## 新发现的问题

### ⚠️ Medium: WebSocket 事件订阅未验证任务归属

**位置**: `api/hermes.py:342-396`

**问题描述**: 
WebSocket 端点 `/events/{task_id}` 仅验证 JWT token 有效，但未验证 task 是否属于该用户。任何认证用户可以订阅任意任务的事件流。

```python
@router.websocket("/events/{task_id}")
async def hermes_websocket_events(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(...),
):
    user_id = decode_token(token)  # 只验证 token
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # ❌ 缺少: 验证 task 是否属于该 user_id
    await websocket.accept()
    ...
```

**影响**: 用户 A 可以看到用户 B 任务执行进度的实时推送（不含敏感数据，但可能被用于探测任务存在性）

**建议修复**:
```python
# 在 accept() 之前添加
task = await hermes_state.get_task(task_id, user_id=user_id)
if not task:
    await websocket.close(code=4003, reason="Task not found")
    return
```

---

### ⚠️ Low: delete_task 无用户归属验证

**位置**: `backend/app/hermes/state.py:179-193`

**问题描述**: 
`delete_task` 方法通过 task_id 直接删除，未验证任务是否属于当前用户。API 层目前无 delete 端点，但如果未来添加则存在安全风险。

**建议**: 
- 选项 1: 添加 `user_id` 参数验证
- 选项 2: 保持在 API 层验证（当前 cancel_hermes_task 的模式）

---

### ⚠️ Low: update_task_result 无用户归属验证

**位置**: `backend/app/hermes/state.py:115-137`

**问题描述**: 
`update_task_result` 通过 task_id 直接更新结果，未验证任务归属。内部调用时可能存在风险。

**建议**: 考虑添加 `user_id` 参数进行安全验证

---

## 总体评估

| 方面 | 状态 | 说明 |
|------|------|------|
| P0 安全修复 | ✅ 完成 | user_id 隔离正确实现 |
| 核心功能 | ✅ 完成 | CRUD 操作正常 |
| 认证覆盖 | ✅ 完成 | 所有端点均有认证 |
| WebSocket 安全 | ⚠️ 需修复 | 未验证任务归属 |
| 内部方法安全 | ⚠️ 建议改进 | 部分方法无归属验证 |

---

## 审查结论

**通过条件**: 
- [x] P0 安全修复已正确实现
- [ ] WebSocket 任务归属验证（建议在发布前修复）

**建议**: 
1. 修复 WebSocket 端点的任务归属验证问题
2. 考虑为内部方法添加 user_id 验证作为防御性编程

**审查结果**: 🟡 有条件通过（待修复 WebSocket 问题后完全通过）

---

## 后续行动

| 问题 | 优先级 | 状态 |
|------|--------|------|
| WebSocket 任务归属验证 | Medium | 待修复 |
| delete_task 用户验证 | Low | 建议改进 |
| update_task_result 用户验证 | Low | 建议改进 |
