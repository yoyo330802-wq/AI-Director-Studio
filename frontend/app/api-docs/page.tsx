'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, BookOpen, Code, Copy, Check,
  ChevronRight, ChevronDown, Play, Key,
  Terminal, Box, Lock, Zap
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

// API分类
const API_CATEGORIES = [
  { id: 'auth', name: '认证', icon: Lock },
  { id: 'users', name: '用户', icon: BookOpen },
  { id: 'generation', name: '视频生成', icon: Zap },
  { id: 'tasks', name: '任务管理', icon: Terminal },
  { id: 'videos', name: '作品管理', icon: Box },
  { id: 'payments', name: '支付', icon: Key },
]

// API端点
const API_ENDPOINTS = [
  // 认证
  {
    category: 'auth',
    method: 'POST',
    path: '/v1/auth/register',
    title: '用户注册',
    description: '注册新用户账号',
    params: [
      { name: 'username', type: 'string', required: true, description: '用户名(3-50字符)' },
      { name: 'email', type: 'string', required: false, description: '邮箱地址' },
      { name: 'password', type: 'string', required: true, description: '密码(至少6位)' },
    ],
    example: {
      request: '{"username": "creator", "email": "test@example.com", "password": "123456"}',
      response: '{"access_token": "eyJhbG...", "token_type": "bearer"}',
    },
  },
  {
    category: 'auth',
    method: 'POST',
    path: '/v1/auth/login',
    title: '用户登录',
    description: '登录获取访问令牌',
    params: [
      { name: 'username', type: 'string', required: true, description: '用户名' },
      { name: 'password', type: 'string', required: true, description: '密码' },
    ],
    example: {
      request: '{"username": "creator", "password": "123456"}',
      response: '{"access_token": "eyJhbG...", "token_type": "bearer"}',
    },
  },
  // 视频生成
  {
    category: 'generation',
    method: 'POST',
    path: '/v1/generations',
    title: '创建生成任务',
    description: '提交一个新的AI视频生成任务',
    params: [
      { name: 'prompt', type: 'string', required: true, description: '生成提示词(1-500字符)' },
      { name: 'mode', type: 'string', required: false, description: '生成模式: fast/balanced/premium' },
      { name: 'duration', type: 'integer', required: false, description: '视频时长: 5或10秒' },
      { name: 'aspect_ratio', type: 'string', required: false, description: '宽高比: 16:9/9:16/1:1' },
      { name: 'resolution', type: 'string', required: false, description: '分辨率: 480p/720p/1080p' },
      { name: 'image_url', type: 'string', required: false, description: '参考图片URL' },
    ],
    example: {
      request: '{"prompt": "一只猫在草地上奔跑", "mode": "balanced", "duration": 5}',
      response: '{"task_id": "task_abc123", "status": "pending", "estimated_cost": 0.06}',
    },
  },
  // 任务管理
  {
    category: 'tasks',
    method: 'GET',
    path: '/v1/tasks/{task_id}',
    title: '获取任务状态',
    description: '查询任务的当前状态和进度',
    params: [
      { name: 'task_id', type: 'string', required: true, description: '任务ID' },
    ],
    example: {
      request: '',
      response: '{"task_id": "task_abc123", "status": "processing", "progress": 45}',
    },
  },
  {
    category: 'tasks',
    method: 'GET',
    path: '/v1/tasks',
    title: '任务列表',
    description: '获取当前用户的任务列表',
    params: [
      { name: 'page', type: 'integer', required: false, description: '页码' },
      { name: 'page_size', type: 'integer', required: false, description: '每页数量' },
      { name: 'status', type: 'string', required: false, description: '状态过滤' },
    ],
    example: {
      request: '',
      response: '{"items": [...], "total": 100, "page": 1}',
    },
  },
  // 用户
  {
    category: 'users',
    method: 'GET',
    path: '/v1/users/me',
    title: '获取当前用户',
    description: '获取登录用户的基本信息',
    params: [],
    example: {
      request: '',
      response: '{"id": 1, "username": "creator", "balance": 100.00}',
    },
  },
  // 作品
  {
    category: 'videos',
    method: 'GET',
    path: '/v1/videos',
    title: '作品列表',
    description: '获取公开作品列表',
    params: [
      { name: 'page', type: 'integer', required: false, description: '页码' },
      { name: 'page_size', type: 'integer', required: false, description: '每页数量' },
      { name: 'category', type: 'string', required: false, description: '分类筛选' },
      { name: 'sort', type: 'string', required: false, description: '排序: latest/popular' },
    ],
    example: {
      request: '',
      response: '{"items": [...], "total": 1000}',
    },
  },
  {
    category: 'videos',
    method: 'GET',
    path: '/v1/videos/{id}',
    title: '作品详情',
    description: '获取单个作品的详细信息',
    params: [
      { name: 'id', type: 'integer', required: true, description: '作品ID' },
    ],
    example: {
      request: '',
      response: '{"id": 1, "title": "作品标题", "video_url": "https://..."}',
    },
  },
  // 支付
  {
    category: 'payments',
    method: 'GET',
    path: '/v1/payments/packages',
    title: '套餐列表',
    description: '获取所有可用的订阅套餐',
    params: [],
    example: {
      request: '',
      response: '[{"id": 1, "name": "创作者", "price": 39}]',
    },
  },
  {
    category: 'payments',
    method: 'POST',
    path: '/v1/payments/create',
    title: '创建订单',
    description: '创建充值或套餐购买订单',
    params: [
      { name: 'amount', type: 'number', required: false, description: '充值金额' },
      { name: 'package_id', type: 'integer', required: false, description: '套餐ID' },
      { name: 'payment_method', type: 'string', required: true, description: '支付方式: alipay/wechat' },
    ],
    example: {
      request: '{"package_id": 2, "payment_method": "alipay"}',
      response: '{"order_id": "123", "pay_url": "https://..."}',
    },
  },
]

const METHOD_COLORS = {
  GET: 'bg-green-500/20 text-green-400',
  POST: 'bg-blue-500/20 text-blue-400',
  PUT: 'bg-amber-500/20 text-amber-400',
  DELETE: 'bg-red-500/20 text-red-400',
}

export default function ApiDocsPage() {
  const [activeCategory, setActiveCategory] = useState('auth')
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // 过滤端点
  const filteredEndpoints = API_ENDPOINTS.filter(endpoint => {
    const matchesCategory = endpoint.category === activeCategory
    const matchesSearch = !searchQuery || 
      endpoint.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // 复制代码
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
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
                <Code className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">API文档</h1>
                <p className="text-sm text-gray-400">漫AI 开发者中心</p>
              </div>
            </div>
            
            {/* 搜索 */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索API..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-cyan-400/50"
                />
              </div>
            </div>
            
            {/* API Key按钮 */}
            <button className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors">
              <Key className="w-4 h-4" />
              获取API Key
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* 侧边栏 */}
          <aside className="w-56 flex-shrink-0">
            <nav className="space-y-1">
              {API_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                    activeCategory === cat.id
                      ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400"
                      : "text-gray-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <cat.icon className="w-5 h-5" />
                  {cat.name}
                </button>
              ))}
            </nav>
            
            {/* 快速链接 */}
            <div className="mt-8 p-4 bg-white/5 rounded-xl">
              <h4 className="text-sm font-medium mb-3">快速链接</h4>
              <div className="space-y-2 text-sm">
                <a href="#" className="block text-gray-400 hover:text-cyan-400">
                  开发者指南 →
                </a>
                <a href="#" className="block text-gray-400 hover:text-cyan-400">
                  SDK下载 →
                </a>
                <a href="#" className="block text-gray-400 hover:text-cyan-400">
                  技术博客 →
                </a>
              </div>
            </div>
          </aside>

          {/* 主内容 */}
          <main className="flex-1 min-w-0">
            {/* 分类标题 */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold">
                {API_CATEGORIES.find(c => c.id === activeCategory)?.name}
              </h2>
              <p className="text-gray-400 mt-1">
                {activeCategory === 'auth' && '用户认证和授权相关接口'}
                {activeCategory === 'users' && '用户信息管理接口'}
                {activeCategory === 'generation' && 'AI视频生成核心接口'}
                {activeCategory === 'tasks' && '任务状态查询接口'}
                {activeCategory === 'videos' && '作品管理接口'}
                {activeCategory === 'payments' && '支付和订单接口'}
              </p>
            </div>

            {/* 端点列表 */}
            <div className="space-y-4">
              {filteredEndpoints.map((endpoint) => (
                <motion.div
                  key={endpoint.path}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
                >
                  {/* 标题栏 */}
                  <button
                    onClick={() => setExpandedEndpoint(
                      expandedEndpoint === endpoint.path ? null : endpoint.path
                    )}
                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <span className={cn(
                        "px-2 py-1 rounded text-xs font-mono",
                        METHOD_COLORS[endpoint.method as keyof typeof METHOD_COLORS]
                      )}>
                        {endpoint.method}
                      </span>
                      <code className="text-sm font-mono text-cyan-400">
                        {endpoint.path}
                      </code>
                      <span className="text-gray-400 text-sm">
                        {endpoint.title}
                      </span>
                    </div>
                    <ChevronRight className={cn(
                      "w-5 h-5 text-gray-400 transition-transform",
                      expandedEndpoint === endpoint.path && "rotate-90"
                    )} />
                  </button>
                  
                  {/* 详细内容 */}
                  <AnimatePresence>
                    {expandedEndpoint === endpoint.path && (
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: 'auto' }}
                        exit={{ height: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="px-4 pb-4 border-t border-white/10">
                          <p className="text-gray-400 py-4">
                            {endpoint.description}
                          </p>
                          
                          {/* 参数 */}
                          {endpoint.params.length > 0 && (
                            <div className="mb-4">
                              <h4 className="text-sm font-medium mb-2">请求参数</h4>
                              <div className="bg-black/30 rounded-lg overflow-hidden">
                                <table className="w-full text-sm">
                                  <thead>
                                    <tr className="border-b border-white/10">
                                      <th className="text-left p-3 text-gray-400 font-medium">参数</th>
                                      <th className="text-left p-3 text-gray-400 font-medium">类型</th>
                                      <th className="text-left p-3 text-gray-400 font-medium">必填</th>
                                      <th className="text-left p-3 text-gray-400 font-medium">描述</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {endpoint.params.map((param) => (
                                      <tr key={param.name} className="border-b border-white/5">
                                        <td className="p-3 font-mono text-cyan-400">{param.name}</td>
                                        <td className="p-3 text-purple-400">{param.type}</td>
                                        <td className="p-3">
                                          {param.required ? (
                                            <span className="text-red-400">是</span>
                                          ) : (
                                            <span className="text-gray-500">否</span>
                                          )}
                                        </td>
                                        <td className="p-3 text-gray-400">{param.description}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                          
                          {/* 示例 */}
                          <div className="space-y-4">
                            {endpoint.example.request && (
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="text-sm font-medium">请求示例</h4>
                                  <button
                                    onClick={() => handleCopy(endpoint.example.request, `req-${endpoint.path}`)}
                                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-white"
                                  >
                                    {copiedCode === `req-${endpoint.path}` ? (
                                      <Check className="w-3 h-3 text-green-400" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                    复制
                                  </button>
                                </div>
                                <pre className="bg-black/50 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                                  {endpoint.example.request}
                                </pre>
                              </div>
                            )}
                            
                            {endpoint.example.response && (
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="text-sm font-medium">响应示例</h4>
                                  <button
                                    onClick={() => handleCopy(endpoint.example.response, `res-${endpoint.path}`)}
                                    className="flex items-center gap-1 text-xs text-gray-400 hover:text-white"
                                  >
                                    {copiedCode === `res-${endpoint.path}` ? (
                                      <Check className="w-3 h-3 text-green-400" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                    复制
                                  </button>
                                </div>
                                <pre className="bg-black/50 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                                  {endpoint.example.response}
                                </pre>
                              </div>
                            )}
                          </div>
                          
                          {/* 调试按钮 */}
                          <div className="mt-4 pt-4 border-t border-white/10">
                            <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors">
                              <Play className="w-4 h-4" />
                              在线调试
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
