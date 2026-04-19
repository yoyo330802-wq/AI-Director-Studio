'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useStore } from '@/lib/store'
import api from '@/lib/api'
import { cn, formatCurrency } from '@/lib/utils'
import { 
  Zap, Sparkles, Crown, 
  Upload, Image as ImageIcon, 
  Play, Clock, DollarSign,
  X, Check, AlertCircle
} from 'lucide-react'

// 生成模式配置
const MODES = {
  fast: {
    id: 'fast' as const,
    label: '闪电模式',
    icon: Zap,
    model: 'Wan2.1-1.3B',
    speed: '~15秒出片',
    price: 0.04,
    description: '快速验证创意，适合草稿',
    color: 'from-yellow-400 to-orange-500',
    borderColor: 'border-yellow-400',
  },
  balanced: {
    id: 'balanced' as const,
    label: '智能模式',
    icon: Sparkles,
    model: '智能路由',
    speed: '~30秒出片',
    price: 0.06,
    description: '成本与质量平衡，推荐',
    color: 'from-blue-400 to-purple-500',
    borderColor: 'border-blue-400',
  },
  premium: {
    id: 'premium' as const,
    label: '专业模式',
    icon: Crown,
    model: 'Vidu/可灵',
    speed: '~60秒出片',
    price: 0.09,
    description: '商用级质量，精益求精',
    color: 'from-purple-500 to-pink-500',
    borderColor: 'border-purple-400',
  },
} as const

type ModeId = keyof typeof MODES

export default function StudioPage() {
  const [mode, setMode] = useState<ModeId>('balanced')
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [duration, setDuration] = useState<5 | 10>(5)
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '1:1'>('16:9')
  const [referenceImage, setReferenceImage] = useState<File | null>(null)
  const [referencePreview, setReferencePreview] = useState<string>('')
  const [estimatedCost, setEstimatedCost] = useState(0)
  
  const { 
    user, 
    isAuthenticated, 
    setUser, 
    setToken, 
    currentTask, 
    setCurrentTask,
    isGenerating,
    setIsGenerating 
  } = useStore()

  // 计算预估成本
  useEffect(() => {
    const price = MODES[mode].price
    setEstimatedCost(price * duration)
  }, [mode, duration])

  // 获取用户信息
  const { data: userData, refetch: refetchUser } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      try {
        return await api.getCurrentUser()
      } catch {
        return null
      }
    },
    enabled: isAuthenticated,
  })

  useEffect(() => {
    if (userData) {
      setUser(userData)
    }
  }, [userData, setUser])

  // 路由预览
  const { data: routePreview } = useQuery({
    queryKey: ['routePreview', mode, duration],
    queryFn: () => api.previewRoute(mode, duration),
    enabled: !!isAuthenticated,
  })

  // 生成任务
  const generateMutation = useMutation({
    mutationFn: async () => {
      // mode 映射到后端 quality_mode 字段
      const qualityModeMap: Record<ModeId, string> = {
        fast: 'cost',
        balanced: 'balanced',
        premium: 'quality',
      }

      return api.createTask({
        mode: qualityModeMap[mode],
        prompt,
        negative_prompt: negativePrompt,
        duration,
        aspect_ratio: aspectRatio,
      })
    },
    onSuccess: (data) => {
      toast.success('任务已提交！')
      setCurrentTask(data)
      setIsGenerating(true)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '生成失败')
      setIsGenerating(false)
    },
  })

  // 处理图片上传
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setReferenceImage(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setReferencePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  // 清除参考图
  const clearReferenceImage = () => {
    setReferenceImage(null)
    setReferencePreview('')
  }

  // 提交生成
  const handleSubmit = () => {
    if (!prompt.trim()) {
      toast.error('请输入提示词')
      return
    }
    
    if (!isAuthenticated) {
      toast.error('请先登录')
      return
    }
    
    if (user && user.token_balance < estimatedCost) {
      toast.error('余额不足，请充值')
      return
    }
    
    generateMutation.mutate()
  }

  // 模拟进度更新
  useEffect(() => {
    if (!currentTask || currentTask.status !== 'pending') return
    
    const interval = setInterval(() => {
      // 模拟进度更新
      setCurrentTask({
        ...currentTask,
        status: 'processing',
        progress: Math.min((currentTask.progress || 0) + 10, 90),
      })
    }, 2000)
    
    return () => clearInterval(interval)
  }, [currentTask, setCurrentTask])

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%)' }}>
      {/* 装饰性渐变光晕 - 左上粉色 */}
      <div className="absolute top-0 left-0 w-96 h-96 rounded-full opacity-40 blur-3xl" style={{ background: 'radial-gradient(circle, #ec4899 0%, transparent 70%)', transform: 'translate(-30%, -30%)' }} />
      {/* 装饰性渐变光晕 - 右下紫色 */}
      <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full opacity-30 blur-3xl" style={{ background: 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)', transform: 'translate(30%, 30%)' }} />
      {/* 装饰性渐变光晕 - 中间青色 */}
      <div className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full opacity-20 blur-3xl" style={{ background: 'radial-gradient(circle, #06b6d4 0%, transparent 70%)', transform: 'translate(-50%, -50%)' }} />
      
      {/* 顶部导航 - 深色毛玻璃风格 */}
      <header className="sticky top-0 z-50 backdrop-blur-xl border-b" style={{ background: 'rgba(26, 10, 46, 0.7)', borderColor: 'rgba(139, 92, 246, 0.3)' }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">
              <span className="bg-clip-text text-transparent" style={{ backgroundImage: 'linear-gradient(135deg, #ec4899, #8b5cf6)' }}>
                ✨ 漫AI创作工作室
              </span>
            </h1>
            <p className="text-sm" style={{ color: '#a78bfa' }}>AI驱动，创意无限</p>
          </div>
          
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <div className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/80 backdrop-blur border border-pink-100 shadow-sm">
                  <span className="text-sm" style={{ color: '#a78bfa' }}>账户余额</span>
                  <span className="text-xl font-bold" style={{ color: '#ec4899' }}>
                    {user?.token_balance?.toFixed(2) || '0.00'}
                  </span>
                </div>
                <button className="px-4 py-2 text-sm rounded-xl hover:bg-white/50 transition-all" style={{ color: '#7c3aed' }}>
                  个人中心
                </button>
              </>
            ) : (
              <button 
                onClick={() => {/* 登录 */}}
                className="px-6 py-2 text-white font-medium rounded-2xl shadow-lg hover:shadow-xl transition-all"
                style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)' }}
              >
                登录 / 注册
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 relative z-10">
        {/* 模式选择 */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4" style={{ color: '#e9d5ff' }}>🎯 选择生成模式</h2>
          <div className="grid grid-cols-3 gap-6">
            {(Object.keys(MODES) as ModeId[]).map((modeId) => {
              const m = MODES[modeId]
              const Icon = m.icon
              return (
                <motion.button
                  key={modeId}
                  onClick={() => setMode(modeId)}
                  whileHover={{ scale: 1.02, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  className={cn(
                    'relative p-6 rounded-2xl transition-all backdrop-blur',
                    mode === modeId 
                      ? `${m.borderColor} shadow-xl` 
                      : 'border border-white/10 bg-white/5 hover:bg-white/10'
                  )}
                  style={{ 
                    background: mode === modeId ? 'rgba(139, 92, 246, 0.3)' : 'rgba(255,255,255,0.05)',
                    boxShadow: mode === modeId ? '0 20px 40px -12px rgba(139, 92, 246, 0.4)' : 'none',
                    borderColor: mode === modeId ? m.borderColor.replace('border-', '') : 'rgba(255,255,255,0.1)'
                  }}
                >
                  {mode === modeId && (
                    <motion.div
                      layoutId="mode-indicator"
                      className={cn(
                        'absolute -top-3 -right-3 w-8 h-8 rounded-full flex items-center justify-center text-white shadow-lg',
                        `bg-gradient-to-br ${m.color}`
                      )}
                    >
                      <Check className="w-5 h-5" />
                    </motion.div>
                  )}
                  
                  <div className={cn(
                    'inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4 shadow-lg',
                    `bg-gradient-to-br ${m.color}`
                  )}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  
                  <h3 className="text-lg font-bold mb-1 text-white">{m.label}</h3>
                  <p className="text-sm mb-2" style={{ color: '#c4b5fd' }}>{m.model}</p>
                  <p className="text-xs mb-3" style={{ color: '#94a3b8' }}>{m.description}</p>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm" style={{ color: '#a78bfa' }}>{m.speed}</span>
                    <span style={{ color: mode === modeId ? '#f472b6' : '#a78bfa' }} className="font-bold">
                      ¥{m.price}/秒
                    </span>
                  </div>
                </motion.button>
              )
            })}
          </div>
        </section>

        {/* 主创作区 */}
        <div className="grid grid-cols-3 gap-8">
          {/* 左侧：输入区 */}
          <div className="col-span-2 space-y-6">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-3xl p-8 border"
              style={{ background: 'rgba(30, 20, 60, 0.8)', borderColor: 'rgba(139, 92, 246, 0.3)' }}
            >
              {/* 提示词输入 */}
              <div className="mb-6">
                <label className="block text-sm font-semibold mb-2 text-white">
                  ✍️ 描述你的场景
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="例如：一位银发少女在樱花树下跳舞，镜头缓慢旋转，花瓣飘落，夕阳温暖的光线，动漫风格"
                  className="w-full h-32 p-4 rounded-2xl border-2 transition-all resize-none focus:outline-none"
                  style={{ 
                    borderColor: 'rgba(139, 92, 246, 0.5)',
                    background: 'rgba(15, 10, 40, 0.8)',
                    color: '#e9d5ff',
                  }}
                  maxLength={500}
                />
                <div className="flex justify-between mt-2 text-sm">
                  <span style={{ color: '#a78bfa' }}>💡 详细描述获得更好效果</span>
                  <span style={{ color: '#7c3aed' }}>{prompt.length}/500</span>
                </div>
              </div>

              {/* 负向提示词 */}
              <div className="mb-6">
                <label className="block text-sm font-semibold mb-2 text-white">
                  🚫 不想要的内容（可选）
                </label>
                <input
                  type="text"
                  value={negativePrompt}
                  onChange={(e) => setNegativePrompt(e.target.value)}
                  placeholder="低质量, 模糊, 变形, 文字, 水印"
                  className="w-full px-4 py-3 rounded-2xl border-2 transition-all focus:outline-none"
                  style={{ 
                    borderColor: 'rgba(139, 92, 246, 0.5)',
                    background: 'rgba(15, 10, 40, 0.8)',
                    color: '#e9d5ff',
                  }}
                />
              </div>

              {/* 参数设置 */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                {/* 时长 */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-white">
                    ⏱️ 视频时长
                  </label>
                  <div className="flex gap-3">
                    {([5, 10] as const).map((d) => (
                      <button
                        key={d}
                        onClick={() => setDuration(d)}
                        className={cn(
                          'flex-1 py-3 px-4 rounded-2xl font-semibold transition-all',
                        )}
                        style={duration === d
                          ? { background: 'linear-gradient(135deg, #ec4899, #8b5cf6)', color: 'white', boxShadow: '0 4px 20px rgba(236, 72, 153, 0.4)' }
                          : { background: 'rgba(255,255,255,0.05)', border: '2px solid rgba(139, 92, 246, 0.3)', color: '#c4b5fd' }
                        }
                      >
                        {d}秒
                      </button>
                    ))}
                  </div>
                </div>

                {/* 宽高比 */}
                <div>
                  <label className="block text-sm font-semibold mb-2 text-white">
                    📐 宽高比
                  </label>
                  <div className="flex gap-3">
                    {([
                      { value: '16:9', label: '横屏', icon: '📺' },
                      { value: '9:16', label: '竖屏', icon: '📱' },
                      { value: '1:1', label: '方形', icon: '⬜' },
                    ] as const).map((ratio) => (
                      <button
                        key={ratio.value}
                        onClick={() => setAspectRatio(ratio.value)}
                        className={cn(
                          'flex-1 py-2 px-2 rounded-2xl font-semibold transition-all text-sm',
                        )}
                        style={aspectRatio === ratio.value
                          ? { background: 'linear-gradient(135deg, #ec4899, #8b5cf6)', color: 'white', boxShadow: '0 4px 20px rgba(236, 72, 153, 0.4)' }
                          : { background: 'rgba(255,255,255,0.05)', border: '2px solid rgba(139, 92, 246, 0.3)', color: '#c4b5fd' }
                        }
                      >
                        <div>{ratio.icon}</div>
                        <div>{ratio.label}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 参考图上传 */}
              <div className="mb-6">
                <label className="block text-sm font-semibold mb-2 text-white">
                  🖼️ 参考图片（可选）
                </label>
                {referencePreview ? (
                  <div className="relative rounded-2xl overflow-hidden border-2" style={{ borderColor: 'rgba(139, 92, 246, 0.5)' }}>
                    <img
                      src={referencePreview}
                      alt="参考图"
                      className="w-full h-48 object-cover"
                    />
                    <button
                      onClick={clearReferenceImage}
                      className="absolute top-2 right-2 p-2 text-white rounded-full shadow-lg transition-transform hover:scale-110"
                      style={{ background: 'linear-gradient(135deg, #ec4899, #8b5cf6)' }}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <label className="block border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer hover:bg-purple-900/20"
                    style={{ borderColor: 'rgba(139, 92, 246, 0.5)', background: 'rgba(15, 10, 40, 0.5)' }}>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />
                    <ImageIcon className="w-10 h-10 mx-auto mb-2" style={{ color: '#7c3aed' }} />
                    <p style={{ color: '#c4b5fd' }}>点击上传参考图片</p>
                    <p className="text-sm mt-1" style={{ color: '#7c3aed' }}>支持 JPG, PNG, WebP</p>
                  </label>
                )}
              </div>

              {/* 生成按钮 */}
              <motion.button
                onClick={handleSubmit}
                disabled={!prompt.trim() || isGenerating || generateMutation.isPending}
                whileHover={{ scale: 1.01, y: -2 }}
                whileTap={{ scale: 0.99 }}
                className={cn(
                  'w-full py-4 rounded-2xl font-bold text-lg text-white shadow-xl hover:shadow-2xl transition-all flex items-center justify-center gap-2',
                  `bg-gradient-to-r ${MODES[mode].color}`,
                  (!prompt.trim() || isGenerating) && 'opacity-50 cursor-not-allowed'
                )}
              >
                {isGenerating || generateMutation.isPending ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                    />
                    生成中...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    立即生成（预计 ¥{estimatedCost.toFixed(2)}）
                  </>
                )}
              </motion.button>

              {/* 预估信息 */}
              {routePreview && (
                <div className="mt-4 p-4 rounded-2xl" style={{ background: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                  <div className="flex justify-between text-sm mb-2">
                    <span style={{ color: '#a78bfa' }}>路由策略：</span>
                    <span className="font-semibold text-white">{routePreview.channel_name}</span>
                  </div>
                  <div className="flex justify-between text-sm mb-2">
                    <span style={{ color: '#a78bfa' }}>预计等待：</span>
                    <span className="font-semibold text-white">~{routePreview.estimated_time}秒</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: '#a78bfa' }}>质量评分：</span>
                    <span className="font-semibold text-white">{routePreview.quality_score}/10</span>
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* 右侧：状态与历史 */}
          <div className="space-y-6">
            {/* 当前任务状态 */}
            <AnimatePresence>
              {currentTask && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="rounded-3xl p-6 border"
                  style={{ background: 'rgba(30, 20, 60, 0.8)', borderColor: 'rgba(139, 92, 246, 0.3)' }}
                >
                  <h3 className="font-bold mb-4 flex items-center gap-2 text-white">
                    <Clock className="w-5 h-5" style={{ color: '#ec4899' }} />
                    当前任务
                  </h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm" style={{ color: '#a78bfa' }}>任务ID</span>
                      <span className="text-xs font-mono px-2 py-1 rounded-xl" style={{ background: 'rgba(139, 92, 246, 0.3)', color: '#c4b5fd' }}>
                        {currentTask.task_id.slice(0, 8)}...
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm" style={{ color: '#a78bfa' }}>状态</span>
                      <span className={cn(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        currentTask.status === 'completed' && 'text-white',
                        currentTask.status === 'processing' && 'text-white',
                        currentTask.status === 'pending' && 'text-white',
                        currentTask.status === 'failed' && 'text-white',
                      )} style={
                        currentTask.status === 'completed' ? { background: 'linear-gradient(135deg, #10b981, #059669)' } :
                        currentTask.status === 'processing' ? { background: 'linear-gradient(135deg, #3b82f6, #2563eb)' } :
                        currentTask.status === 'pending' ? { background: 'linear-gradient(135deg, #f59e0b, #d97706)' } :
                        { background: 'linear-gradient(135deg, #ef4444, #dc2626)' }
                      }>
                        {currentTask.status === 'completed' && '已完成'}
                        {currentTask.status === 'processing' && '处理中'}
                        {currentTask.status === 'pending' && '等待中'}
                        {currentTask.status === 'failed' && '失败'}
                      </span>
                    </div>
                    
                    {currentTask.status === 'processing' && (
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span style={{ color: '#a78bfa' }}>进度</span>
                          <span className="font-medium text-white">{currentTask.progress || 0}%</span>
                        </div>
                        <div className="w-full rounded-full h-2" style={{ background: 'rgba(139, 92, 246, 0.2)' }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${currentTask.progress || 0}%` }}
                            className="h-2 rounded-full"
                            style={{ background: 'linear-gradient(90deg, #ec4899, #8b5cf6)' }}
                          />
                        </div>
                      </div>
                    )}

                    {currentTask.status === 'completed' && currentTask.video_url && (
                      <div className="mt-4">
                        <video
                          src={currentTask.video_url}
                          controls
                          className="w-full rounded-2xl shadow-lg"
                        />
                      </div>
                    )}

                    {currentTask.status === 'failed' && currentTask.error && (
                      <div className="p-3 rounded-2xl border" style={{ background: 'rgba(239, 68, 68, 0.2)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                        <p className="text-sm" style={{ color: '#fca5a5' }}>{currentTask.error}</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 快捷模板 */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="rounded-3xl p-6 border"
              style={{ background: 'rgba(30, 20, 60, 0.8)', borderColor: 'rgba(139, 92, 246, 0.3)' }}
            >
              <h3 className="font-bold mb-4 text-white">💡 灵感模板</h3>

              <div className="space-y-3">
                {[
                  {
                    category: '古风国漫',
                    items: [
                      '一位白衣剑客在竹林中挥剑，竹叶飘落，水墨画风格',
                      '仙女在云海中起舞，飘逸长裙，仙气缭绕',
                    ]
                  },
                  {
                    category: '赛博朋克',
                    items: [
                      '霓虹灯闪烁的未来都市，飞车穿梭，下着紫色的雨',
                      '机械女孩站在摩天大楼顶端俯瞰城市',
                    ]
                  },
                  {
                    category: '日常治愈',
                    items: [
                      '一只橘猫在阳光下打盹，慵懒地伸懒腰',
                      '雨后的街道，积水倒映着彩虹',
                    ]
                  },
                ].map((template) => (
                  <div key={template.category} className="mb-4">
                    <h4 className="text-sm font-medium mb-2" style={{ color: '#a78bfa' }}>
                      {template.category}
                    </h4>
                    <div className="space-y-2">
                      {template.items.map((item, idx) => (
                        <button
                          key={idx}
                          onClick={() => setPrompt(item)}
                          className="w-full text-left px-3 py-2 text-sm rounded-xl transition-all hover:shadow-md"
                          style={{ background: 'rgba(139, 92, 246, 0.2)', color: '#e9d5ff', border: '1px solid rgba(139, 92, 246, 0.3)' }}
                        >
                          {item.length > 30 ? `${item.slice(0, 30)}...` : item}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  )
}
