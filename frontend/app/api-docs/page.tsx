'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, BookOpen, Code, Copy, Check,
  ChevronRight, ChevronDown, Play, Key,
  Terminal, Box, Lock, Zap, RefreshCw,
  AlertCircle, Loader2, Globe, Shield
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

// OpenAPI Schema Types
interface OpenAPISchema {
  openapi: string
  info: {
    title: string
    description?: string
    version: string
  }
  paths: Record<string, PathItem>
  components?: {
    schemas?: Record<string, SchemaObject>
    securitySchemes?: Record<string, any>
  }
}

interface PathItem {
  get?: Operation
  post?: Operation
  put?: Operation
  delete?: Operation
  patch?: Operation
  options?: Operation
  head?: Operation
}

interface Operation {
  summary?: string
  description?: string
  operationId?: string
  tags?: string[]
  parameters?: Parameter[]
  requestBody?: RequestBody
  responses?: Record<string, Response>
  security?: any[]
}

interface Parameter {
  name: string
  in: 'query' | 'path' | 'header' | 'cookie'
  required?: boolean
  description?: string
  schema?: SchemaObject
  example?: any
}

interface RequestBody {
  required?: boolean
  description?: string
  content?: Record<string, MediaType>
}

interface MediaType {
  schema?: SchemaObject
  example?: any
}

interface Response {
  description: string
  content?: Record<string, MediaType>
}

interface SchemaObject {
  type?: string
  properties?: Record<string, SchemaObject>
  items?: SchemaObject
  enum?: any[]
  description?: string
  example?: any
  $ref?: string
  required?: string[]
}

// API分类映射
const TAG_CATEGORIES: Record<string, { name: string; icon: any; color: string }> = {
  auth: { name: '认证', icon: Lock, color: 'from-red-500/20 to-orange-500/20 text-red-400' },
  users: { name: '用户', icon: BookOpen, color: 'from-blue-500/20 to-cyan-500/20 text-blue-400' },
  generate: { name: '视频生成', icon: Zap, color: 'from-yellow-500/20 to-amber-500/20 text-yellow-400' },
  hermes: { name: 'Hermes', icon: Terminal, color: 'from-purple-500/20 to-pink-500/20 text-purple-400' },
  feishu: { name: '飞书', icon: Box, color: 'from-green-500/20 to-emerald-500/20 text-green-400' },
  billing: { name: '计费', icon: Key, color: 'from-cyan-500/20 to-teal-500/20 text-cyan-400' },
  packages: { name: '套餐', icon: Box, color: 'from-indigo-500/20 to-blue-500/20 text-indigo-400' },
  moderation: { name: '审核', icon: Shield, color: 'from-gray-500/20 to-slate-500/20 text-gray-400' },
}

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-green-500/20 text-green-400 border-green-500/30',
  POST: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  PUT: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  DELETE: 'bg-red-500/20 text-red-400 border-red-500/30',
  PATCH: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
}

export default function ApiDocsPage() {
  const [schema, setSchema] = useState<OpenAPISchema | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTag, setActiveTag] = useState<string>('all')
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [testModal, setTestModal] = useState<{ endpoint: string; method: string; operation: Operation } | null>(null)
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)

  // 获取OpenAPI Schema
  const fetchSchema = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      // 尝试从后端获取OpenAPI schema (通过代理)
      const response = await fetch('/openapi.json')
      if (!response.ok) {
        // 如果代理未生效，尝试直接获取
        const directResponse = await fetch('http://localhost:8000/openapi.json')
        if (directResponse.ok) {
          const data = await directResponse.json()
          setSchema(data)
        } else {
          setError('无法连接到后端API服务，请确保后端服务正在运行')
        }
      } else {
        const data = await response.json()
        setSchema(data)
      }
    } catch (err) {
      setError(`加载API文档失败: ${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSchema()
  }, [fetchSchema])

  // 解析端点列表
  const endpoints = schema ? Object.entries(schema.paths).flatMap(([path, methods]) =>
    Object.entries(methods).map(([method, operation]) => ({
      path,
      method: method.toUpperCase(),
      operation,
      tags: operation.tags || ['other'],
    }))
  ) : []

  // 获取所有标签
  const allTags = schema ? ['all', ...new Set(endpoints.flatMap(e => e.tags))] : ['all']

  // 过滤端点
  const filteredEndpoints = endpoints.filter(endpoint => {
    const matchesTag = activeTag === 'all' || endpoint.tags.includes(activeTag)
    const matchesSearch = !searchQuery || 
      endpoint.operation.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.operation.operationId?.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesTag && matchesSearch
  })

  // 生成curl命令
  const generateCurl = (endpoint: string, method: string, operation: Operation): string => {
    const params = operation.parameters || []
    const pathParams = params.filter(p => p.in === 'path')
    const queryParams = params.filter(p => p.in === 'query')
    
    let path = endpoint
    pathParams.forEach(p => {
      path = path.replace(`{${p.name}}`, `\${${p.name}}`)
    })
    
    let curl = `curl -X ${method} '${path}'`
    
    if (queryParams.length > 0) {
      const queryString = queryParams.map(p => `${p.name}=${p.schema?.example || p.example || '{value}'}`).join('&')
      curl += `?${queryString}`
    }
    
    curl += ` \\\n  -H 'Content-Type: application/json'`
    curl += ` \\\n  -H 'Authorization: Bearer YOUR_TOKEN'`
    
    if (operation.requestBody?.content?.['application/json']?.example) {
      curl += ` \\\n  -d '${JSON.stringify(operation.requestBody.content['application/json'].example, null, 2)}'`
    } else if (operation.requestBody?.content?.['application/json']?.schema?.example) {
      curl += ` \\\n  -d '${JSON.stringify(operation.requestBody.content['application/json'].schema.example, null, 2)}'`
    }
    
    return curl
  }

  // 复制代码
  const handleCopy = async (code: string, id: string) => {
    await navigator.clipboard.writeText(code)
    setCopiedCode(id)
    toast.success('已复制到剪贴板')
    setTimeout(() => setCopiedCode(null), 2000)
  }

  // 测试API
  const handleTest = async () => {
    if (!testModal) return
    setTesting(true)
    setTestResult(null)
    
    try {
      const params = testModal.operation.parameters || []
      const queryParams = params.filter(p => p.in === 'query')
      
      let url = testModal.endpoint
      if (queryParams.length > 0) {
        const queryString = queryParams.map(p => `${p.name}=${p.schema?.example || 'value'}`).join('&')
        url += `?${queryString}`
      }
      
      const response = await fetch(url, {
        method: testModal.method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer YOUR_TOKEN'
        }
      })
      
      const data = await response.json()
      setTestResult(JSON.stringify(data, null, 2))
    } catch (err) {
      setTestResult(`错误: ${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      setTesting(false)
    }
  }

  // 解析schema引用
  const resolveSchema = (schema: SchemaObject | undefined): SchemaObject | null => {
    if (!schema) return null
    if (schema.$ref && schema.$ref.startsWith('#/components/schemas/') && schema.components) {
      const refName = schema.$ref.replace('#/components/schemas/', '')
      return schema.components.schemas?.[refName] || null
    }
    return schema
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">正在加载API文档...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">连接失败</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={fetchSchema}
            className="px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            重试
          </button>
        </div>
      </div>
    )
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
                <p className="text-sm text-gray-400">
                  {schema?.info.title || '漫AI'} v{schema?.info.version || '1.0'}
                </p>
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
            
            {/* 操作按钮 */}
            <div className="flex items-center gap-2">
              <button 
                onClick={fetchSchema}
                className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                title="刷新"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <a 
                href="/docs" 
                target="_blank"
                className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
              >
                <Globe className="w-4 h-4" />
                Swagger UI
              </a>
              <button className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors">
                <Key className="w-4 h-4" />
                获取API Key
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* 侧边栏 */}
          <aside className="w-56 flex-shrink-0">
            <nav className="space-y-1">
              {allTags.map((tag) => {
                const tagInfo = TAG_CATEGORIES[tag]
                return (
                  <button
                    key={tag}
                    onClick={() => setActiveTag(tag)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                      activeTag === tag
                        ? tagInfo 
                          ? `bg-gradient-to-r ${tagInfo.color}`
                          : "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400"
                        : "text-gray-400 hover:text-white hover:bg-white/5"
                    )}
                  >
                    {tagInfo ? (
                      <tagInfo.icon className="w-5 h-5" />
                    ) : (
                      <Box className="w-5 h-5" />
                    )}
                    {tag === 'all' ? '全部' : (tagInfo?.name || tag)}
                  </button>
                )
              })}
            </nav>
            
            {/* 快速链接 */}
            <div className="mt-8 p-4 bg-white/5 rounded-xl">
              <h4 className="text-sm font-medium mb-3">开发者资源</h4>
              <div className="space-y-2 text-sm">
                <a href="/sdk-docs" className="block text-gray-400 hover:text-cyan-400">
                  SDK文档 →
                </a>
                <a href="/docs" target="_blank" className="block text-gray-400 hover:text-cyan-400">
                  Swagger UI →
                </a>
                <a href="#" className="block text-gray-400 hover:text-cyan-400">
                  开发者指南 →
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
                {activeTag === 'all' ? '全部API' : (TAG_CATEGORIES[activeTag]?.name || activeTag)}
              </h2>
              <p className="text-gray-400 mt-1">
                共 {filteredEndpoints.length} 个端点
                {schema?.info.description && ` - ${schema.info.description.split('.')[0]}`}
              </p>
            </div>

            {/* 端点列表 */}
            <div className="space-y-4">
              {filteredEndpoints.map((endpoint) => {
                const endpointId = `${endpoint.method}-${endpoint.path}`
                const operation = endpoint.operation
                
                return (
                  <motion.div
                    key={endpointId}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white/5 rounded-xl border border-white/10 overflow-hidden"
                  >
                    {/* 标题栏 */}
                    <button
                      onClick={() => setExpandedEndpoint(expandedEndpoint === endpointId ? null : endpointId)}
                      className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <span className={cn(
                          "px-2 py-1 rounded text-xs font-mono border",
                          METHOD_COLORS[endpoint.method]
                        )}>
                          {endpoint.method}
                        </span>
                        <code className="text-sm font-mono text-cyan-400">
                          {endpoint.path}
                        </code>
                        <span className="text-gray-400 text-sm">
                          {operation.summary || operation.operationId || '未命名端点'}
                        </span>
                      </div>
                      <ChevronRight className={cn(
                        "w-5 h-5 text-gray-400 transition-transform",
                        expandedEndpoint === endpointId && "rotate-90"
                      )} />
                    </button>
                    
                    {/* 详细内容 */}
                    <AnimatePresence>
                      {expandedEndpoint === endpointId && (
                        <motion.div
                          initial={{ height: 0 }}
                          animate={{ height: 'auto' }}
                          exit={{ height: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="px-4 pb-4 border-t border-white/10">
                            {/* 描述 */}
                            {(operation.description || operation.summary) && (
                              <p className="text-gray-400 py-4">
                                {operation.description || operation.summary}
                              </p>
                            )}
                            
                            {/* 参数 */}
                            {operation.parameters && operation.parameters.length > 0 && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium mb-2">请求参数</h4>
                                <div className="bg-black/30 rounded-lg overflow-hidden">
                                  <table className="w-full text-sm">
                                    <thead>
                                      <tr className="border-b border-white/10">
                                        <th className="text-left p-3 text-gray-400 font-medium">参数</th>
                                        <th className="text-left p-3 text-gray-400 font-medium">位置</th>
                                        <th className="text-left p-3 text-gray-400 font-medium">类型</th>
                                        <th className="text-left p-3 text-gray-400 font-medium">必填</th>
                                        <th className="text-left p-3 text-gray-400 font-medium">描述</th>
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {operation.parameters.map((param) => (
                                        <tr key={param.name} className="border-b border-white/5">
                                          <td className="p-3 font-mono text-cyan-400">{param.name}</td>
                                          <td className="p-3 text-purple-400">{param.in}</td>
                                          <td className="p-3 text-orange-400">{param.schema?.type || 'string'}</td>
                                          <td className="p-3">
                                            {param.required ? (
                                              <span className="text-red-400">是</span>
                                            ) : (
                                              <span className="text-gray-500">否</span>
                                            )}
                                          </td>
                                          <td className="p-3 text-gray-400">{param.description || '-'}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                            
                            {/* 请求体 */}
                            {operation.requestBody && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium mb-2">
                                  请求体 {operation.requestBody.required && <span className="text-red-400">*</span>}
                                </h4>
                                <div className="bg-black/30 rounded-lg p-4">
                                  {operation.requestBody.description && (
                                    <p className="text-gray-400 mb-2">{operation.requestBody.description}</p>
                                  )}
                                  {operation.requestBody.content?.['application/json']?.schema && (
                                    <div className="mt-2">
                                      <div className="text-xs text-gray-500 mb-1">Schema:</div>
                                      <pre className="text-xs text-purple-400 overflow-x-auto">
                                        {JSON.stringify(operation.requestBody.content['application/json'].schema, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {/* 响应 */}
                            {operation.responses && (
                              <div className="mb-4">
                                <h4 className="text-sm font-medium mb-2">响应</h4>
                                <div className="space-y-2">
                                  {Object.entries(operation.responses).map(([code, response]) => (
                                    <div key={code} className="bg-black/30 rounded-lg p-4">
                                      <div className="flex items-center gap-2 mb-2">
                                        <span className={cn(
                                          "px-2 py-0.5 rounded text-xs font-mono",
                                          code.startsWith('2') ? 'bg-green-500/20 text-green-400' :
                                          code.startsWith('4') ? 'bg-amber-500/20 text-amber-400' :
                                          'bg-red-500/20 text-red-400'
                                        )}>
                                          {code}
                                        </span>
                                        <span className="text-sm text-gray-400">{response.description}</span>
                                      </div>
                                      {response.content?.['application/json']?.schema && (
                                        <pre className="text-xs text-purple-400 overflow-x-auto mt-2">
                                          {JSON.stringify(response.content['application/json'].schema, null, 2)}
                                        </pre>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* curl示例 */}
                            <div className="mb-4">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-medium">curl 示例</h4>
                                <button
                                  onClick={() => handleCopy(generateCurl(endpoint.path, endpoint.method, operation), `curl-${endpointId}`)}
                                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-white"
                                >
                                  {copiedCode === `curl-${endpointId}` ? (
                                    <Check className="w-3 h-3 text-green-400" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                  复制
                                </button>
                              </div>
                              <pre className="bg-black/50 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                                {generateCurl(endpoint.path, endpoint.method, operation)}
                              </pre>
                            </div>
                            
                            {/* 操作按钮 */}
                            <div className="mt-4 pt-4 border-t border-white/10 flex gap-2">
                              <button 
                                onClick={() => setTestModal({ endpoint: endpoint.path, method: endpoint.method, operation })}
                                className="flex items-center gap-2 px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors"
                              >
                                <Play className="w-4 h-4" />
                                在线调试
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )
              })}
            </div>

            {filteredEndpoints.length === 0 && (
              <div className="text-center py-12">
                <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">未找到匹配的API端点</p>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* 测试弹窗 */}
      <AnimatePresence>
        {testModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setTestModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#1a1a2e] rounded-2xl border border-white/10 w-full max-w-2xl max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-white/10">
                <h3 className="text-lg font-bold">在线调试</h3>
                <p className="text-sm text-gray-400 mt-1">
                  <span className={cn(
                    "px-2 py-0.5 rounded text-xs font-mono",
                    METHOD_COLORS[testModal.method]
                  )}>
                    {testModal.method}
                  </span>
                  {' '}
                  <code className="text-cyan-400">{testModal.endpoint}</code>
                </p>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                {testResult ? (
                  <div>
                    <h4 className="text-sm font-medium mb-2">响应结果</h4>
                    <pre className="bg-black/50 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                      {testResult}
                    </pre>
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-8">
                    点击「发送测试」发起请求
                  </p>
                )}
              </div>
              
              <div className="p-6 border-t border-white/10 flex justify-end gap-3">
                <button
                  onClick={() => setTestModal(null)}
                  className="px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
                >
                  关闭
                </button>
                <button
                  onClick={handleTest}
                  disabled={testing}
                  className="px-4 py-2 bg-cyan-500 rounded-lg text-sm hover:bg-cyan-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {testing && <Loader2 className="w-4 h-4 animate-spin" />}
                  发送测试
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
