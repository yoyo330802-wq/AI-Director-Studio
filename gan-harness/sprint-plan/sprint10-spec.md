# Sprint 10 规格说明书 - OpenAPI文档完善 + 前端API Docs动态化

## 1. 背景与目标

**Sprint 10 聚焦**: OpenAPI文档完善 + 前端API Docs动态化

**现状分析**:
- 漫AI项目已有完整的后端API（FastAPI），OpenAPI已启用（`/docs`, `/openapi.json`）
- 前端有API Docs页面 (`/api-docs`)，但使用硬编码数据，未与OpenAPI集成
- 多处API端点缺少完整的schema定义和示例

**目标**:
1. 后端: 完善所有API端点的OpenAPI schema定义（request/response模型、示例、文档字符串）
2. 前端: API Docs页面从OpenAPI动态获取数据，支持在线调试
3. 覆盖: 认证、视频生成、计费、套餐、任务管理、Hermes、飞书等全量API

---

## 2. 功能清单

### S10-F1: 后端OpenAPI Schema完善

**目标文件**: `backend/app/api/*.py`

需要完善的API模块:
| 模块 | 端点数 | 状态 |
|------|--------|------|
| auth.py | 4 | 需补充response_model示例 |
| users.py | 3 | 需补充schema |
| generate.py | 6 | 部分已有docstring |
| billing.py | 6 | 需补充完整schema |
| packages.py | 9 | 需补充schema |
| moderation.py | 2 | 需补充schema |
| websocket.py | 1 | WebSocket特殊处理 |
| hermes.py | 8 | 需补充完整schema |
| feishu_bot.py | 4 | 需补充schema |

**具体任务**:
- [ ] 为所有端点添加`response_model`（使用Pydantic模型）
- [ ] 为所有端点添加`summary`和`description`
- [ ] 为复杂端点添加`examples`
- [ ] 统一错误响应格式

### S10-F2: 前端API Docs动态化

**目标文件**: `frontend/app/api-docs/page.tsx`

**当前状态**: 硬编码API_ENDPOINTS数组

**改进方案**:
1. 页面加载时从 `/api/v1/openapi.json` 获取schema
2. 解析schema生成API分类和端点列表
3. 支持展示request/response示例
4. 支持"在线调试"功能（调用API）

**新增功能**:
- [ ] OpenAPI schema动态加载
- [ ] API端点搜索过滤
- [ ] 请求/响应示例展示
- [ ] curl命令一键复制

### S10-F3: 新增SDK风格文档页

**目标文件**: `frontend/app/sdk-docs/page.tsx`

创建开发者友好的SDK文档页面:
- [ ] 认证授权说明
- [ ] 快速开始指南
- [ ] 各语言SDK示例（curl, Python, JavaScript）
- [ ] 错误码参考

---

## 3. 技术方案

### 3.1 后端OpenAPI增强

```python
# 示例: 完善后的billing.py
from pydantic import BaseModel, Field
from typing import Optional, List

class BalanceResponse(BaseModel):
    """余额响应"""
    balance: float = Field(..., description="账户余额(元)")
    video_quota: int = Field(..., description="视频配额(秒)")
    video_used: int = Field(..., description="已用配额(秒)")
    video_remaining: int = Field(..., description="剩余配额(秒)")

class OnDemandPricingResponse(BaseModel):
    """按需计费价格表响应"""
    billing_type: str = Field(default="on_demand")
    currency: str = Field(default="CNY")
    modes: List[dict] = Field(..., description="各模式价格配置")

@router.get(
    "/on-demand/pricing",
    response_model=OnDemandPricingResponse,
    summary="按需计费价格表",
    description="返回各质量模式的每秒价格和预估生成时间",
    responses={
        200: {"description": "价格表获取成功"},
        401: {"description": "未授权"},
    }
)
async def get_on_demand_pricing():
    """..."""
```

### 3.2 前端API Docs动态化

```typescript
// 页面加载时获取OpenAPI schema
useEffect(() => {
  fetch('/api/v1/openapi.json')
    .then(res => res.json())
    .then(data => {
      // 解析paths生成端点列表
      // 解析components/schemas生成模型定义
      setSchema(data)
    })
}, [])

// 解析OpenAPI路径
const parseEndpoints = (paths: any) => {
  return Object.entries(paths).map(([path, methods]) => ({
    path,
    methods: Object.entries(methods as any).map(([method, details]) => ({
      method: method.toUpperCase(),
      ...(details as any)
    }))
  }))
}
```

---

## 4. 文件变更

### 新增文件
```
frontend/app/sdk-docs/page.tsx          # SDK文档页
backend/app/api/_schemas.py            # 共享API Schema定义
```

### 修改文件
```
backend/app/api/auth.py                 # OpenAPI schema完善
backend/app/api/users.py                # OpenAPI schema完善
backend/app/api/generate.py             # OpenAPI schema完善
backend/app/api/billing.py              # OpenAPI schema完善
backend/app/api/packages.py             # OpenAPI schema完善
backend/app/api/moderation.py           # OpenAPI schema完善
backend/app/api/hermes.py               # OpenAPI schema完善
backend/app/api/feishu_bot.py           # OpenAPI schema完善
backend/app/main.py                     # 添加/openapi.json路由
frontend/app/api-docs/page.tsx          # 动态化改造
```

---

## 5. 验收标准

1. **后端验收**:
   - [ ] 所有REST端点有完整的`response_model`
   - [ ] 所有端点有`summary`和`description`
   - [ ] 访问`/docs`可以看到完整的Swagger UI文档
   - [ ] 访问`/openapi.json`返回有效的OpenAPI 3.0 JSON

2. **前端验收**:
   - [ ] API Docs页面从OpenAPI动态加载数据
   - [ ] 支持按名称/路径搜索API
   - [ ] 展示每个端点的请求/响应示例
   - [ ] 一键复制curl命令

3. **文档验收**:
   - [ ] SDK Docs页面包含快速开始指南
   - [ ] 包含认证授权说明
   - [ ] 包含常见错误码参考
