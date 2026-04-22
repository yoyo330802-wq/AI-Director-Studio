# Sprint 7 Hermes API Phase 3 问题修复报告

## 修复日期
2026-04-18

## P0 - 安全 Critical（Security 4.0 根因修复）

### 问题 1: HermesTask 添加 user_id 字段

**文件**: `backend/app/hermes/models.py`
**行数**: 第 46 行（新增）
**修改内容**: 在 `HermesTask` 模型中添加 `user_id: int = Field(foreign_key="users.id", index=True)`

```python
user_id: int = Field(foreign_key="users.id", index=True, description="所属用户ID")
```

**验证方法**: 
- 检查 `HermesTask` 模型包含 `user_id` 字段
- 确认字段有外键约束指向 `users.id`
- 确认字段已建立索引

---

### 问题 2: list_tasks() 添加 user_id 参数过滤

**文件**: `backend/app/hermes/state.py`
**行数**: 第 140 行（新增参数）, 第 150-151 行（过滤逻辑）, 第 160-170 行（总数查询）
**修改内容**: 
1. `list_tasks()` 方法签名添加 `user_id: Optional[int] = None` 参数
2. 查询时添加 `where(HermesTask.user_id == user_id)` 过滤条件
3. 总数查询同样应用 user_id 过滤

```python
async def list_tasks(
    self,
    user_id: Optional[int] = None,  # 新增
    status: Optional[HermesTaskStatus] = None,
    agent_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[HermesTask], int]:
```

**验证方法**: 调用 `list_tasks(user_id=X)` 只返回该用户的任务

---

### 问题 3: get_task() 添加 user_id 参数验证

**文件**: `backend/app/hermes/state.py`
**行数**: 第 68-77 行
**修改内容**: `get_task()` 方法添加 `user_id: Optional[int] = None` 参数，验证任务归属

```python
async def get_task(self, task_id: str, user_id: Optional[int] = None) -> Optional[HermesTask]:
    async with AsyncSessionLocal() as session:
        query = select(HermesTask).where(HermesTask.id == task_id)
        if user_id is not None:
            query = query.where(HermesTask.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
```

**验证方法**: 调用 `get_task(task_id, user_id=X)` 如果任务不属于该用户则返回 None

---

### 问题 4: API 层 user_id 传递与归属验证

**文件**: `backend/app/api/hermes.py`

#### 4a. create_hermes_task() 传入 user_id
**行数**: 第 76 行
```python
task = await hermes_state.create_task(
    command=request.command,
    agent_type=agent_type,
    sprint=sprint,
    user_id=current_user.id,  # 新增
)
```

#### 4b. list_hermes_tasks() 传入 user_id
**行数**: 第 278 行
```python
tasks, total = await hermes_state.list_tasks(
    user_id=current_user.id,  # 新增
    status=status_enum,
    agent_type=agent_type,
    limit=limit,
    offset=offset,
)
```

#### 4c. get_hermes_task() 传入 user_id
**行数**: 第 299 行
```python
task = await hermes_state.get_task(task_id, user_id=current_user.id)
```

#### 4d. cancel_hermes_task() 验证归属
**行数**: 第 309-317 行
```python
task = await hermes_state.get_task(task_id, user_id=current_user.id)
if not task:
    raise HTTPException(status_code=404, detail="Task not found")

if task.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized to cancel this task")
```

**验证方法**: 
- 用户 A 无法看到/操作用户 B 的任务
- 跨用户访问返回 404（get_task 层面）或 403（cancel 层面额外验证）

---

## P1 - 功能问题

### 问题 5: HermesTaskResponse task_id 字段修复

**文件**: `backend/app/hermes/models.py`
**行数**: 第 138 行
**修改内容**: `HermesTaskResponse` 使用 `id: str` 替代 `task_id: str`

```python
class HermesTaskResponse(SQLModel):
    """任务响应"""
    id: str  # 改为直接用 id
    command: str
```

**对应 API 修改**: `backend/app/api/hermes.py` 第 37 行
```python
def _task_to_response(task: HermesTask) -> HermesTaskResponse:
    return HermesTaskResponse(
        id=task.id,  # 从 task_id=task.id 改为 id=task.id
        command=task.command,
        ...
    )
```

**验证方法**: 响应 JSON 中字段名为 `id` 而非 `task_id`

---

## P2 - 其他

### 问题 6: cancel_hermes_task() 添加 response_model

**文件**: `backend/app/api/hermes.py`
**行数**: 第 304 行
**修改内容**: 添加 `response_model=dict`

```python
@router.delete("/tasks/{task_id}", response_model=dict, summary="取消任务")
async def cancel_hermes_task(
```

**验证方法**: DELETE /tasks/{task_id} 返回明确的 dict 类型

---

### 问题 7: get_stats() 和 list_agents() 添加认证

**文件**: `backend/app/api/hermes.py`

#### 7a. list_agents()
**行数**: 第 399 行
```python
@router.get("/agents", summary="列出可用Agent")
async def list_agents(current_user = Depends(get_current_user)):  # 新增认证
```

#### 7b. get_stats()
**行数**: 第 419 行
```python
@router.get("/stats", summary="获取统计信息")
async def get_stats(current_user = Depends(get_current_user)):  # 新增认证
```

**验证方法**: 未认证请求返回 401 Unauthorized

---

## 文件修改汇总

| 文件 | 修改类型 | 问题编号 |
|------|----------|----------|
| `backend/app/hermes/models.py` | 添加 user_id 字段，修复 task_id→id | P0-1, P1-5 |
| `backend/app/hermes/state.py` | 添加 user_id 参数到 create_task, get_task, list_tasks | P0-2, P0-3 |
| `backend/app/api/hermes.py` | 传递 user_id，添加认证，添加 response_model | P0-4, P2-6, P2-7 |

---

## 安全性验证

1. **用户隔离**: 用户只能看到和管理自己的 HermesTask
2. **外键约束**: `user_id` 字段通过外键约束确保数据完整性
3. **索引优化**: `user_id` 字段建立索引提升查询性能
4. **认证覆盖**: 所有 Hermès API 端点均需认证

---

## 数据库迁移说明

由于添加了 `user_id` 字段（外键），需要执行数据库迁移：

```sql
ALTER TABLE hermes_tasks ADD COLUMN user_id INTEGER REFERENCES users(id);
CREATE INDEX idx_hermes_tasks_user_id ON hermes_tasks(user_id);
```

如果使用 Alembic 迁移：
```bash
cd backend
alembic revision --autogenerate -m "Add user_id to HermesTask"
alembic upgrade head
```
