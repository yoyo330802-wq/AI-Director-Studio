'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { 
  Search, Grid, List, Play, Copy, Check, 
  Clock, Sparkles, TrendingUp, Star, Filter,
  Plus, Bookmark, BookmarkCheck
} from 'lucide-react'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

// 分类
const CATEGORIES = [
  { id: 'all', name: '全部' },
  { id: 'anime', name: '动漫风格' },
  { id: '3d', name: '3D渲染' },
  { id: 'realistic', name: '写实' },
  { id: 'abstract', name: '抽象艺术' },
  { id: 'music', name: '音乐视频' },
  { id: 'commercial', name: '商业广告' },
]

interface Template {
  id: number
  name: string
  description: string
  category: string
  prompt_template: string
  negative_prompt_template: string | null
  recommended_mode: string | null
  recommended_duration: number | null
  tags: string[]
  usage_count: number
  is_official: boolean
  cover_image: string
  demo_video: string | null
}

export default function TemplatesPage() {
  const router = useRouter()
  const [category, setCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [favorites, setFavorites] = useState<number[]>([])
  const [copiedId, setCopiedId] = useState<number | null>(null)

  // 获取模板列表
  const { data, isLoading } = useQuery({
    queryKey: ['templates', category],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (category !== 'all') {
        params.append('category', category)
      }
      return api.get(`/v1/templates?${params}`)
    },
  })

  const templates: Template[] = data?.items || []

  // 过滤搜索
  const filteredTemplates = templates.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  // 复制提示词
  const handleCopyPrompt = async (template: Template) => {
    await navigator.clipboard.writeText(template.prompt_template)
    setCopiedId(template.id)
    toast.success('提示词已复制到剪贴板')
    setTimeout(() => setCopiedId(null), 2000)
  }

  // 使用模板创建
  const handleUseTemplate = (template: Template) => {
    const params = new URLSearchParams({
      prompt: template.prompt_template,
    })
    if (template.recommended_mode) {
      params.append('mode', template.recommended_mode)
    }
    if (template.recommended_duration) {
      params.append('duration', template.recommended_duration.toString())
    }
    router.push(`/studio?${params}`)
  }

  // 收藏模板
  const handleFavorite = (templateId: number) => {
    setFavorites(prev => 
      prev.includes(templateId) 
        ? prev.filter(id => id !== templateId)
        : [...prev, templateId]
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* 头部 */}
      <div className="sticky top-0 z-40 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                提示词模板
              </h1>
              <p className="text-sm text-gray-400">使用精选模板快速创作</p>
            </div>

            {/* 搜索框 */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索模板..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-cyan-400/50 transition-colors"
                />
              </div>
            </div>

            {/* 视图切换 */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  viewMode === 'grid' 
                    ? "bg-cyan-400/20 text-cyan-400" 
                    : "text-gray-400 hover:text-white"
                )}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  viewMode === 'list' 
                    ? "bg-cyan-400/20 text-cyan-400" 
                    : "text-gray-400 hover:text-white"
                )}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 分类 */}
          <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={cn(
                  "px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap",
                  category === cat.id
                    ? "bg-gradient-to-r from-cyan-500 to-purple-500 text-white shadow-lg shadow-cyan-500/25"
                    : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
                )}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 内容 */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* 模板列表 */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-white/5 rounded-xl animate-pulse"
                style={{ height: 320 }}
              />
            ))}
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-20">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-gray-600" />
            <h3 className="text-lg font-medium text-gray-400 mb-2">
              暂无模板
            </h3>
            <p className="text-sm text-gray-500">
              {searchQuery ? '试试其他搜索词' : '敬请期待更多模板'}
            </p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template, index) => (
              <motion.div
                key={template.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="group bg-white/5 rounded-xl overflow-hidden hover:bg-white/10 transition-colors"
              >
                {/* 封面 */}
                <div className="aspect-video relative overflow-hidden">
                  <img
                    src={template.cover_image || '/images/template-default.jpg'}
                    alt={template.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  
                  {/* 官方标签 */}
                  {template.is_official && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full text-xs font-medium flex items-center gap-1">
                      <Star className="w-3 h-3" />
                      官方
                    </div>
                  )}
                  
                  {/* 收藏按钮 */}
                  <button
                    onClick={() => handleFavorite(template.id)}
                    className="absolute top-2 right-2 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
                  >
                    {favorites.includes(template.id) ? (
                      <BookmarkCheck className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Bookmark className="w-4 h-4 text-white" />
                    )}
                  </button>
                  
                  {/* 播放按钮 */}
                  {template.demo_video && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <Play className="w-6 h-6 text-white ml-1" />
                      </div>
                    </div>
                  )}
                </div>
                
                {/* 信息 */}
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-semibold line-clamp-1">{template.name}</h3>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      {template.usage_count}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                    {template.description}
                  </p>
                  
                  {/* 标签 */}
                  {template.tags && template.tags.length > 0 && (
                    <div className="flex items-center gap-1 flex-wrap mb-3">
                      {template.tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-white/5 rounded text-xs text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  {/* 推荐参数 */}
                  {template.recommended_mode && (
                    <div className="flex items-center gap-2 mb-3 text-xs text-gray-500">
                      <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded">
                        {template.recommended_mode}
                      </span>
                      {template.recommended_duration && (
                        <span>{template.recommended_duration}秒</span>
                      )}
                    </div>
                  )}
                  
                  {/* 操作 */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleUseTemplate(template)}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                    >
                      <Sparkles className="w-4 h-4" />
                      使用模板
                    </button>
                    <button
                      onClick={() => handleCopyPrompt(template)}
                      className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                      title="复制提示词"
                    >
                      {copiedId === template.id ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTemplates.map((template, index) => (
              <motion.div
                key={template.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors"
              >
                {/* 封面 */}
                <div className="w-40 h-24 relative rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={template.cover_image || '/images/template-default.jpg'}
                    alt={template.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                
                {/* 信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{template.name}</h3>
                        {template.is_official && (
                          <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs">
                            官方
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-400 line-clamp-2 mb-2">
                        {template.description}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {template.usage_count}次使用
                        </span>
                        {template.recommended_mode && (
                          <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded">
                            {template.recommended_mode}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* 操作 */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleFavorite(template.id)}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        {favorites.includes(template.id) ? (
                          <BookmarkCheck className="w-4 h-4 text-amber-400" />
                        ) : (
                          <Bookmark className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleCopyPrompt(template)}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        {copiedId === template.id ? (
                          <Check className="w-4 h-4 text-green-400" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                      <button
                        onClick={() => handleUseTemplate(template)}
                        className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium"
                      >
                        使用
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
