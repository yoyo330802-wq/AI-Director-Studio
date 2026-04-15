# Kong Rate Limiting Configuration
# Sprint 4: S4-F3 Kong限流

## Rate Limiting Strategy

### 限流规则
- **用户级限流**: 10 请求/用户/分钟 (针对 `/api/v1/generate` 端点)
- **IP级限流**: 60 请求/IP/分钟 (全局)
- **服务级限流**: 1000 请求/分钟 (全局)

### 实现方式
使用 Kong Plugin: `rate-limiting`

## Kong Declarative Configuration

```yaml
# kong.yml

services:
  # 视频生成服务
  - name: manai-generate
    url: http://backend:8000/api/v1/generate
    routes:
      - name: generate-route
        paths:
          - /api/v1/generate
        methods:
          - POST
          - GET
    plugins:
      # 用户级限流 (按 Authorization header 识别用户)
      - name: rate-limiting
        config:
          minute: 10
          policy: redis
          redis_host: redis
          redis_port: 6379
          fault_tolerant: true
          hide_client_headers: false
          header_name: X-RateLimit-Limit
          error_code: 429
          error_message: "请求过于频繁，请稍后再试"
      
      # IP级限流
      - name: ip-restriction
        config:
          allow:
            - 0.0.0.0/0
          deny: []
      
      # 请求大小限制
      - name: request-size-limiting
        config:
          allowed_payload_size: 10  # MB
          size_unit: megabytes

  # 其他API服务
  - name: manai-api
    url: http://backend:8000/api/v1
    routes:
      - name: api-route
        paths:
          - /api/v1
    plugins:
      - name: rate-limiting
        config:
          minute: 60
          policy: redis
          redis_host: redis
          redis_port: 6379
          fault_tolerant: true

  # 公开页面 (无限制)
  - name: manai-public
    url: http://frontend:3000
    routes:
      - name: public-route
        paths:
          - /
          - /gallery
          - /templates
          - /about
    plugins: []

# 全局插件
plugins:
  # 跨域
  - name: cors
    config:
      origins:
        - "*"
      methods:
        - GET
        - POST
        - PUT
        - DELETE
      headers:
        - Authorization
        - Content-Type
      credentials: true
      max_age: 3600

  # 响应压缩
  - name: gzip
    config:
      mime_types:
        - application/json
        - text/html
        - text/css
        - application/javascript

  # 日志
  - name: access-log
    config:
      log_level: info
```

## Redis Rate Limiting 配置

```bash
# 使用 Redis 作为限流存储
# 需要确保 Redis 可用

redis_conf:
  host: redis
  port: 6379
  database: 1  # 使用单独的 database 避免与其他用途冲突
  password: ${REDIS_PASSWORD}
```

## 返回 Headers

限流信息会通过以下 Headers 返回给客户端:

| Header | 说明 |
|--------|------|
| X-RateLimit-Limit-Minute | 允许的请求数/分钟 |
| X-RateLimit-Remaining-Minute | 剩余可用请求数 |
| X-RateLimit-Limit-Second | 允许的请求数/秒 (如有) |
| X-RateLimit-Remaining-Second | 剩余可用请求数/秒 (如有) |

## 错误响应

当请求被限流时，返回:

```json
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "Rate limit exceeded",
  "message": "请求过于频繁，请稍后再试",
  "retry_after": 60
}
```

## 前端处理

```typescript
// lib/api.ts

// 响应拦截器处理 429 限流
if (response.status === 429) {
  const retryAfter = response.headers.get('Retry-After') || 60
  toast.error(`请求过于频繁，请在 ${retryAfter} 秒后重试`)
  throw new Error('RATE_LIMIT_EXCEEDED')
}
```

## 测试限流

```bash
# 测试用户级限流
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/generate \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"prompt": "test"}'
  sleep 0.5
done

# 预期: 第11个请求返回 429
```
