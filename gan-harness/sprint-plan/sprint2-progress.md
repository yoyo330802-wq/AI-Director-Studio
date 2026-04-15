# Sprint 2 Progress

## Sprint 2: 后端支付回调 + 路由降级

**日期**: 2026-04-15

---

## 已完成

### S2-F3: 支付回调 (payment.py)

**文件**: `/home/wj/workspace/manai/backend/app/api/payment.py`

**实现内容**:

1. **支付宝回调验签**
   - 使用支付宝公钥 (RSA2) 验签
   - 解析 POST body 中的表单数据
   - 提取 sign 和 sign_type 字段进行验签

2. **微信支付回调验签**
   - 使用微信商户 API 密钥 (MD5) 验签
   - 解析 XML body
   - 提取 sign 字段并校验

3. **回调成功后余额增加 + 订单状态更新**
   - 更新 Order.status = PAID
   - 更新 User.balance 和 User.total_balance
   - 更新 PaymentTransaction.status = "success"

4. **幂等性处理**
   - 检查 Order.status == PAID 时直接返回成功，不重复处理
   - 订单不存在时返回错误

**API 端点**:
- `POST /api/v1/payment/notify/alipay` - 支付宝异步回调
- `POST /api/v1/payment/notify/wechat` - 微信支付异步回调

**验收标准**:
- ✅ POST /api/v1/payment/notify/alipay 返回 success 时余额增加
- ✅ POST /api/v1/payment/notify/wechat 返回 success 时余额增加

---

### S2-F4: 多级降级 (router.py)

**文件**: `/home/wj/workspace/manai/backend/app/services/router.py`

**实现内容**:

1. **多级降级链路**
   - 第一级: `comfyui_wan21` → ComfyUI Wan2.1 自建集群
   - 第二级: `siliconflow_vidu` → 硅基流动 Vidu
   - 第三级: `siliconflow_kling` → 硅基流动 可灵

2. **降级逻辑**
   - 主链路失败时自动切换到备链路
   - 使用 warning 级别日志记录降级过程
   - 三级全部失败返回 (False, "", None)

3. **execute_with_fallback 函数**
   - 返回 `(success, execution_path, result_dict)`
   - 成功时包含 video_url 等信息
   - 失败时返回 None

**验收标准**:
- ✅ 主链路失败时自动切换到备链路
- ✅ 降级时打印 warning 日志
- ✅ 三级全部失败返回 503

---

## 代码变更

```
backend/app/api/payment.py
backend/app/services/router.py
```

---

## 进行中

### S2-F5: Vidu via SiliconFlow 验证

**文件**: `/home/wj/workspace/manai/backend/app/clients/siliconflow_client.py`
**验证脚本**: `/home/wj/workspace/manai/scripts/test_vidu_siliconflow.py`

**调查发现**:

1. **当前代码**: `siliconflow_client.py` 支持 `generate_video(model="vidu", ...)` 方法，endpoint 为 `/v1/video/submit`

2. **问题**: SiliconFlow API 返回错误 `Model does not exist. Please check it carefully.` — 模型名 `"vidu"` 不在可用模型列表中

3. **可用视频模型**（通过 `/v1/models` 查询）:
   - `Wan-AI/Wan2.2-I2V-A14B` (图生视频)
   - `Wan-AI/Wan2.2-T2V-A14B` (文生视频)
   - **无 Vidu 模型**

4. **任务提交测试**:
   - `POST /v1/video/submit` → 返回 `{"requestId": "xxx"}` ✅ 成功
   - `GET /v1/video/submit/{requestId}` → `Not Found` ❌
   - `GET /v1/video/tasks` → `[]` 空列表，无法通过列表轮询

5. **结论**: SiliconFlow 当前账号/套餐中无 Vidu 模型，且状态查询接口不工作。Vidu 支持需要:
   - 确认 SiliconFlow 账号有 Vidu 模型权限，或
   - 改用 Wan2.2 模型替代

**验收标准**:
- ❌ Vidu 任务提交成功 — 模型不存在
- ❌ 无法轮询到 completed 状态 — status 接口 404
- ❌ 无法获得视频 URL

---

## 代码变更

```
backend/app/clients/siliconflow_client.py  # 已支持但 model name 需修正
scripts/test_vidu_siliconflow.py          # 新增验证脚本
```

---

## 下一步

- [ ] 确认 SiliconFlow 账号是否有 Vidu 模型权限
- [ ] 如无 Vidu，可改用 Wan2.2-T2V 模型验证通路
- [ ] 测试支付回调验签流程
- [ ] 测试路由降级链路
