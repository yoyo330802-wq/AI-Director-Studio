# 漫AI Sprint Contract — 全模块开发规划

**日期**: 2026-04-15  
**Phase**: 0 (PRD质疑) + 1 (初始化) + 2 (Sprint Contract)  
**基于**: PRD v2.1 + 盘点报告 (inventory-backend-002.md, inventory-frontend-002.md)

---

## Phase 0: PRD 质疑 — 关键问题

### Q1: generation.py vs generate.py 冗余
两个文件功能高度重叠，都处理视频生成任务。
**决策**: 保留 `generate.py` (新版Sprint 1成果)，删除 `generation.py`

### Q2: payment.py 支付回调空实现
PRD 要求接入支付宝/微信支付，但回调 endpoint 只有 pass-through。
**决策**: S2 优先实现支付回调，先用模拟回调验证业务逻辑

### Q3: Vidu API 是否真实接入？
PRD 列出 Vidu 作为主力20%，但代码里有 vidu_client.py。
**决策**: 需要验证 vidu_client 是否可用 SiliconFlow 代替

### Q4: 前端 Gallery/Admin 功能不完整
PRD 要求完整功能，当前只是 stub。
**决策**: S3/S4 迭代完善，核心业务流程优先

### Q5: CDN/OSS 存储未实现
PRD 要求视频存储到 MinIO/OSS，但代码无相关实现。
**决策**: S4 才接入真实存储，S2/S3 用 URL 直接返回

---

## Phase 1: 模块依赖关系

```
[认证] auth.py
    ↓
[用户] users.py
    ↓
[路由] smart_router.py ──→ [Wan2.1] ──→ [ComfyUI]
         │                      ↑
         └──→ [SiliconFlow] ────┘
         │         │
         └──→ [Vidu] (via SiliconFlow)
    ↓
[生成] generate.py
    ↓
[计费] billing.py
    ↓
[支付] payment.py  ←── [支付宝/微信] 回调
    ↓
[存储] (S4才接入OSS)
```

---

## Sprint 划分

### Sprint 2: 支付闭环 + 路由增强
**目标**: 付费流程完整可用

| ID | 模块 | 功能 | 验收标准 |
|----|------|------|---------|
| S2-F1 | 代码清理 | 删除冗余 generation.py | 只有一个视频生成endpoint |
| S2-F2 | billing | validate_balance 完善 | token不足时返回明确错误 |
| S2-F3 | payment | 支付回调完整实现 | 支付宝/微信回调验签+到账 |
| S2-F4 | router | smart_router 多级降级 | 上游失败时自动切换 |
| S2-F5 | vidu | Vidu via SiliconFlow 真实调用 | 端到端视频生成成功 |

**验收**: 创建充值订单 → 模拟支付回调 → 余额增加 → 扣费生成视频

---

### Sprint 3: 前端体验增强
**目标**: Gallery/Admin 可用，Studio 功能完整

| ID | 模块 | 功能 | 验收标准 |
|----|------|------|---------|
| S3-F1 | gallery | 作品广场完整实现 | 瀑布流展示+点赞+分享 |
| S3-F2 | dashboard | 所有子模块完整 | 订单/钱包/会员/设置全可用 |
| S3-F3 | admin | 管理后台核心功能 | 用户管理+订单管理+任务管理 |
| S3-F4 | templates | 模板广场完善 | 分类筛选+模板预览+使用统计 |
| S3-F5 | websocket | Studio 实时进度 | 任务进度实时推送 |

**验收**: 用户可在 gallery 点赞 → dashboard 查看消费 → admin 看到数据

---

### Sprint 4: 运营增强
**目标**: 完整商业化功能

| ID | 模块 | 功能 | 验收标准 |
|----|------|------|---------|
| S4-F1 | CDN | 视频存储到 OSS/CDN | 视频 URL 可访问 |
| S4-F2 | 审核 | 内容审核 API | 违规提示词被拦截 |
| S4-F3 | 限流 | Kong 限流完善 | 并发10请求/用户/分钟 |
| S4-F4 | 监控 | 日志和告警 | 任务失败告警 |
| S4-F5 | SEO | 公开页面SEO | robots.txt + sitemap |

**验收**: 完整商业链路可跑通

---

### Sprint 5: 性能和商业化
**目标**: 99.5% SLA，产品级质量

| ID | 模块 | 功能 | 验收标准 |
|----|------|------|---------|
| S5-F1 | 数据库 | 索引优化+连接池 | 查询<50ms |
| S5-F2 | 缓存 | Redis 缓存热门数据 | 缓存命中率>60% |
| S5-F3 | 套餐 | 完整套餐体系 | 4档套餐完整 |
| S5-F4 | 文档 | API 完整文档 | Swagger 可测试 |
| S5-F5 | 回归 | 全模块 GAN 回归测试 | 全部 PASS |

---

## 当前 Sprint 状态

|| Sprint | 状态 | 评分 |
|--------|------|------|
|| S1 视频生成API | ✅ 完成 | 9.05/10 |
|| S2 支付闭环 | 🔄 进行中 | - |
|| S3 前端体验 | ⏳ 待开始 | - |
|| S4 运营增强 | ⏳ 待开始 | - |
|| S5 性能商业化 | ⏳ 待开始 | - |
|| S7 Hermes API | ✅ 完成 | - |

### Sprint S7 - Hermes API 集成 (2026-04-18)

**功能**:
- POST /api/v1/hermes/tasks 提交任务 (engineer/researcher/creator)
- WebSocket /api/v1/hermes/events/{task_id} 实时推送 Phase 0-8 进度
- GAN Runner 完整工作流集成
- Evolution Engine 执行日志与优化建议

**Phase 4 修复 (P0 Critical)**:
- user_id 数据隔离: HermesTask 添加 user_id，所有查询按用户过滤
- task_id 响应修复: HermesTaskResponse 使用 `id` 而非 `task_id`
- 认证覆盖: /stats 和 /agents 端点添加 JWT 认证

**代码审查**: 
- 状态: 🟡 有条件通过
- 问题: 3 个 (1 Medium, 2 Low) - 见 sprint7-code-review.md

**相关文件**:
- `backend/app/hermes/models.py`
- `backend/app/hermes/state.py`
- `backend/app/hermes/router.py`
- `backend/app/hermes/gan_runner.py`
- `backend/app/hermes/executor.py`
- `backend/app/hermes/evolution.py`
- `backend/app/api/hermes.py`
