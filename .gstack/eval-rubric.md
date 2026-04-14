# EVAL RUBRIC: 漫AI — Sprint 1

> Sprint: S1
> Generated: 2026-04-14

---

## 7 Test Scenarios

### Scenario 1: 用户注册
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "name": "测试用户"}'

Expected: 201
{"user_id": 1, "email": "test@example.com", "token_balance": 100}
```

### Scenario 2: 用户登录
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

Expected: 200
{"access_token": "eyJ...", "token_type": "bearer"}
```

### Scenario 3: 提交生成任务 (cost模式 - ComfyUI)
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"prompt": "动漫女孩在樱花树下", "duration": 5, "quality_mode": "cost", "aspect_ratio": "16:9"}'

Expected: 202
{"task_id": "uuid", "status": "queued", "estimated_time": 15}
```

### Scenario 4: 余额不足
```bash
# 先消耗余额至<1Token
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Authorization: Bearer <token>" \
  -d '{"prompt": "测试", "duration": 5, "quality_mode": "cost", "aspect_ratio": "16:9"}'

Expected: 402
{"detail": "Insufficient token balance"}
```

### Scenario 5: 查询任务状态
```bash
curl http://localhost:8000/api/v1/generate/{task_id} \
  -H "Authorization: Bearer <token>"

Expected: 200
{"task_id": "uuid", "status": "completed", "progress": 100, "video_url": "http://...", "error": null}
```

### Scenario 6: 获取用户信息(含余额)
```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token>"

Expected: 200
{"user_id": 1, "email": "test@example.com", "name": "测试用户", "token_balance": 95}
```

### Scenario 7: 未授权
```bash
curl http://localhost:8000/api/v1/users/me

Expected: 401
{"detail": "Not authenticated"}
```

---

## Scoring Rubric

### Feature Completeness (25%)
| Score | Meaning |
|-------|---------|
| 10 | 4个功能全部完整 |
| 7 | 3个完整，1个minor缺陷 |
| 4 | 2个完整 |
| 1 | 功能不工作 |

### Functionality (20%)
| Score | Meaning |
|-------|---------|
| 10 | 所有endpoint按预期工作 |
| 7 | 核心正常，minor边界问题 |
| 4 | 核心有问题 |
| 1 | 完全不工作 |

### Code Quality (20%)
| Score | Meaning |
|-------|---------|
| 10 | 完美：无hardcoded/类型提示完整/无重复 |
| 7 | 好，minor问题 |
| 4 | 明显问题 |
| 1 | 不可读 |

### AI Integration (10%)
| Score | Meaning |
|-------|---------|
| 10 | ComfyUI客户端 + 硅基流动客户端 + 路由正确 |
| 7 | 客户端存在，路由minor问题 |
| 4 | 只有mock |
| 1 | 无集成 |

### Security (5%)
| Score | Meaning |
|-------|---------|
| 10 | bcrypt/JWT/输入验证正确 |
| 7 | minor问题 |
| 4 | 明显缺陷 |
| 1 | 严重漏洞 |

### Performance (5%)
| Score | Meaning |
|-------|---------|
| 10 | 无N+1，提交<200ms |
| 7 | minor问题 |
| 4 | 明显问题 |
| 1 | 服务不可用 |

---

## Sprint Contract: S1

### 交付物
- [ ] F001: 用户注册/登录/查询
- [ ] F002: Token余额/扣费逻辑
- [ ] F003: cost/balanced/quality三种路由
- [ ] F004: 任务提交/进度/WebSocket

### 测试标准
- [ ] curl所有endpoint返回正确status
- [ ] JWT有效且未过期
- [ ] 余额不足返回402
- [ ] WebSocket连接可建立
- [ ] 任务状态流转: queued → processing → completed
