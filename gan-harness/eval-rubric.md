# Evaluation Rubric: 漫AI Sprint 1 — 视频生成 API 真实通路

## Pass Threshold: 7.0
Any criterion below 7.0 = FAIL. Any Critical issue = FAIL regardless of total score.

---

## Scoring Criteria（7维度）

### Feature Completeness (weight: 25%)
| Score | Meaning |
|-------|---------|
| 10 | 100% Sprint Contract 交付物完成，4项修复全部验收通过 |
| 7 | 核心功能完成，1-2个次要项缺失 |
| 4 | 核心功能部分完成 |
| 1 | Sprint Contract 完全未达成 |

### Functionality (weight: 20%)
| Score | Meaning |
|-------|---------|
| 10 | 所有 endpoint 正确，边界情况全覆盖 |
| 7 | 核心 CRUD 正常，边界情况有小缺陷 |
| 4 | endpoint 可工作但偶尔返回错误数据 |
| 1 | endpoint 崩溃或返回 500 |

### Code Quality (weight: 20%)
| Score | Meaning |
|-------|---------|
| 10 | 完美：类型提示、docstring、无重复、配置外置 |
| 7 | 好：文档或命名有 minor gaps |
| 4 | 明显问题：缺类型提示、函数名不清晰 |
| 1 | 不可读或有不安全代码 |

### Visual Design (weight: 15%) — 前端项目时启用
| Score | Meaning |
|-------|---------|
| 10 | UI/UX 无懈可击 |
| 7 | 好，有 minor 不一致 |
| 4 | 有明显 UX 问题 |
| 1 | 不可用 |

### AI Integration (weight: 10%)
| Score | Meaning |
|-------|---------|
| 10 | AI 功能完美集成，SiliconFlow + ComfyUI 双通路正常 |
| 7 | 核心功能正常 |
| 4 | AI 功能部分可用 |
| 1 | AI 功能完全不可用 |

### Security (weight: 5%)
| Score | Meaning |
|-------|---------|
| 10 | 无安全漏洞 |
| 7 | minor 安全问题 |
| 4 | 有明显安全问题 |
| 1 | 严重安全漏洞 |

### Performance (weight: 5%)
| Score | Meaning |
|-------|---------|
| 10 | P95 < 目标，0 N+1 查询 |
| 7 | 轻微性能问题 |
| 4 | 明显性能问题 |
| 1 | 服务不可用 |

---

## Critical Issues (auto-FAIL)
1. 没有 response_model 的 endpoint
2. JSON 响应被序列化为字符串
3. 删除了数据但没真正移除
4. 路由算法返回错误的执行路径
5. SiliconFlow API Key 硬编码在代码中
6. ComfyUI API Key 暴露在前端
7. 核心功能完全不可用

---

## Test Scenarios (7个)

### Scenario 1: Health Check
```
GET /api/v1/health
→ 200 {"status": "ok", "version": "0.1.0"}
```

### Scenario 2: Route Preview
```
GET /api/v1/generate/route/preview?mode=balanced&duration=5
→ 200 {"execution_path": "comfyui_wan21", "estimated_time": 30, ...}
```

### Scenario 3: User Registration
```
POST /api/v1/auth/register {"name": "test", "email": "test@example.com", "password": "test123456"}
→ 201 或 409 (already exists)
```

### Scenario 4: Task Creation (authenticated)
```
POST /api/v1/generate {"mode": "balanced", "prompt": "银发少女跳舞", "duration": 5}
Authorization: Bearer <token>
→ 201 {"task_id": "<uuid>", "status": "queued"}
```

### Scenario 5: Task Status (authenticated)
```
GET /api/v1/generate/{task_id}
Authorization: Bearer <token>
→ 200 {"task_id": "...", "status": "queued|processing|completed|failed", "video_url": null or str}
```

### Scenario 6: Unauthorized Access
```
POST /api/v1/generate (no token)
→ 401 or 403 {"detail": "Not authenticated"}
```

### Scenario 7: Frontend Build
```bash
cd frontend && npm run build
→ exit code 0, no errors
```
