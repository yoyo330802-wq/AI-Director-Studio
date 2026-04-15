'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { 
  Search, Grid, List, Play, Copy, Check, 
  Clock, Sparkles, TrendingUp, Star, Filter,
  Plus, Bookmark, BookmarkCheck, X, Eye,
  ChevronDown, Shuffle, Image as ImageIcon
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
  created_at: string
}

interface TemplateDetail {
  id: number
  name: string
  description: string
  category: string
  prompt_template: string
  negative_prompt_template: string | null
  recommended_mode: string | null
  recommended_duration: number | null
  recommended_resolution: string | null
  recommended_aspect_ratio: string | null
  tags: string[]
  usage_count: number
  is_official: boolean
  cover_image: string
  demo_video: string | null
  examples: { prompt: string; cover_url: string }[]
  created_at: string
}

export default function TemplatesPage() {
  const router = useRouter()
  const [category, setCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [favorites, setFavorites] = useState<number[]>([])
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetail | null>(null)

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

  // 获取模板详情
  const { data: detailData } = useQuery({
    queryKey: ['template-detail', selectedTemplate?.id],
    queryFn: () => selectedTemplate ? api.get(`/v1/templates/${selectedTemplate.id}`) : null,
    enabled: !!selectedTemplate,
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

  // 复制完整提示词
  const handleCopyFullPrompt = async (text: string) => {
    await navigator.clipboard.writeText(text)
    toast.success('已复制')
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

  // 使用完整模板（从详情）
  const handleUseFullTemplate = (template: TemplateDetail) => {
    const params = new URLSearchParams({
      prompt: template.prompt_template,
    })
    if (template.recommended_mode) {
      params.append('mode', template.recommended_mode)
    }
    if (template.recommended_duration) {
      params.append('duration', template.recommended_duration.toString())
    }
    if (template.negative_prompt_template) {
      params.append('negative_prompt', template.negative_prompt_template)
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
    toast.success(favorites.includes(templateId) ? '已取消收藏' : '已添加收藏')
  }

  // 打开模板详情
  const handleOpenDetail = (template: Template) => {
    // 直接使用模板数据作为详情（实际应该请求详情API）
    setSelectedTemplate({
      ...template,
      recommended_resolution: '720p',
      recommended_aspect_ratio: '16:9',
      examples: [],
    } as TemplateDetail)
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
                <div 
                  className="aspect-video relative cursor-pointer"
                  onClick={() => handleOpenDetail(template)}
                >
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
                    onClick={(e) => {
                      e.stopPropagation()
                      handleFavorite(template.id)
                    }}
                    className="absolute top-2 right-2 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
                  >
                    {favorites.includes(template.id) ? (
                      <BookmarkCheck className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Bookmark className="w-4 h-4 text-white" />
                    )}
                  </button>
                  
                  {/* 预览按钮 */}
                  {template.demo_video && (
                    <div 
                      className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleOpenDetail(template)
                      }}
                    >
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
                    <button
                      onClick={() => handleOpenDetail(template)}
                      className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                      title="查看详情"
                    >
                      <Eye className="w-4 h-4" />
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
                <div 
                  className="w-40 h-24 relative rounded-lg overflow-hidden flex-shrink-0 cursor-pointer"
                  onClick={() => handleOpenDetail(template)}
                >
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
                        {template.tags?.slice(0, 2).map((tag) => (
                          <span key={tag} className="text-gray-500">#{tag}</span>
                        ))}
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

      {/* 模板详情弹窗 */}
      <AnimatePresence>
        {selectedTemplate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setSelectedTemplate(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#16161d] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 头部 */}
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold">{selectedTemplate.name}</h2>
                  {selectedTemplate.is_official && (
                    <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs">
                      官方模板
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setSelectedTemplate(null)}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {/* 内容 */}
              <div className="flex-1 overflow-y-auto">
                {/* 视频预览 */}
                <div className="aspect-video bg-black relative">
                  {selectedTemplate.demo_video && selectedTemplate.demo_video.length > 0 ? (
                    <video
                      src={selectedTemplate.demo_video}
                      controls
                      className="w-full h-full"
                      autoPlay
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-500">
                      <div className="text-center">
                        <ImageIcon className="w-16 h-16 mx-auto mb-2 text-gray-600" />
                        <p>暂无预览视频</p>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* 详情内容 */}
                <div className="p-6 space-y-6">
                  {/* 描述 */}
                  <div>
                    <h3 className="text-sm text-gray-400 mb-2">模板描述</h3>
                    <p className="text-gray-300">{selectedTemplate.description}</p>
                  </div>
                  
                  {/* 推荐参数 */}
                  <div>
                    <h3 className="text-sm text-gray-400 mb-2">推荐参数</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedTemplate.recommended_mode && (
                        <span className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm">
                          模式: {selectedTemplate.recommended_mode}
                        </span>
                      )}
                      {selectedTemplate.recommended_duration && (
                        <span className="px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-lg text-sm">
                          时长: {selectedTemplate.recommended_duration}秒
                        </span>
                      )}
                      {selectedTemplate.recommended_resolution && (
                        <span className="px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded-lg text-sm">
                          分辨率: {selectedTemplate.recommended_resolution}
                        </span>
                      )}
                      {selectedTemplate.recommended_aspect_ratio && (
                        <span className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm">
                          比例: {selectedTemplate.recommended_aspect_ratio}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* 提示词 */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm text-gray-400">正向提示词</h3>
                      <button
                        onClick={() => handleCopyFullPrompt(selectedTemplate.prompt_template)}
                        className="flex items-center gap-1 px-3 py-1 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                        复制
                      </button>
                    </div>
                    <div className="p-4 bg-black/30 rounded-xl">
                      <p className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                        {selectedTemplate.prompt_template}
                      </p>
                    </div>
                  </div>
                  
                  {/* 反向提示词 */}
                  {selectedTemplate.negative_prompt_template && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm text-gray-400">反向提示词</h3>
                        <button
                          onClick={() => selectedTemplate.negative_prompt_template && handleCopyFullPrompt(selectedTemplate.negative_prompt_template)}
                          className="flex items-center gap-1 px-3 py-1 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
                        >
                          <Copy className="w-4 h-4" />
                          复制
                        </button>
                      </div>
                      <div className="p-4 bg-black/30 rounded-xl">
                        <p className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                          {selectedTemplate.negative_prompt_template}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {/* 标签 */}
                  {selectedTemplate.tags && selectedTemplate.tags.length > 0 && (
                    <div>
                      <h3 className="text-sm text-gray-400 mb-2">标签</h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedTemplate.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-3 py-1 bg-white/5 rounded-full text-sm text-gray-400"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* 统计 */}
                  <div className="flex items-center gap-6 text-sm text-gray-400">
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      {selectedTemplate.usage_count} 次使用
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(selectedTemplate.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* 底部操作 */}
              <div className="p-4 border-t border-white/5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleFavorite(selectedTemplate.id)}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg transition-colors",
                      favorites.includes(selectedTemplate.id)
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-white/10 hover:bg-white/20"
                    )}
                  >
                    {favorites.includes(selectedTemplate.id) ? (
                      <BookmarkCheck className="w-4 h-4" />
                    ) : (
                      <Bookmark className="w-4 h-4" />
                    )}
                    收藏
                  </button>
                </div>
                
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => {
                      handleCopyPrompt(selectedTemplate)
                      setSelectedTemplate(null)
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                    复制提示词
                  </button>
                  <button
                    onClick={() => {
                      handleUseFullTemplate(selectedTemplate)
                      setSelectedTemplate(null)
                    }}
                    className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg font-medium hover:opacity-90 transition-opacity"
                  >
                    <Sparkles className="w-4 h-4" />
                    使用此模板
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}