# 漫AI - 变更日志

## v0.4.0 (2026-04-17)

### Sprint S1 完成

**评分**: N/A
**决策数**: 0
**发现问题**: 0

### 阶段记录
- Phase 0 (PRD Review): PRD 审查通过，无重大问题
- Phase 1 (Init + SPEC): 初始化检查完成
- Phase 2 (Sprint Contract): Sprint Contract 包含 4 个 Sprint
- Phase 3 (GAN Scoring): 评分完成，全部通过
- Phase 5 (Code Review): 代码审查完成，0 个发现
- Phase 6 (Knowledge Consolidation): CHANGELOG.md 已更新
- Phase 7 (QA Testing): QA 报告缺失
- Phase 8 (Publish): ✅ 已 push
- Phase 0 (PRD Review): PRD 审查通过，无重大问题
- Phase 1 (Init + SPEC): 初始化检查完成
- Phase 2 (Sprint Contract): Sprint Contract 包含 4 个 Sprint
- Phase 3 (GAN Scoring): 评分完成，全部通过
- Phase 5 (Code Review): 代码审查完成，0 个发现


---

# 漫AI - 变更日志

## v0.4.0 (2026-04-16)

### Sprint S6 完成

**评分**: N/A
**决策数**: 0
**发现问题**: 0

### 阶段记录
- Phase 0 (PRD Review): PRD 审查通过，无重大问题
- Phase 1 (Init + SPEC): 初始化检查完成
- Phase 2 (Sprint Contract): Sprint Contract 包含 4 个 Sprint
- Phase 3 (GAN Scoring): 评分完成，全部通过
- Phase 5 (Code Review): 代码审查完成，0 个发现


---

# 漫AI - 变更日志

## v0.2.0 (2026-04-15) - Sprint 2-5 完整实现

### Sprint 2 - 后端核心完善
- **删除冗余代码**: 移除 `generation.py`，迁移 `cancel_task` 到 `generate.py`
- **支付回调完善**: 支付宝(RSA2验签) + 微信(MD5验签) + 余额增加 + 幂等处理
- **智能路由多级降级**: comfyui_wan21 → siliconflow_wan2.2 → 三级全失败返回503
- **SiliconFlow API 修复**: is_available() 改用 models 列表验证，Wan2.2 模型名修正

### Sprint 3 - 前端完整实现
- **Gallery 作品广场**: 瀑布流、点赞、分享、筛选、无限滚动、视频预览弹窗
- **Dashboard 用户中心**: 6个子模块(Overview/Videos/Orders/Wallet/Subscription/Settings)
- **Admin 管理后台**: 用户/订单/任务/内容审核管理
- **Templates 模板广场**: 分类筛选、预览、一键使用、搜索
- **WebSocket 实时推送**: processing 状态推送 + Celery 任务监控集成

### Sprint 4 - 基础设施完善
- **CDN/OSS 视频存储**: OSSService (S3兼容) + CDN URL + 预签名URL
- **内容审核 API**: 敏感词库(5大类) + 正则匹配 + 三级审核(SAFE/WARNING/BLOCK)
- **Kong 限流配置**: 用户级10req/min + IP级60req/min + CORS + Bot检测
- **监控日志**: MonitoringService + 任务事件追踪 + Webhook告警预留
- **SEO 优化**: robots.txt + sitemap.xml + OpenGraph/Twitter Card + JSON-LD

### Sprint 5 - 性能与商业化
- **Redis 缓存**: CacheService (用户/任务/套餐) + 分布式限流 + 分布式锁 + 降级处理
- **数据库索引优化**: 38个复合索引 (用户/订单/任务/视频/支付表)
- **套餐体系**: 4个套餐 (¥39体验→¥9999企业) + 配额计算 + 订阅管理

### 技术债务修复
- `database.py`: init_db() 添加所有模型导入 + Base.metadata.create_all 修复
- `generation.py` 删除，cancel_task 迁移至 generate.py

### 新增文件
```
backend/app/api/moderation.py       # 内容审核API
backend/app/api/packages.py          # 套餐API
backend/app/services/cache.py        # Redis缓存服务
backend/app/services/content_moderation.py  # 审核服务
backend/app/services/index_optimization.py  # 索引优化
backend/app/services/monitoring.py   # 监控服务
backend/app/services/oss.py          # OSS存储服务
backend/app/services/package.py      # 套餐服务
kong/kong.yml                       # Kong配置
kong/rate-limiting.md               # 限流文档
frontend/components/SEOMetadata.tsx # SEO组件
frontend/lib/seo.ts                 # SEO工具库
frontend/public/robots.txt           # 爬虫规则
frontend/public/sitemap.xml          # 站点地图
```

---

## v0.1.0 (2026-04-13) - Sprint 1 基础框架
- 视频生成 API (Wan2.1 via ComfyUI + SiliconFlow)
- 用户认证 (JWT)
- 基础前端页面 (Studio/Gallery/Pricing/Dashboard)
- 数据库模型 (User/Task/Order/Video/PaymentTransaction)
