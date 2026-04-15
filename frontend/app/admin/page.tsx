'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Users, Video, CreditCard, Settings, BarChart3, 
  TrendingUp, TrendingDown, DollarSign, Activity,
  Shield, Server, AlertTriangle, CheckCircle, XCircle,
  RefreshCw, Search, Filter, MoreVertical, Edit, Trash2,
  Eye, Pause, Play, Download, X, ChevronDown, Check,
  Clock, Flag, Ban, Zap, ExternalLink, Copy, Image
} from 'lucide-react'
import { toast } from 'sonner'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

// 导航项
const NAV_ITEMS = [
  { id: 'dashboard', name: '仪表盘', icon: BarChart3 },
  { id: 'users', name: '用户管理', icon: Users },
  { id: 'videos', name: '作品管理', icon: Video },
  { id: 'orders', name: '订单管理', icon: CreditCard },
  { id: 'tasks', name: '任务管理', icon: Zap },
  { id: 'review', name: '内容审核', icon: Shield },
]

// 统计卡片数据
interface Stats {
  total_users: number
  total_videos: number
  total_orders: number
  total_revenue: number
  today_users: number
  today_videos: number
  today_orders: number
  today_revenue: number
  pending_review_count: number
}

interface User {
  id: number
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  level: string
  balance: number
  is_vip: boolean
  is_active: boolean
  video_count: number
  order_count: number
  total_consumption: number
  created_at: string
  last_login_at: string
}

interface VideoItem {
  id: number
  title: string
  description: string
  video_url: string
  cover_url: string
  status: 'processing' | 'completed' | 'failed'
  review_status: 'pending' | 'approved' | 'rejected'
  view_count: number
  like_count: number
  user: { id: number; username: string; nickname: string }
  created_at: string
  tags: string[]
}

interface Order {
  id: number
  order_no: string
  user: { id: number; username: string }
  type: string
  amount: number
  actual_amount: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  payment_method: string | null
  created_at: string
  paid_at: string | null
}

interface Task {
  task_id: string
  task_no: string
  user: { id: number; username: string }
  mode: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  prompt: string
  video_url: string | null
  cover_url: string | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

interface ReviewItem {
  id: number
  video_id: number
  title: string
  cover_url: string
  video_url: string
  user: { id: number; username: string; nickname: string }
  reason: string
  flagged_at: string
  status: 'pending' | 'approved' | 'rejected'
}

export default function AdminPage() {
  const [activeNav, setActiveNav] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')

  // 获取统计数据
  const { data: stats } = useQuery<Stats>({
    queryKey: ['admin-stats'],
    queryFn: () => api.get('/v1/admin/stats'),
  })

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex">
      {/* 侧边栏 */}
      <aside className="w-64 bg-[#12121a] border-r border-white/5 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-white/5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center font-bold text-white">
            M
          </div>
          <span className="ml-3 font-bold">漫AI 管理后台</span>
        </div>

        {/* 导航 */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors relative",
                activeNav === item.id
                  ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
              {item.id === 'review' && stats?.pending_review_count ? (
                <span className="absolute right-3 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center">
                  {stats.pending_review_count > 9 ? '9+' : stats.pending_review_count}
                </span>
              ) : null}
            </button>
          ))}
        </nav>

        {/* 底部信息 */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>系统正常运行</span>
          </div>
          <div className="text-xs text-gray-600 mt-1">
            v3.0.0
          </div>
        </div>
      </aside>

      {/* 主内容 */}
      <main className="flex-1 overflow-auto">
        {/* 顶部栏 */}
        <header className="h-16 bg-[#12121a]/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">
              {NAV_ITEMS.find(n => n.id === activeNav)?.name}
            </h2>
          </div>

          <div className="flex items-center gap-4">
            {/* 搜索 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-cyan-400/50"
              />
            </div>

            {/* 通知 */}
            <button className="relative p-2 rounded-lg hover:bg-white/5">
              <AlertTriangle className="w-5 h-5 text-gray-400" />
              {stats?.pending_review_count ? (
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              ) : null}
            </button>

            {/* 头像 */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
              <span className="text-sm font-medium">管</span>
            </div>
          </div>
        </header>

        {/* 内容区 */}
        <div className="p-6">
          {activeNav === 'dashboard' && <DashboardContent stats={stats} />}
          {activeNav === 'users' && <UsersContent searchQuery={searchQuery} />}
          {activeNav === 'videos' && <VideosContent searchQuery={searchQuery} />}
          {activeNav === 'orders' && <OrdersContent searchQuery={searchQuery} />}
          {activeNav === 'tasks' && <TasksContent searchQuery={searchQuery} />}
          {activeNav === 'review' && <ReviewContent />}
        </div>
      </main>
    </div>
  )
}

// 仪表盘内容
function DashboardContent({ stats }: { stats?: Stats }) {
  const statCards = [
    {
      title: '总用户数',
      value: stats?.total_users || 0,
      change: '+12.5%',
      trend: 'up',
      icon: Users,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      title: '总作品数',
      value: stats?.total_videos || 0,
      change: '+8.2%',
      trend: 'up',
      icon: Video,
      color: 'from-purple-500 to-pink-500',
    },
    {
      title: '总订单数',
      value: stats?.total_orders || 0,
      change: '+15.3%',
      trend: 'up',
      icon: CreditCard,
      color: 'from-amber-500 to-orange-500',
    },
    {
      title: '总收入',
      value: `¥${((stats?.total_revenue || 0) / 10000).toFixed(1)}万`,
      change: '+23.1%',
      trend: 'up',
      icon: DollarSign,
      color: 'from-green-500 to-emerald-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-[#16161d] rounded-2xl p-6 border border-white/5"
          >
            <div className="flex items-center justify-between mb-4">
              <div className={cn(
                "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center",
                card.color
              )}>
                <card.icon className="w-6 h-6 text-white" />
              </div>
              <div className={cn(
                "flex items-center gap-1 text-sm",
                card.trend === 'up' ? 'text-green-400' : 'text-red-400'
              )}>
                {card.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                {card.change}
              </div>
            </div>
            <div className="text-2xl font-bold mb-1">{card.value}</div>
            <div className="text-sm text-gray-400">{card.title}</div>
          </motion.div>
        ))}
      </div>

      {/* 今日概览 */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-[#16161d] rounded-2xl p-4 border border-white/5">
          <div className="text-sm text-gray-400 mb-1">今日新增用户</div>
          <div className="text-xl font-bold text-green-400">+{stats?.today_users || 0}</div>
        </div>
        <div className="bg-[#16161d] rounded-2xl p-4 border border-white/5">
          <div className="text-sm text-gray-400 mb-1">今日作品</div>
          <div className="text-xl font-bold text-cyan-400">+{stats?.today_videos || 0}</div>
        </div>
        <div className="bg-[#16161d] rounded-2xl p-4 border border-white/5">
          <div className="text-sm text-gray-400 mb-1">今日订单</div>
          <div className="text-xl font-bold text-amber-400">+{stats?.today_orders || 0}</div>
        </div>
        <div className="bg-[#16161d] rounded-2xl p-4 border border-white/5">
          <div className="text-sm text-gray-400 mb-1">今日收入</div>
          <div className="text-xl font-bold text-purple-400">¥{stats?.today_revenue || 0}</div>
        </div>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-[#16161d] rounded-2xl p-6 border border-white/5">
          <h3 className="text-lg font-semibold mb-4">收入趋势</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            <Activity className="w-8 h-8 mr-2" />
            图表加载中...
          </div>
        </div>
        
        <div className="bg-[#16161d] rounded-2xl p-6 border border-white/5">
          <h3 className="text-lg font-semibold mb-4">用户增长</h3>
          <div className="h-64 flex items-center justify-center text-gray-500">
            <Users className="w-8 h-8 mr-2" />
            图表加载中...
          </div>
        </div>
      </div>

      {/* 待审核 */}
      {stats?.pending_review_count ? (
        <div className="bg-[#16161d] rounded-2xl p-6 border border-white/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <div className="font-medium">待审核内容</div>
                <div className="text-sm text-gray-400">有 {stats.pending_review_count} 个作品待审核</div>
              </div>
            </div>
            <button className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
              立即处理
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}

// 用户管理
function UsersContent({ searchQuery }: { searchQuery: string }) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [levelFilter, setLevelFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', page, levelFilter, statusFilter, searchQuery],
    queryFn: () => api.get('/v1/admin/users', {
      params: {
        page,
        page_size: 20,
        level: levelFilter !== 'all' ? levelFilter : undefined,
        is_active: statusFilter !== 'all' ? statusFilter === 'active' : undefined,
        search: searchQuery || undefined,
      }
    }),
  })

  const users: User[] = data?.items || []
  const totalPages = data?.total_pages || 1

  // 禁用/启用用户
  const toggleUserStatus = useMutation({
    mutationFn: ({ userId, isActive }: { userId: number; isActive: boolean }) =>
      api.post(`/v1/admin/users/${userId}/${isActive ? 'enable' : 'disable'}`),
    onSuccess: () => {
      toast.success('操作成功')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: () => toast.error('操作失败'),
  })

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg">
            <Download className="w-4 h-4" />
            导出
          </button>
          <button 
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          {['all', 'L1_BASIC', 'L2_CREATOR', 'L3_STUDIO', 'L4_ENTERPRISE'].map((level) => (
            <button
              key={level}
              onClick={() => setLevelFilter(level)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm transition-colors",
                levelFilter === level ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
              )}
            >
              {level === 'all' ? '全部等级' :
               level === 'L1_BASIC' ? '体验版' :
               level === 'L2_CREATOR' ? '创作者' :
               level === 'L3_STUDIO' ? '工作室' : '企业版'}
            </button>
          ))}
        </div>
      </div>

      {/* 用户列表 */}
      <div className="bg-[#16161d] rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-gray-400">用户</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">等级</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">余额</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">消费</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">作品</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">注册时间</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">状态</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="p-4"><div className="h-10 bg-white/5 rounded w-32 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-12 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-24 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-8 bg-white/5 rounded w-24 animate-pulse" /></td>
                </tr>
              ))
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">暂无用户</td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
                        {user.nickname?.[0] || user.username[0]}
                      </div>
                      <div>
                        <div className="font-medium">{user.nickname || user.username}</div>
                        <div className="text-sm text-gray-400">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-sm",
                      user.level === 'L4_ENTERPRISE' ? 'bg-amber-500/20 text-amber-400' :
                      user.level === 'L3_STUDIO' ? 'bg-purple-500/20 text-purple-400' :
                      user.level === 'L2_CREATOR' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    )}>
                      {user.level === 'L4_ENTERPRISE' ? '企业版' :
                       user.level === 'L3_STUDIO' ? '工作室' :
                       user.level === 'L2_CREATOR' ? '创作者' : '体验版'}
                    </span>
                  </td>
                  <td className="p-4">¥{user.balance.toFixed(2)}</td>
                  <td className="p-4">¥{user.total_consumption.toFixed(2)}</td>
                  <td className="p-4">{user.video_count}</td>
                  <td className="p-4 text-gray-400">{new Date(user.created_at).toLocaleDateString()}</td>
                  <td className="p-4">
                    <span className={cn(
                      "flex items-center gap-1 text-sm",
                      user.is_active ? 'text-green-400' : 'text-red-400'
                    )}>
                      {user.is_active ? (
                        <><CheckCircle className="w-4 h-4" /> 正常</>
                      ) : (
                        <><XCircle className="w-4 h-4" /> 禁用</>
                      )}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1">
                      <button className="p-2 hover:bg-white/10 rounded-lg" title="查看">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => toggleUserStatus.mutate({ userId: user.id, isActive: !user.is_active })}
                        className={cn(
                          "p-2 hover:bg-white/10 rounded-lg",
                          user.is_active ? 'text-red-400' : 'text-green-400'
                        )}
                        title={user.is_active ? '禁用' : '启用'}
                      >
                        {user.is_active ? <Ban className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
          <span className="text-sm text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}

// 作品管理
function VideosContent({ searchQuery }: { searchQuery: string }) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-videos', page, statusFilter, searchQuery],
    queryFn: () => api.get('/v1/admin/videos', {
      params: {
        page,
        page_size: 20,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchQuery || undefined,
      }
    }),
  })

  const videos: VideoItem[] = data?.items || []
  const totalPages = data?.total_pages || 1

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg">
            <Download className="w-4 h-4" />
            导出
          </button>
          <button 
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin-videos'] })}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          {['all', 'completed', 'processing', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm transition-colors",
                statusFilter === status ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
              )}
            >
              {status === 'all' ? '全部' :
               status === 'completed' ? '已完成' :
               status === 'processing' ? '生成中' : '失败'}
            </button>
          ))}
        </div>
      </div>

      {/* 作品列表 */}
      <div className="bg-[#16161d] rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-gray-400">作品</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">作者</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">播放</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">点赞</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">状态</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">审核</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">时间</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="p-4"><div className="h-12 bg-white/5 rounded w-32 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-12 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-8 bg-white/5 rounded w-20 animate-pulse" /></td>
                </tr>
              ))
            ) : videos.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">暂无作品</td>
              </tr>
            ) : (
              videos.map((video) => (
                <tr key={video.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-16 h-10 rounded-lg bg-gray-800 overflow-hidden">
                        {video.cover_url && (
                          <img src={video.cover_url} alt="" className="w-full h-full object-cover" />
                        )}
                      </div>
                      <span className="font-medium line-clamp-1">{video.title || '无标题'}</span>
                    </div>
                  </td>
                  <td className="p-4 text-gray-400">
                    {video.user.nickname || video.user.username}
                  </td>
                  <td className="p-4">{video.view_count}</td>
                  <td className="p-4">{video.like_count}</td>
                  <td className="p-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      video.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      video.status === 'processing' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-red-500/20 text-red-400'
                    )}>
                      {video.status === 'completed' ? '已完成' :
                       video.status === 'processing' ? '生成中' : '失败'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      video.review_status === 'approved' ? 'bg-green-500/20 text-green-400' :
                      video.review_status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-red-500/20 text-red-400'
                    )}>
                      {video.review_status === 'approved' ? '已通过' :
                       video.review_status === 'pending' ? '待审核' : '已拒绝'}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400">
                    {new Date(video.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1">
                      <button 
                        onClick={() => setSelectedVideo(video)}
                        className="p-2 hover:bg-white/10 rounded-lg" title="预览"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {video.video_url && (
                        <a href={video.video_url} target="_blank" className="p-2 hover:bg-white/10 rounded-lg" title="下载">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
          <span className="text-sm text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            下一页
          </button>
        </div>
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
                  <video src={selectedVideo.video_url} controls className="w-full h-full" />
                )}
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{selectedVideo.title || '无标题'}</h3>
                    <p className="text-sm text-gray-400">
                      作者: {selectedVideo.user.nickname || selectedVideo.user.username}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedVideo(null)}
                    className="p-2 bg-white/10 rounded-lg hover:bg-white/20"
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

// 订单管理
function OrdersContent({ searchQuery }: { searchQuery: string }) {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('all')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-orders', page, statusFilter, searchQuery],
    queryFn: () => api.get('/v1/admin/orders', {
      params: {
        page,
        page_size: 20,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchQuery || undefined,
      }
    }),
  })

  const orders: Order[] = data?.items || []
  const totalPages = data?.total_pages || 1

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg">
            <Download className="w-4 h-4" />
            导出
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          {['all', 'paid', 'pending', 'cancelled', 'refunded'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm transition-colors",
                statusFilter === status ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
              )}
            >
              {status === 'all' ? '全部' :
               status === 'paid' ? '已支付' :
               status === 'pending' ? '待支付' :
               status === 'cancelled' ? '已取消' : '已退款'}
            </button>
          ))}
        </div>
      </div>

      {/* 订单列表 */}
      <div className="bg-[#16161d] rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-gray-400">订单号</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">用户</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">类型</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">金额</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">实付</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">支付方式</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">状态</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">时间</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-24 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-24 animate-pulse" /></td>
                </tr>
              ))
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">暂无订单</td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-4 font-mono text-sm">{order.order_no}</td>
                  <td className="p-4">{order.user.username}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-white/5 rounded text-sm">
                      {order.type === 'recharge' ? '充值' :
                       order.type === 'package' ? '套餐' :
                       order.type === 'vip' ? 'VIP' : '其他'}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400">¥{order.amount.toFixed(2)}</td>
                  <td className="p-4 font-medium">¥{order.actual_amount.toFixed(2)}</td>
                  <td className="p-4 text-gray-400">
                    {order.payment_method === 'alipay' ? '支付宝' :
                     order.payment_method === 'wechat' ? '微信' : '-'}
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      order.status === 'paid' ? 'bg-green-500/20 text-green-400' :
                      order.status === 'pending' ? 'bg-amber-500/20 text-amber-400' :
                      order.status === 'cancelled' ? 'bg-gray-500/20 text-gray-400' :
                      'bg-red-500/20 text-red-400'
                    )}>
                      {order.status === 'paid' ? '已支付' :
                       order.status === 'pending' ? '待支付' :
                       order.status === 'cancelled' ? '已取消' : '已退款'}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400 text-sm">
                    {new Date(order.created_at).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
          <span className="text-sm text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}

// 任务管理
function TasksContent({ searchQuery }: { searchQuery: string }) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('all')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-tasks', page, statusFilter, searchQuery],
    queryFn: () => api.get('/v1/admin/tasks', {
      params: {
        page,
        page_size: 20,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchQuery || undefined,
      }
    }),
  })

  const tasks: Task[] = data?.items || []
  const totalPages = data?.total_pages || 1

  // 取消任务
  const cancelMutation = useMutation({
    mutationFn: (taskId: string) => api.post(`/v1/admin/tasks/${taskId}/cancel`),
    onSuccess: () => {
      toast.success('任务已取消')
      queryClient.invalidateQueries({ queryKey: ['admin-tasks'] })
    },
    onError: () => toast.error('操作失败'),
  })

  // 重试任务
  const retryMutation = useMutation({
    mutationFn: (taskId: string) => api.post(`/v1/admin/tasks/${taskId}/retry`),
    onSuccess: () => {
      toast.success('任务已重试')
      queryClient.invalidateQueries({ queryKey: ['admin-tasks'] })
    },
    onError: () => toast.error('操作失败'),
  })

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors">
            <RefreshCw className="w-4 h-4" />
            刷新队列
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          {['all', 'pending', 'processing', 'completed', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm transition-colors",
                statusFilter === status ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
              )}
            >
              {status === 'all' ? '全部' :
               status === 'pending' ? '排队中' :
               status === 'processing' ? '生成中' :
               status === 'completed' ? '已完成' : '失败'}
            </button>
          ))}
        </div>
      </div>

      {/* 任务列表 */}
      <div className="bg-[#16161d] rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-gray-400">任务ID</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">用户</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">模式</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">进度</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">状态</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">提示词</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">创建时间</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-12 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-16 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-32 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-24 animate-pulse" /></td>
                  <td className="p-4"><div className="h-8 bg-white/5 rounded w-20 animate-pulse" /></td>
                </tr>
              ))
            ) : tasks.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-gray-500">暂无任务</td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr key={task.task_id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-4 font-mono text-sm">#{task.task_no}</td>
                  <td className="p-4">{task.user.username}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs">
                      {task.mode}
                    </span>
                  </td>
                  <td className="p-4">
                    {task.status === 'processing' ? (
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-white/10 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-cyan-500 rounded-full transition-all"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400">{task.progress}%</span>
                      </div>
                    ) : '-'}
                  </td>
                  <td className="p-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      task.status === 'processing' ? 'bg-blue-500/20 text-blue-400' :
                      task.status === 'pending' ? 'bg-gray-500/20 text-gray-400' :
                      'bg-red-500/20 text-red-400'
                    )}>
                      {task.status === 'completed' ? '已完成' :
                       task.status === 'processing' ? '生成中' :
                       task.status === 'pending' ? '排队中' :
                       task.status === 'cancelled' ? '已取消' : '失败'}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm text-gray-400 line-clamp-1 max-w-xs">
                      {task.prompt}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400 text-sm">
                    {new Date(task.created_at).toLocaleString()}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1">
                      {task.status === 'pending' && (
                        <button 
                          onClick={() => cancelMutation.mutate(task.task_id)}
                          className="p-2 hover:bg-white/10 rounded-lg text-red-400" title="取消"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                      {task.status === 'failed' && (
                        <button 
                          onClick={() => retryMutation.mutate(task.task_id)}
                          className="p-2 hover:bg-white/10 rounded-lg text-green-400" title="重试"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      {task.video_url && (
                        <a href={task.video_url} target="_blank" className="p-2 hover:bg-white/10 rounded-lg" title="预览">
                          <Eye className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
          <span className="text-sm text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}

// 内容审核
function ReviewContent() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [selectedItem, setSelectedItem] = useState<ReviewItem | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-review', page],
    queryFn: () => api.get('/v1/admin/review/pending', {
      params: { page, page_size: 20 }
    }),
  })

  const items: ReviewItem[] = data?.items || []
  const totalPages = data?.total_pages || 1

  // 审核操作
  const reviewMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'approve' | 'reject' }) =>
      api.post(`/v1/admin/review/${id}/${action}`),
    onSuccess: () => {
      toast.success('审核操作成功')
      queryClient.invalidateQueries({ queryKey: ['admin-review'] })
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
      setSelectedItem(null)
    },
    onError: () => toast.error('操作失败'),
  })

  return (
    <div className="space-y-4">
      {/* 提示 */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          <div>
            <div className="font-medium">待审核内容</div>
            <div className="text-sm text-gray-400">请仔细审核每个作品，确保内容符合平台规范</div>
          </div>
        </div>
      </div>

      {/* 审核列表 */}
      <div className="bg-[#16161d] rounded-2xl border border-white/5 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-gray-400">作品</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">作者</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">举报原因</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">时间</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="p-4"><div className="h-12 bg-white/5 rounded w-32 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-20 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-32 animate-pulse" /></td>
                  <td className="p-4"><div className="h-6 bg-white/5 rounded w-24 animate-pulse" /></td>
                  <td className="p-4"><div className="h-8 bg-white/5 rounded w-24 animate-pulse" /></td>
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-gray-500">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                  暂无待审核内容
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-b border-white/5 hover:bg-white/5">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-16 h-10 rounded-lg bg-gray-800 overflow-hidden">
                        {item.cover_url && (
                          <img src={item.cover_url} alt="" className="w-full h-full object-cover" />
                        )}
                      </div>
                      <span className="font-medium line-clamp-1">{item.title || '无标题'}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    {item.user.nickname || item.user.username}
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">
                      {item.reason}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400 text-sm">
                    {new Date(item.flagged_at).toLocaleString()}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => setSelectedItem(item)}
                        className="p-2 hover:bg-white/10 rounded-lg" title="查看"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => reviewMutation.mutate({ id: item.id, action: 'approve' })}
                        className="p-2 hover:bg-green-500/10 rounded-lg text-green-400" title="通过"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => reviewMutation.mutate({ id: item.id, action: 'reject' })}
                        className="p-2 hover:bg-red-500/10 rounded-lg text-red-400" title="拒绝"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
          <span className="text-sm text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white/5 rounded-lg text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
          >
            下一页
          </button>
        </div>
      )}

      {/* 审核详情弹窗 */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setSelectedItem(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[#16161d] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-white/5 flex items-center justify-between">
                <h3 className="font-semibold">审核详情</h3>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="p-2 hover:bg-white/10 rounded-lg"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              
              <div className="flex-1 overflow-auto">
                <div className="aspect-video bg-black">
                  {selectedItem.video_url && (
                    <video src={selectedItem.video_url} controls className="w-full h-full" />
                  )}
                </div>
                
                <div className="p-4 space-y-4">
                  <div>
                    <div className="text-sm text-gray-400 mb-1">标题</div>
                    <div className="font-medium">{selectedItem.title || '无标题'}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-400 mb-1">作者</div>
                    <div>{selectedItem.user.nickname || selectedItem.user.username}</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-400 mb-1">举报原因</div>
                    <div className="text-red-400">{selectedItem.reason}</div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 border-t border-white/5 flex items-center justify-end gap-3">
                <button
                  onClick={() => reviewMutation.mutate({ id: selectedItem.id, action: 'reject' })}
                  className="px-6 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                >
                  拒绝
                </button>
                <button
                  onClick={() => reviewMutation.mutate({ id: selectedItem.id, action: 'approve' })}
                  className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                >
                  通过
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}