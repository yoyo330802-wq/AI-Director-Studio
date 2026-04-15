# 漫AI Sprint 1 — GAN Phase 6 知识沉淀

**Sprint:** Sprint 1 — 视频生成 API 真实通路
**Date:** 2026-04-15
**GAN Score:** 9.05/10 ✅ PASS
**Phase:** Phase 6 — Documentation

---

## 1. 有效模式

### 1.1 SiliconFlow API（硅基流动）

**客户端位置:** `backend/app/clients/siliconflow_client.py`

**关键模式:**
- 统一 endpoint: `POST /video/submit` 提交任务
- 状态查询: `GET /video/submit/{task_id}`
- 认证: `Authorization: Bearer {api_key}` header
- 返回格式: `{"task_id": "xxx", ...}` 或 `{"id": "xxx", ...}`（兼容处理）
- 支持 model: `"vidu"` | `"kling"`（可灵）

```python
# 关键代码片段
endpoint = f"{self.BASE_URL}/video/submit"
payload = {
    "model": model,
    "prompt": prompt,
    "duration": duration,
    "aspect_ratio": aspect_ratio,
    "with_text": True,
}
```

**可用性检查:** `GET /balance`

### 1.2 ComfyUI Wan2.1

**客户端位置:** `backend/app/clients/comfyui_client.py`

**关键模式:**
- 系统状态: `GET /system_stats`
- 提交工作流: `POST /api/prompt` → 返回 `{"prompt_id": "xxx"}`
- 获取结果: `GET /history/{prompt_id}`
- 超时设置: 300 秒

**工作流结构（ WanVideo 节点）:**
```python
{
    "3": {"class_type": "CheckpointLoader", "inputs": {"ckpt_name": "Wan2.1_T2V_1.3B_bf16.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["3", 0]}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt, "clip": ["3", 1]}},
    "6": {"class_type": "WanVideo", "inputs": {"video_length": duration * 16, "size": "1280x720", ...}},
    "7": {"class_type": "SaveVideo", "inputs": {"video": ["6", 0], "filename_prefix": "manai_wan21"}}
}
```

**轮询策略:** 每 5 秒轮询一次，最多等待 60 次（300 秒）

### 1.3 路由算法

**位置:** `backend/app/services/router.py`

**QualityMode 枚举:**
- `cost` → Wan2.1 via ComfyUI
- `balanced` → ≤30秒用 Wan2.1，>30秒用 Vidu
- `quality` → Vidu via SiliconFlow

**执行路径枚举:**
- `comfyui_wan21` — Wan2.1-1.3B
- `siliconflow_vidu` — Vidu
- `siliconflow_kling` — 可灵

**关键阈值:** `BALANCED_DURATION_THRESHOLD = 30` 秒

### 1.4 前端 API 规范

**位置:** `frontend/lib/api.ts`

**关键模式:**
- Axios 实例，baseURL `/api`（本地通过 Next.js rewrite 代理）
- 请求拦截器自动注入 `Authorization: Bearer {token}`
- 401 响应自动清除 token
- 所有 API 路径以 `/v1/` 开头

**认证端点:**
- `POST /v1/auth/register`
- `POST /v1/auth/login`

**生成端点:**
- `POST /v1/generate` — 创建任务
- `GET /v1/generate/{task_id}` — 查询状态
- `GET /v1/generate/route/preview?mode=&duration=` — 路由预览

---

## 2. 遇到的问题

### 2.1 endpoint 问题

**问题描述:** SiliconFlow API endpoint 需要正确对接 `https://api.siliconflow.cn/v1/video/submit`

**解决方案:** 确认使用统一的 `/video/submit` endpoint，状态查询用 `/video/submit/{task_id}`

### 2.2 格式问题

**问题描述:** SiliconFlow 返回格式可能有 `task_id` 或 `id` 字段

**解决方案:** 兼容处理 `result.get("task_id") or result.get("id")`

### 2.3 FormData 问题

**说明:** Sprint 1 阶段未涉及文件上传，ComfyUI 的视频通过 `/view?filename=xxx` URL 直接访问

### 2.4 ngrok 稳定性

**问题描述:** ComfyUI Wan2.1 运行在 Colab 通过 ngrok 暴露，ngrok 免费版连接不稳定

**影响:** 长时间视频生成任务可能因连接中断失败

**建议:** 后续考虑使用 Cloudflare Tunnel 或固定出口 IP

---

## 3. 工具使用

### 3.1 烟雾测试（Smoke Testing）

GAN-Evaluator 执行了 7 个测试场景，全部通过：
1. `GET /api/v1/health` — 健康检查
2. `GET /api/v1/generate/route/preview?mode=balanced&duration=5` — 路由预览
3. `POST /api/v1/auth/register` — 用户注册
4. `POST /api/v1/generate` — 创建生成任务（需认证）
5. `GET /api/v1/generate/{task_id}` — 查询任务状态
6. 未授权访问测试 — 401 正确返回
7. `cd frontend && npm run build` — 前端构建

### 3.2 GAN-Evaluator

**位置:** `gan-harness/feedback/feedback-001.md`

**评分维度（7维度加权）：**
| 维度 | 权重 | 得分 |
|------|------|------|
| Feature Completeness | 25% | 10 |
| Functionality | 20% | 10 |
| Code Quality | 20% | 8 |
| Visual Design | 15% | 7 |
| AI Integration | 10% | 10 |
| Security | 5% | 10 |
| Performance | 5% | 8 |

**加权总分:** 9.05/10
**Critical Issues:** 0

### 3.3 后端启动

```bash
cd backend
uvicorn app.main:app --reload --port 8002
```

---

## 4. 性能数据

### 4.1 GAN 评分

- **总分:** 9.05/10
- **Sprint Contract 完成度:** 100% (4/4 修复项)
- **测试场景通过率:** 7/7 (100%)
- **Critical Issues:** 0

### 4.2 预估时间

| 执行路径 | 预估时间 |
|----------|----------|
| Wan2.1 via ComfyUI | 30 秒 |
| Vidu via SiliconFlow | 60 秒 |
| 可灵 via SiliconFlow | 90 秒 |

### 4.3 质量评分

| 执行路径 | 质量评分 |
|----------|----------|
| Wan2.1 via ComfyUI | 7 |
| Vidu via SiliconFlow | 8 |
| 可灵 via SiliconFlow | 9 |

---

## 5. 下次改进建议

### 5.1 Code Quality（当前 8分）

- 增加更多类型注解的边界检查
- 统一错误处理日志格式
- 添加更多单元测试覆盖边界情况

### 5.2 Visual Design（当前 7分）

- 前端 UI 细节优化
- 加载状态动画完善
- 错误提示信息更友好

### 5.3 Performance（当前 8分）

- ComfyUI 轮询优化：可考虑 WebSocket 实时推送
- 添加请求缓存减少重复查询
- 考虑连接池复用

### 5.4 技术债务

1. **ngrok 稳定性：** 考虑迁移到更稳定的隧道方案
2. **视频存储：** 当前视频 URL 直接返回，缺少 CDN 加速
3. **重试机制：** 任务失败后自动重试逻辑
4. **监控告警：** 缺少任务超时和 API 可用性监控

### 5.5 GAN 工作流优化

- Phase 3 评分发现的问题应尽快在 Phase 4 修复循环中解决
- Critical Issues 为 0 是理想状态，保持这一标准

---

## 6. 参考文件

| 文件 | 描述 |
|------|------|
| `gan-harness/feedback/feedback-001.md` | GAN 评审报告 |
| `backend/app/clients/siliconflow_client.py` | 硅基流动 API 客户端 |
| `backend/app/clients/comfyui_client.py` | ComfyUI Wan2.1 客户端 |
| `backend/app/services/router.py` | 智能路由服务 |
| `backend/app/api/generate.py` | 视频生成 API 端点 |
| `frontend/lib/api.ts` | 前端 API 客户端 |

---

## 7. 后续计划

Phase 5 → Code Review → Phase 6（本文档）→ Phase 7 QA → Phase 8 Release
