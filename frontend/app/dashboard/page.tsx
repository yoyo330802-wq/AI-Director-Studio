'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  User, Video, CreditCard, Settings, Bell, Shield,
  Key, LogOut, ChevronRight, Copy, Check, 
  Zap, Clock, Play, Download, Trash2, Edit,
  Wallet, Crown, Star, Gift, TrendingUp, Search,
  MoreVertical, Eye, Pause, PlayCircle, X, Filter
} from 'lucide-react'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { cn, formatCurrency } from '@/lib/utils'

// 侧边栏菜单
const MENU_ITEMS = [
  { id: 'overview', name: '概览', icon: User },
  { id: 'videos', name: '我的作品', icon: Video },
  { id: 'orders', name: '订单记录', icon: CreditCard },
  { id: 'wallet', name: '钱包', icon: Wallet },
  { id: 'subscription', name: '会员', icon: Crown },
  { id: 'settings', name: '设置', icon: Settings },
]

interface UserData {
  id: number
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  level: string
  balance: number
  video_quota: number
  video_used: number
  is_vip: boolean
  vip_expires_at: string | null
  created_at: string
}

interface Task {
  task_id: string
  task_no: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  prompt: string
  cover_url: string | null
  video_url: string | null
  created_at: string
  completed_at: string | null
}

interface Order {
  id: number
  order_no: string
  type: string
  amount: number
  actual_amount: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  created_at: string
  paid_at: string | null
}

interface VideoItem {
  id: number
  title: string
  description: string
  video_url: string
  cover_url: string
  thumbnail_url: string
  duration: number
  view_count: number
  like_count: number
  status: 'processing' | 'completed' | 'failed'
  created_at: string
  task_id: string
}

export default function DashboardPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [activeMenu, setActiveMenu] = useState('overview')

  // 获取用户信息
  const { data: userData, isLoading } = useQuery<UserData>({
    queryKey: ['current-user'],
    queryFn: () => api.get('/v1/users/me'),
  })

  const user = userData

  const menuComponents: Record<string, React.ReactNode> = {
    overview: <OverviewSection user={user} />,
    videos: <VideosSection />,
    orders: <OrdersSection />,
    wallet: <WalletSection user={user} />,
    subscription: <SubscriptionSection user={user} />,
    settings: <SettingsSection />,
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* 侧边栏 */}
          <aside className="w-56 flex-shrink-0">
            {/* 用户信息 */}
            <div className="bg-white/5 rounded-2xl p-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center text-xl font-bold">
                  {user?.nickname?.[0] || user?.username?.[0] || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">
                    {user?.nickname || user?.username}
                  </div>
                  <div className="text-sm text-gray-400 truncate">
                    {user?.email}
                  </div>
                </div>
              </div>
              
              {/* 用户等级 */}
              <div className="mt-3 flex items-center justify-between">
                <span className={cn(
                  "px-2 py-0.5 rounded-full text-xs font-medium",
                  user?.level === 'L4_ENTERPRISE' ? 'bg-amber-500/20 text-amber-400' :
                  user?.level === 'L3_STUDIO' ? 'bg-purple-500/20 text-purple-400' :
                  user?.level === 'L2_CREATOR' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-gray-500/20 text-gray-400'
                )}>
                  {user?.level === 'L4_ENTERPRISE' ? '企业版' :
                   user?.level === 'L3_STUDIO' ? '工作室' :
                   user?.level === 'L2_CREATOR' ? '创作者' : '体验版'}
                </span>
                {user?.is_vip && (
                  <span className="flex items-center gap-1 text-xs text-amber-400">
                    <Crown className="w-3 h-3" />
                    VIP
                  </span>
                )}
              </div>
            </div>

            {/* 菜单 */}
            <nav className="space-y-1">
              {MENU_ITEMS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveMenu(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                    activeMenu === item.id
                      ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400"
                      : "text-gray-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                  <ChevronRight className="w-4 h-4 ml-auto opacity-50" />
                </button>
              ))}
            </nav>

            {/* 快速操作 */}
            <div className="mt-4 p-4 bg-gradient-to-br from-cyan-500/10 to-purple-500/10 rounded-2xl border border-white/5">
              <h4 className="text-sm font-medium mb-3">快速操作</h4>
              <button
                onClick={() => router.push('/studio')}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium"
              >
                <Zap className="w-4 h-4" />
                开始创作
              </button>
            </div>
          </aside>

          {/* 主内容 */}
          <main className="flex-1 min-w-0">
            {isLoading ? (
              <div className="bg-white/5 rounded-2xl p-8 animate-pulse">
                <div className="h-8 bg-white/10 rounded w-1/4 mb-4" />
                <div className="h-4 bg-white/10 rounded w-1/2" />
              </div>
            ) : (
              menuComponents[activeMenu]
            )}
          </main>
        </div>
      </div>
    </div>
  )
}

// 概览
function OverviewSection({ user }: { user?: UserData }) {
  const router = useRouter()
  const { data: tasksData } = useQuery({
    queryKey: ['my-tasks-overview'],
    queryFn: () => api.get('/v1/tasks?page=1&page_size=5'),
  })
  const tasks = tasksData?.items || []
  
  const stats = [
    {
      label: '账户余额',
      value: formatCurrency(user?.balance || 0),
      icon: Wallet,
      color: 'from-green-500 to-emerald-500',
    },
    {
      label: '视频额度',
      value: `${user?.video_quota || 0}分钟`,
      icon: Play,
      color: 'from-cyan-500 to-blue-500',
    },
    {
      label: '已用额度',
      value: `${user?.video_used || 0}分钟`,
      icon: Clock,
      color: 'from-purple-500 to-pink-500',
    },
    {
      label: '累计消费',
      value: formatCurrency(user?.video_used ? user.video_used * 0.06 : 0),
      icon: TrendingUp,
      color: 'from-amber-500 to-orange-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white/5 rounded-2xl p-4"
          >
            <div className={cn(
              "w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center mb-3",
              stat.color
            )}>
              <stat.icon className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold">{stat.value}</div>
            <div className="text-sm text-gray-400">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* 最近任务 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">最近任务</h3>
          <button 
            onClick={() => {
              const dashboard = document.querySelector('[data-dashboard]')
              if (dashboard) {
                const event = new CustomEvent('navigate', { detail: 'videos' })
                dashboard.dispatchEvent(event)
              }
            }}
            className="text-sm text-cyan-400 hover:text-cyan-300"
          >
            查看全部
          </button>
        </div>
        
        {tasks.length === 0 ? (
          <div className="text-center py-8">
            <Video className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="text-gray-400 mb-4">暂无创作记录</p>
            <button
              onClick={() => router.push('/studio')}
              className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium"
            >
              开始创作
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {tasks.map((task: Task) => (
              <div key={task.task_id} className="flex items-center gap-4 p-3 bg-white/5 rounded-xl">
                <div className="w-16 h-12 rounded-lg bg-gray-700 overflow-hidden">
                  {task.cover_url && (
                    <img src={task.cover_url} alt="" className="w-full h-full object-cover" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">任务 #{task.task_no}</div>
                  <div className="text-sm text-gray-400">
                    {new Date(task.created_at).toLocaleString()}
                  </div>
                </div>
                <span className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium",
                  task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  task.status === 'processing' ? 'bg-blue-500/20 text-blue-400' :
                  task.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                  'bg-gray-500/20 text-gray-400'
                )}>
                  {task.status === 'completed' ? '已完成' :
                   task.status === 'processing' ? '生成中' :
                   task.status === 'failed' ? '失败' : '排队中'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 会员推广 */}
      {!user?.is_vip && (
        <div className="bg-gradient-to-r from-amber-500/20 to-purple-500/20 rounded-2xl p-6 border border-amber-500/20">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-1">升级VIP会员</h3>
              <p className="text-sm text-gray-400">享无限额度、优先队列、专属客服</p>
            </div>
            <button
              onClick={() => router.push('/pricing')}
              className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
              立即升级
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// 作品
function VideosSection() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null)
  const [page, setPage] = useState(1)

  // 获取我的视频列表
  const { data: videosData, isLoading } = useQuery({
    queryKey: ['my-videos', page, statusFilter],
    queryFn: () => api.get('/v1/videos/my', {
      params: { page, page_size: 12, status: statusFilter !== 'all' ? statusFilter : undefined }
    }),
  })

  const videos: VideoItem[] = videosData?.items || []
  const totalPages = videosData?.total_pages || 1

  // 删除视频
  const deleteMutation = useMutation({
    mutationFn: (videoId: number) => api.post(`/v1/videos/${videoId}/delete`),
    onSuccess: () => {
      toast.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['my-videos'] })
    },
    onError: () => {
      toast.error('删除失败')
    },
  })

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">我的作品</h2>
        <button
          onClick={() => router.push('/studio')}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium"
        >
          <Zap className="w-4 h-4" />
          创作新视频
        </button>
      </div>

      {/* 筛选 */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索我的作品..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-cyan-400/50"
          />
        </div>
        <div className="flex items-center gap-2">
          {['all', 'completed', 'processing', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
                statusFilter === status
                  ? "bg-white/10 text-white"
                  : "text-gray-400 hover:text-white"
              )}
            >
              {status === 'all' ? '全部' :
               status === 'completed' ? '已完成' :
               status === 'processing' ? '生成中' : '失败'}
            </button>
          ))}
        </div>
      </div>

      {/* 视频列表 */}
      {isLoading ? (
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="aspect-video bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : videos.length === 0 ? (
        <div className="text-center py-16 bg-white/5 rounded-2xl">
          <Video className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-400 mb-2">暂无作品</h3>
          <p className="text-sm text-gray-500 mb-4">开始创作你的第一个AI视频吧</p>
          <button
            onClick={() => router.push('/studio')}
            className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-lg text-sm font-medium"
          >
            开始创作
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4">
            {videos.map((video) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="group bg-white/5 rounded-xl overflow-hidden hover:bg-white/10 transition-colors"
              >
                {/* 封面 */}
                <div 
                  className="aspect-video relative cursor-pointer"
                  onClick={() => video.status === 'completed' && setSelectedVideo(video)}
                >
                  {video.cover_url ? (
                    <img
                      src={video.cover_url}
                      alt={video.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                      {video.status === 'processing' ? (
                        <div className="flex flex-col items-center gap-2">
                          <div className="w-8 h-8 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
                          <span className="text-xs text-gray-400">生成中...</span>
                        </div>
                      ) : (
                        <Video className="w-8 h-8 text-gray-600" />
                      )}
                    </div>
                  )}
                  
                  {video.status === 'completed' && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                      <PlayCircle className="w-12 h-12 text-white" />
                    </div>
                  )}
                  
                  {/* 时长 */}
                  {video.duration > 0 && (
                    <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/70 rounded text-xs">
                      {formatDuration(video.duration)}
                    </div>
                  )}
                  
                  {/* 状态标签 */}
                  {video.status !== 'completed' && (
                    <div className="absolute top-2 left-2">
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        video.status === 'processing' ? 'bg-blue-500/80 text-white' :
                        video.status === 'failed' ? 'bg-red-500/80 text-white' :
                        'bg-gray-500/80 text-white'
                      )}>
                        {video.status === 'processing' ? '生成中' : 
                         video.status === 'failed' ? '失败' : '处理中'}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* 信息 */}
                <div className="p-3">
                  <h3 className="font-medium text-sm line-clamp-1 mb-1">
                    {video.title || '无标题'}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>{formatTime(video.created_at)}</span>
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {video.view_count || 0}
                    </span>
                  </div>
                  
                  {/* 操作 */}
                  <div className="flex items-center gap-2 mt-3">
                    {video.status === 'completed' && video.video_url && (
                      <>
                        <a
                          href={video.video_url}
                          download
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition-colors"
                        >
                          <Download className="w-3 h-3" />
                          下载
                        </a>
                        <button
                          onClick={() => setSelectedVideo(video)}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-xs hover:bg-cyan-500/30 transition-colors"
                        >
                          <Eye className="w-3 h-3" />
                          预览
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => deleteMutation.mutate(video.id)}
                      className="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
              >
                上一页
              </button>
              <span className="text-sm text-gray-400">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {/* 视频预览弹窗 */}
      <AnimatePresence>
        {selectedVideo && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setSelectedVideo(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#16161d] rounded-2xl max-w-3xl w-full overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="aspect-video bg-black">
                {selectedVideo.video_url && (
                  <video
                    src={selectedVideo.video_url}
                    controls
                    className="w-full h-full"
                    autoPlay
                  />
                )}
              </div>
              <div className="p-4 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{selectedVideo.title || '无标题'}</h3>
                  <p className="text-sm text-gray-400">{formatTime(selectedVideo.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  {selectedVideo.video_url && (
                    <a
                      href={selectedVideo.video_url}
                      download
                      className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      下载
                    </a>
                  )}
                  <button
                    onClick={() => setSelectedVideo(null)}
                    className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <X className="w-4 h-4" />
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

// 订单
function OrdersSection() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data: ordersData, isLoading } = useQuery({
    queryKey: ['my-orders', page, statusFilter],
    queryFn: () => api.get('/v1/orders', {
      params: { page, page_size: 10, status: statusFilter !== 'all' ? statusFilter : undefined }
    }),
  })

  const orders: Order[] = ordersData?.items || []
  const totalPages = ordersData?.total_pages || 1

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">订单记录</h2>

      {/* 筛选 */}
      <div className="flex items-center gap-2">
        {['all', 'paid', 'pending', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
              statusFilter === status
                ? "bg-white/10 text-white"
                : "text-gray-400 hover:text-white"
            )}
          >
            {status === 'all' ? '全部' :
             status === 'paid' ? '已支付' :
             status === 'pending' ? '待支付' : '已取消'}
          </button>
        ))}
      </div>

      {/* 订单列表 */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-16 bg-white/5 rounded-2xl">
          <CreditCard className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-medium text-gray-400 mb-2">暂无订单记录</h3>
          <p className="text-sm text-gray-500">购买套餐即可获得更多额度</p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {orders.map((order) => (
              <div key={order.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    order.status === 'paid' ? 'bg-green-500/20' :
                    order.status === 'pending' ? 'bg-amber-500/20' :
                    'bg-gray-500/20'
                  )}>
                    <CreditCard className={cn(
                      "w-5 h-5",
                      order.status === 'paid' ? 'text-green-400' :
                      order.status === 'pending' ? 'text-amber-400' :
                      'text-gray-400'
                    )} />
                  </div>
                  <div>
                    <div className="font-medium">订单 #{order.order_no}</div>
                    <div className="text-sm text-gray-400">
                      {formatTime(order.created_at)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {order.type === 'recharge' ? '充值' :
                       order.type === 'package' ? '购买套餐' :
                       order.type === 'vip' ? 'VIP会员' : '其他'}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">¥{order.actual_amount}</div>
                  <span className={cn(
                    "text-sm",
                    order.status === 'paid' ? 'text-green-400' :
                    order.status === 'pending' ? 'text-amber-400' :
                    'text-gray-400'
                  )}>
                    {order.status === 'paid' ? '已支付' :
                     order.status === 'pending' ? '待支付' :
                     order.status === 'cancelled' ? '已取消' : '已退款'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
              >
                上一页
              </button>
              <span className="text-sm text-gray-400">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// 钱包
function WalletSection({ user }: { user?: UserData }) {
  const router = useRouter()
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null)
  const [customAmount, setCustomAmount] = useState('')

  const amounts = [50, 100, 200, 500, 1000]

  const handleRecharge = () => {
    const amount = selectedAmount || parseFloat(customAmount)
    if (!amount || amount <= 0) {
      toast.error('请输入正确的金额')
      return
    }
    router.push(`/pricing?amount=${amount}`)
  }

  return (
    <div className="space-y-6">
      {/* 余额卡片 */}
      <div className="bg-gradient-to-br from-cyan-500 to-purple-500 rounded-2xl p-6">
        <div className="text-sm text-white/70 mb-2">账户余额</div>
        <div className="text-4xl font-bold mb-4">
          ¥{formatCurrency(user?.balance || 0)}
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => router.push('/pricing')}
            className="px-4 py-2 bg-white text-cyan-600 rounded-lg text-sm font-medium"
          >
            充值
          </button>
        </div>
      </div>

      {/* 额度信息 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4">视频额度</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-400">已使用</span>
              <span>{user?.video_used || 0} / {user?.video_quota || 0} 分钟</span>
            </div>
            <div className="h-3 bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full transition-all"
                style={{ width: `${user?.video_quota ? Math.min(100, (user.video_used / user.video_quota) * 100) : 0}%` }}
              />
            </div>
          </div>
          
          <div className="pt-4 border-t border-white/5">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">剩余额度</span>
              <span className="text-cyan-400 font-medium">
                {Math.max(0, (user?.video_quota || 0) - (user?.video_used || 0))} 分钟
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 充值快捷金额 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4">快捷充值</h3>
        <div className="grid grid-cols-5 gap-3 mb-4">
          {amounts.map((amount) => (
            <button
              key={amount}
              onClick={() => setSelectedAmount(amount)}
              className={cn(
                "p-4 rounded-xl text-center transition-colors",
                selectedAmount === amount
                  ? "bg-cyan-500/20 border-2 border-cyan-500 text-cyan-400"
                  : "bg-white/5 border-2 border-transparent hover:bg-white/10"
              )}
            >
              <div className="text-xl font-bold">¥{amount}</div>
              <div className="text-xs text-gray-400 mt-1">
                {Math.floor(amount / 0.06)}分钟
              </div>
            </button>
          ))}
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="number"
              placeholder="输入自定义金额"
              value={customAmount}
              onChange={(e) => {
                setCustomAmount(e.target.value)
                setSelectedAmount(null)
              }}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-cyan-400/50"
            />
          </div>
          <button
            onClick={handleRecharge}
            className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-xl font-medium"
          >
            立即充值
          </button>
        </div>
      </div>
    </div>
  )
}

// 会员
function SubscriptionSection({ user }: { user?: UserData }) {
  const router = useRouter()

  return (
    <div className="space-y-6">
      {user?.is_vip ? (
        <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-2">
            <Crown className="w-6 h-6" />
            <span className="text-lg font-semibold">VIP会员</span>
          </div>
          <p className="text-white/70 mb-4">
            有效期至：{user.vip_expires_at ? new Date(user.vip_expires_at).toLocaleDateString() : '永久'}
          </p>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-white/10 rounded-xl p-3">
              <div className="text-2xl font-bold">∞</div>
              <div className="text-xs text-white/70">无限额度</div>
            </div>
            <div className="bg-white/10 rounded-xl p-3">
              <div className="text-2xl font-bold">✓</div>
              <div className="text-xs text-white/70">优先队列</div>
            </div>
            <div className="bg-white/10 rounded-xl p-3">
              <div className="text-2xl font-bold">✓</div>
              <div className="text-xs text-white/70">专属客服</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white/5 rounded-2xl p-6 text-center">
          <Crown className="w-16 h-16 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-semibold mb-2">开通VIP会员</h3>
          <p className="text-gray-400 mb-4">享无限额度、优先队列、专属客服</p>
          <button
            onClick={() => router.push('/pricing')}
            className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl font-medium"
          >
            立即开通
          </button>
        </div>
      )}

      {/* VIP特权 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4">会员特权</h3>
        <div className="grid grid-cols-2 gap-4">
          {[
            { icon: Crown, title: '无限额度', desc: '无限制创建AI视频' },
            { icon: Zap, title: '优先队列', desc: '任务排队优先处理' },
            { icon: Star, title: '专属模板', desc: '解锁全部官方模板' },
            { icon: Gift, title: '专属客服', desc: '7x24小时人工客服' },
          ].map((item) => (
            <div key={item.title} className="flex items-start gap-3 p-4 bg-white/5 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <item.icon className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <div className="font-medium">{item.title}</div>
                <div className="text-sm text-gray-400">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// 设置
function SettingsSection() {
  const [copied, setCopied] = useState(false)
  const [activeSection, setActiveSection] = useState('profile')

  const handleCopyApiKey = async () => {
    await navigator.clipboard.writeText('your-api-key-here')
    setCopied(true)
    toast.success('API Key已复制')
    setTimeout(() => setCopied(false), 2000)
  }

  const sections = [
    { id: 'profile', name: '个人资料', icon: User },
    { id: 'security', name: '安全设置', icon: Shield },
    { id: 'api', name: 'API设置', icon: Key },
    { id: 'notifications', name: '通知设置', icon: Bell },
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">设置</h2>

      <div className="flex gap-6">
        {/* 左侧菜单 */}
        <div className="w-48 space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                activeSection === section.id
                  ? "bg-white/10 text-white"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              )}
            >
              <section.icon className="w-4 h-4" />
              {section.name}
            </button>
          ))}
        </div>

        {/* 右侧内容 */}
        <div className="flex-1 bg-white/5 rounded-2xl p-6">
          {activeSection === 'profile' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">个人资料</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <User className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">头像</div>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-white/10 rounded-lg">
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-medium">用户名</div>
                      <div className="text-sm text-gray-400">修改用户名</div>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-white/10 rounded-lg">
                    <Edit className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-medium">邮箱</div>
                      <div className="text-sm text-gray-400">user@example.com</div>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-white/10 rounded-lg">
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'security' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">安全设置</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">密码</div>
                      <div className="text-sm text-gray-400">上次修改：30天前</div>
                    </div>
                  </div>
                  <button className="p-2 hover:bg-white/10 rounded-lg">
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <Key className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">两步验证</div>
                      <div className="text-sm text-gray-400">未开启</div>
                    </div>
                  </div>
                  <button className="px-3 py-1.5 bg-white/10 rounded-lg text-sm">
                    开启
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'api' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">API设置</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <Key className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">API Key</div>
                      <div className="text-sm text-gray-400">用于API调用</div>
                    </div>
                  </div>
                  <button 
                    onClick={handleCopyApiKey}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white/10 rounded-lg text-sm"
                  >
                    {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                    复制
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold">通知设置</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <Bell className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">任务完成通知</div>
                      <div className="text-sm text-gray-400">视频生成完成时通知</div>
                    </div>
                  </div>
                  <button className="w-12 h-6 bg-cyan-500 rounded-full relative">
                    <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                  </button>
                </div>
                
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div className="flex items-center gap-3">
                    <Bell className="w-5 h-5 text-gray-400" />
                    <div>
                      <div className="font-medium">营销通知</div>
                      <div className="text-sm text-gray-400">促销活动与更新</div>
                    </div>
                  </div>
                  <button className="w-12 h-6 bg-white/20 rounded-full relative">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-gray-400 rounded-full" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 登出 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <button className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500/20 text-red-400 rounded-xl hover:bg-red-500/30 transition-colors">
          <LogOut className="w-5 h-5" />
          退出登录
        </button>
      </div>
    </div>
  )
}