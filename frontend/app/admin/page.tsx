'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Users, Video, CreditCard, Settings, BarChart3, 
  TrendingUp, TrendingDown, DollarSign, Activity,
  Shield, Server, AlertTriangle, CheckCircle, XCircle,
  RefreshCw, Search, Filter, MoreVertical, Edit, Trash2,
  Eye, Pause, Play, Download
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
  { id: 'channels', name: '渠道管理', icon: Server },
  { id: 'system', name: '系统设置', icon: Settings },
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
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                activeNav === item.id
                  ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-400"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
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
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
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
          {activeNav === 'channels' && <ChannelsContent />}
          {activeNav === 'system' && <SystemContent />}
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

      {/* 最近订单 */}
      <div className="bg-[#16161d] rounded-2xl p-6 border border-white/5">
        <h3 className="text-lg font-semibold mb-4">最近订单</h3>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <div className="font-medium">订单 #{1000 + i}</div>
                  <div className="text-sm text-gray-400">用户 {i} · 创作者月卡</div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium text-green-400">¥399</div>
                <div className="text-sm text-gray-400">刚刚</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// 用户管理
function UsersContent({ searchQuery }: { searchQuery: string }) {
  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 text-white rounded-lg">
            <Users className="w-4 h-4" />
            导出
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg">
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
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
              <th className="text-left p-4 text-sm font-medium text-gray-400">注册时间</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">状态</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4, 5].map((i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
                      用
                    </div>
                    <div>
                      <div className="font-medium">用户 {i}</div>
                      <div className="text-sm text-gray-400">user{i}@example.com</div>
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-sm">
                    创作者
                  </span>
                </td>
                <td className="p-4">¥1,234</td>
                <td className="p-4">¥5,678</td>
                <td className="p-4 text-gray-400">2026-01-15</td>
                <td className="p-4">
                  <span className="flex items-center gap-1 text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    正常
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <button className="p-2 hover:bg-white/10 rounded-lg">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-2 hover:bg-white/10 rounded-lg">
                      <Edit className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// 作品管理
function VideosContent({ searchQuery }: { searchQuery: string }) {
  return (
    <div className="space-y-4">
      <div className="bg-[#16161d] rounded-2xl border border-white/5 p-6">
        <p className="text-gray-400">作品管理功能</p>
      </div>
    </div>
  )
}

// 订单管理
function OrdersContent({ searchQuery }: { searchQuery: string }) {
  return (
    <div className="space-y-4">
      <div className="bg-[#16161d] rounded-2xl border border-white/5 p-6">
        <p className="text-gray-400">订单管理功能</p>
      </div>
    </div>
  )
}

// 渠道管理
function ChannelsContent() {
  const channels = [
    { name: 'Wan2.1-14B', status: 'online', requests: 12345, success_rate: 98.5, avg_time: '30s' },
    { name: 'Wan2.1-1.3B', status: 'online', requests: 23456, success_rate: 99.1, avg_time: '15s' },
    { name: 'Vidu', status: 'online', requests: 5678, success_rate: 97.2, avg_time: '45s' },
    { name: '可灵', status: 'online', requests: 8901, success_rate: 96.8, avg_time: '60s' },
  ]

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4">
        {channels.map((channel) => (
          <div key={channel.name} className="bg-[#16161d] rounded-2xl p-6 border border-white/5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">{channel.name}</h3>
              <span className={cn(
                "flex items-center gap-1 text-sm",
                channel.status === 'online' ? 'text-green-400' : 'text-red-400'
              )}>
                {channel.status === 'online' ? (
                  <><CheckCircle className="w-4 h-4" /> 在线</>
                ) : (
                  <><XCircle className="w-4 h-4" /> 离线</>
                )}
              </span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">请求数</span>
                <span>{channel.requests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">成功率</span>
                <span className="text-green-400">{channel.success_rate}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">平均耗时</span>
                <span>{channel.avg_time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// 系统设置
function SystemContent() {
  return (
    <div className="space-y-4">
      <div className="bg-[#16161d] rounded-2xl border border-white/5 p-6">
        <h3 className="text-lg font-semibold mb-4">系统配置</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-white/5">
            <div>
              <div className="font-medium">用户注册</div>
              <div className="text-sm text-gray-400">允许新用户注册</div>
            </div>
            <button className="w-12 h-6 bg-cyan-500 rounded-full relative">
              <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
            </button>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-white/5">
            <div>
              <div className="font-medium">邮箱验证</div>
              <div className="text-sm text-gray-400">注册需验证邮箱</div>
            </div>
            <button className="w-12 h-6 bg-white/20 rounded-full relative">
              <div className="absolute left-1 top-1 w-4 h-4 bg-gray-400 rounded-full" />
            </button>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <div className="font-medium">内容审核</div>
              <div className="text-sm text-gray-400">AI自动审核生成内容</div>
            </div>
            <button className="w-12 h-6 bg-cyan-500 rounded-full relative">
              <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
