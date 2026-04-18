'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  BookOpen, Code, Copy, Check, Key, Zap,
  Globe, Terminal, Box, ArrowRight, Hash
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

// 代码示例
const EXAMPLES = {
  curl: `curl -X POST 'https://api.manai.com/v1/auth/login' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'`,

  python: `import requests

API_BASE = "https://api.manai.com/v1"

# 登录获取token
def login(email: str, password: str):
    response = requests.post(f"{API_BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    return response.json()["access_token"]

# 创建视频生成任务
def create_task(token: str, prompt: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE}/generate",
        headers=headers,
        json={
            "prompt": prompt,
            "mode": "balanced",
            "duration": 5
        }
    )
    return response.json()

token = login("your@email.com", "password")
result = create_task(token, "一只猫在草地上奔跑")`,

  javascript: `const API_BASE = "https://api.manai.com/v1";

class ManAI {
  constructor(token) {
    this.token = token;
  }

  async login(email, password) {
    const res = await fetch(\`\${API_BASE}/auth/login\`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    this.token = data.access_token;
    return this.token;
  }

  async createTask(prompt, mode = "balanced", duration = 5) {
    const res = await fetch(\`\${API_BASE}/generate\`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": \`Bearer \${this.token}\`
      },
      body: JSON.stringify({ prompt, mode, duration })
    });
    return res.json();
  }
}

// 使用示例
const client = new ManAI();
await client.login("your@email.com", "password");
const task = await client.createTask("一只猫在草地上奔跑");`,
}

// 错误码
const ERROR_CODES = [
  { code: 400, name: 'BAD_REQUEST', description: '请求参数错误', solution: '检查请求体格式和参数类型' },
  { code: 401, name: 'UNAUTHORIZED', description: '未授权或Token过期', solution: '重新登录获取新Token' },
  { code: 402, name: 'PAYMENT_REQUIRED', description: '余额不足', solution: '充值账户或购买套餐' },
  { code: 403, name: 'FORBIDDEN', description: '权限不足', solution: '检查账户权限或升级套餐' },
  { code: 404, name: 'NOT_FOUND', description: '资源不存在', solution: '检查请求的资源ID是否正确' },
  { code: 429, name: 'RATE_LIMITED', description: '请求过于频繁', solution: '降低请求频率或申请提高配额' },
  { code: 500, name: 'INTERNAL_ERROR', description: '服务器内部错误', solution: '稍后重试或联系技术支持' },
  { code: 503, name: 'SERVICE_UNAVAILABLE', description: '服务不可用', solution: '上游服务暂时不可用，稍后重试' },
]

// 认证流程
const AUTH_FLOW = [
  { step: 1, title: '注册账号', description: '通过 POST /v1/auth/register 注册新账号', icon: Key },
  { step: 2, title: '登录获取Token', description: '通过 POST /v1/auth/login 获取访问令牌', icon: Hash },
  { step: 3, title: '携带Token请求', description: '在请求头 Authorization: Bearer <token> 中携带Token', icon: Globe },
  { step: 4, title: 'Token过期处理', description: 'Token有效期7天，过期需重新登录', icon: Terminal },
]

export default function SdkDocsPage() {
  const [activeExample, setActiveExample] = useState<'curl' | 'python' | 'javascript'>('curl')
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const handleCopy = async (code: string, id: string) => {
    await navigator.clipboard.writeText(code)
    setCopiedCode(id)
    toast.success('已复制到剪贴板')
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* 头部 */}
      <div className="sticky top-0 z-40 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">SDK文档</h1>
              <p className="text-sm text-gray-400">漫AI 开发者中心</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* 简介 */}
        <section className="mb-12">
          <h2 className="text-3xl font-bold mb-4">快速开始</h2>
          <p className="text-gray-400 text-lg leading-relaxed">
            漫AI 提供 RESTful API，支持视频生成、任务管理、账户查询等功能。
            所有API通过 HTTPS 访问，返回 JSON 格式数据。
          </p>
        </section>

        {/* 认证流程 */}
        <section className="mb-12">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Key className="w-5 h-5 text-cyan-400" />
            认证流程
          </h3>
          <div className="grid grid-cols-4 gap-4">
            {AUTH_FLOW.map((item) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: item.step * 0.1 }}
                className="bg-white/5 rounded-xl border border-white/10 p-4"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <item.icon className="w-4 h-4 text-cyan-400" />
                  </div>
                  <span className="text-cyan-400 font-mono text-sm">Step {item.step}</span>
                </div>
                <h4 className="font-medium mb-1">{item.title}</h4>
                <p className="text-sm text-gray-400">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* 代码示例 */}
        <section className="mb-12">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Code className="w-5 h-5 text-cyan-400" />
            代码示例
          </h3>
          
          {/* 语言切换 */}
          <div className="flex gap-2 mb-4">
            {(['curl', 'python', 'javascript'] as const).map((lang) => (
              <button
                key={lang}
                onClick={() => setActiveExample(lang)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  activeExample === lang
                    ? "bg-cyan-500/20 text-cyan-400"
                    : "bg-white/5 text-gray-400 hover:text-white"
                )}
              >
                {lang === 'curl' && <Terminal className="w-4 h-4 inline mr-2" />}
                {lang === 'python' && <Box className="w-4 h-4 inline mr-2" />}
                {lang === 'javascript' && <Zap className="w-4 h-4 inline mr-2" />}
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </button>
            ))}
          </div>

          {/* 代码块 */}
          <div className="relative">
            <div className="absolute top-3 right-3 z-10">
              <button
                onClick={() => handleCopy(EXAMPLES[activeExample], `example-${activeExample}`)}
                className="flex items-center gap-1 px-3 py-1.5 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
              >
                {copiedCode === `example-${activeExample}` ? (
                  <>
                    <Check className="w-4 h-4 text-green-400" />
                    已复制
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    复制
                  </>
                )}
              </button>
            </div>
            <pre className="bg-black/50 rounded-xl p-6 text-sm font-mono overflow-x-auto">
              <code className="text-gray-300">{EXAMPLES[activeExample]}</code>
            </pre>
          </div>
        </section>

        {/* 错误码 */}
        <section className="mb-12">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Box className="w-5 h-5 text-cyan-400" />
            错误码参考
          </h3>
          <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-4 text-gray-400 font-medium">状态码</th>
                  <th className="text-left p-4 text-gray-400 font-medium">错误名</th>
                  <th className="text-left p-4 text-gray-400 font-medium">说明</th>
                  <th className="text-left p-4 text-gray-400 font-medium">解决方案</th>
                </tr>
              </thead>
              <tbody>
                {ERROR_CODES.map((error) => (
                  <tr key={error.code} className="border-b border-white/5 hover:bg-white/5">
                    <td className="p-4">
                      <span className={cn(
                        "px-2 py-1 rounded text-xs font-mono",
                        error.code >= 500 ? "bg-red-500/20 text-red-400" :
                        error.code >= 400 ? "bg-amber-500/20 text-amber-400" :
                        "bg-green-500/20 text-green-400"
                      )}>
                        {error.code}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-purple-400">{error.name}</td>
                    <td className="p-4 text-gray-400">{error.description}</td>
                    <td className="p-4 text-gray-400">{error.solution}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 认证说明 */}
        <section className="mb-12">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Globe className="w-5 h-5 text-cyan-400" />
            认证说明
          </h3>
          <div className="space-y-4">
            <div className="bg-white/5 rounded-xl border border-white/10 p-6">
              <h4 className="font-medium mb-3">Bearer Token 认证</h4>
              <p className="text-gray-400 text-sm mb-4">
                所有需要认证的API调用，必须在请求头中携带有效的 JWT Token：
              </p>
              <div className="bg-black/30 rounded-lg p-4">
                <code className="text-cyan-400 text-sm">
                  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
                </code>
              </div>
            </div>

            <div className="bg-white/5 rounded-xl border border-white/10 p-6">
              <h4 className="font-medium mb-3">Token 有效期</h4>
              <ul className="text-gray-400 text-sm space-y-2">
                <li>• Access Token 有效期为 7 天</li>
                <li>• Token 过期后需要重新登录获取</li>
                <li>• 建议在客户端缓存 Token，但需要处理过期情况</li>
              </ul>
            </div>

            <div className="bg-white/5 rounded-xl border border-white/10 p-6">
              <h4 className="font-medium mb-3">公共端点</h4>
              <p className="text-gray-400 text-sm mb-4">
                以下端点不需要认证即可访问：
              </p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-mono">GET</span>
                  <code className="text-sm">/api/v1/health</code>
                  <span className="text-gray-500 text-xs">健康检查</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs font-mono">POST</span>
                  <code className="text-sm">/api/v1/auth/register</code>
                  <span className="text-gray-500 text-xs">用户注册</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs font-mono">POST</span>
                  <code className="text-sm">/api/v1/auth/login</code>
                  <span className="text-gray-500 text-xs">用户登录</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-mono">GET</span>
                  <code className="text-sm">/api/v1/bill/packages</code>
                  <span className="text-gray-500 text-xs">套餐列表</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 限流说明 */}
        <section className="mb-12">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-cyan-400" />
            限流说明
          </h3>
          <div className="bg-white/5 rounded-xl border border-white/10 p-6">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-2">用户级限流</h4>
                <p className="text-gray-400 text-sm">10 requests/minute</p>
                <p className="text-gray-500 text-xs mt-1">基于用户ID进行限制</p>
              </div>
              <div>
                <h4 className="font-medium mb-2">IP级限流</h4>
                <p className="text-gray-400 text-sm">60 requests/minute</p>
                <p className="text-gray-500 text-xs mt-1">基于IP地址进行限制</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-sm text-gray-400">
                限流后会返回 <code className="text-amber-400">429 Too Many Requests</code> 错误，
                请在代码中处理此错误并进行退避重试。
              </p>
            </div>
          </div>
        </section>

        {/* 链接 */}
        <section className="flex gap-4 justify-center pt-8 border-t border-white/10">
          <a 
            href="/api-docs" 
            className="flex items-center gap-2 px-6 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors"
          >
            <BookOpen className="w-5 h-5" />
            API文档
            <ArrowRight className="w-4 h-4" />
          </a>
          <a 
            href="/docs" 
            target="_blank"
            className="flex items-center gap-2 px-6 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors"
          >
            <Globe className="w-5 h-5" />
            Swagger UI
            <ArrowRight className="w-4 h-4" />
          </a>
        </section>
      </div>
    </div>
  )
}
