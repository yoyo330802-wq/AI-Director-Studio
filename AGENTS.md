# 漫AI — Agent 团队协作指南

## 项目背景

**漫AI** — 国产动漫创作 AI 视频 Token 平台，定位：比官网便宜 30%

**技术栈**：
- 前端：Next.js 14 + TypeScript
- 后端：FastAPI + SQLModel + Pydantic v2
- 网关：Kong
- 任务队列：Celery + Redis
- GPU 集群：Wan2.1 自建（4×H100）+ 硅基流动可灵 API
- 数据库：PostgreSQL 16 + pgvector
- 存储：OSS/S3

**当前 Sprint**：Sprint 1 — 视频生成 API 真实通路

---

## Agent 团队

| Agent | Profile | 职责 | 触发条件 |
|-------|---------|------|---------|
| planner | `planner` | PRD质疑、spec、Sprint Contract | "开发XXX功能" |
| researcher | `researcher` | 竞品分析、技术调研 | "调研XXX" |
| coder | `coder` | 按 spec 实现代码 | Sprint Contract 签署后 |
| reviewer | `reviewer` | GAN-Evaluator 7维度评分 | coder 完成实现后 |
| writer | `writer` | 知识沉淀、文档撰写 | reviewer 评分 PASS 后 |

---

## 当前进度

### Sprint 1 — 视频生成 API 真实通路

**已完成**：
- SiliconFlow API 真实接入（`app/clients/siliconflow_client.py`）
- ComfyUI Wan2.1 真实 API 接入（`app/clients/comfyui_client.py`）
- `/v1/generate/route/preview` 端点（`app/api/generate.py`）
- 前端 mode→quality_mode 映射修复（`frontend/lib/api.ts`）

**待完成**：
- Phase 3: GAN-Evaluator 评分 ← **当前任务**
- Phase 4: 修复评分中发现的问题
- Phase 5-8: 代码审查、知识沉淀、QA、发布

---

## 技术约定

### API 设计
- REST JSON API，`/api/v1/` 前缀
- 错误格式：`{"detail": str}`
- 认证：`Authorization: Bearer <token>`（JWT）
- 分页：`{"total": N, "items": [...], "page": N, "limit": N}`

### 数据模型
- 使用 SQLModel（Pyydantic v2 + SQLAlchemy）
- 所有表有 `created_at`, `updated_at`
- UUID 主键

### 代码规范
- 类型提示完整
- 函数 docstring
- 错误处理显式
- 配置进 `app/config.py`

---

## GAN 工作流

```
Phase 0: PRD质疑（planner）
Phase 1: spec + eval-rubric（planner）
Phase 2: Sprint Contract → coder 实现
Phase 3: reviewer 评分
Phase 4: 修复循环（≤3次）
Phase 5: 代码审查
Phase 6: writer 知识沉淀
Phase 7: QA 测试
Phase 8: 发布
```

**Pass Threshold: 7.0**（7维度加权平均）

---

## 参考文件

- `gan-harness/spec.md` — 功能规格
- `gan-harness/eval-rubric.md` — 评分标准
- `gan-harness/feature-list.json` — 功能清单
- `gan-harness/feedback/` — 评审反馈
- `backend/app/` — 后端代码
- `frontend/` — 前端代码
