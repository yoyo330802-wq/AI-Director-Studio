'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { 
  User, Video, CreditCard, Settings, Bell, Shield,
  Key, LogOut, ChevronRight, Copy, Check, 
  Zap, Clock, Play, Download, Trash2, Edit,
  Wallet, Crown, Star, Gift, TrendingUp
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

export default function DashboardPage() {
  const router = useRouter()
  const [activeMenu, setActiveMenu] = useState('overview')

  // 获取用户信息
  const { data: userData, isLoading } = useQuery<UserData>({
    queryKey: ['current-user'],
    queryFn: () => api.get('/v1/users/me'),
  })

  // 获取任务列表
  const { data: tasksData } = useQuery({
    queryKey: ['my-tasks'],
    queryFn: () => api.get('/v1/tasks?page=1&page_size=5'),
  })

  // 获取订单列表
  const { data: ordersData } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => api.get('/v1/orders?page=1&page_size=5'),
  })

  const user = userData
  const tasks = tasksData?.items || []
  const orders = ordersData?.items || []

  const menuComponents: Record<string, React.ReactNode> = {
    overview: <OverviewSection user={user} tasks={tasks} />,
    videos: <VideosSection />,
    orders: <OrdersSection orders={orders} />,
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
function OverviewSection({ user, tasks }: { user?: UserData, tasks: any[] }) {
  const router = useRouter()
  
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
            onClick={() => setActiveMenu('videos')}
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
            {tasks.map((task: any) => (
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
  return (
    <div className="bg-white/5 rounded-2xl p-6">
      <h3 className="text-lg font-semibold mb-4">我的作品</h3>
      <p className="text-gray-400">作品管理功能开发中...</p>
    </div>
  )
}

// 订单
function OrdersSection({ orders }: { orders: any[] }) {
  return (
    <div className="bg-white/5 rounded-2xl p-6">
      <h3 className="text-lg font-semibold mb-4">订单记录</h3>
      {orders.length === 0 ? (
        <div className="text-center py-8">
          <CreditCard className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p className="text-gray-400">暂无订单记录</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order: any) => (
            <div key={order.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl">
              <div>
                <div className="font-medium">订单 #{order.order_no}</div>
                <div className="text-sm text-gray-400">
                  {new Date(order.created_at).toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium">¥{order.actual_amount}</div>
                <span className={cn(
                  "text-sm",
                  order.status === 'paid' ? 'text-green-400' : 'text-gray-400'
                )}>
                  {order.status === 'paid' ? '已支付' : '待支付'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// 钱包
function WalletSection({ user }: { user?: UserData }) {
  const router = useRouter()

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
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"
                style={{ width: `${user?.video_quota ? (user.video_used / user.video_quota) * 100 : 0}%` }}
              />
            </div>
          </div>
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
    </div>
  )
}

// 设置
function SettingsSection() {
  const [copied, setCopied] = useState(false)

  const handleCopyApiKey = async () => {
    await navigator.clipboard.writeText('your-api-key-here')
    setCopied(true)
    toast.success('API Key已复制')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* 账户设置 */}
      <div className="bg-white/5 rounded-2xl p-6">
        <h3 className="text-lg font-semibold mb-4">账户设置</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-white/5">
            <div className="flex items-center gap-3">
              <User className="w-5 h-5 text-gray-400" />
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
          
          <div className="flex items-center justify-between py-3 border-b border-white/5">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-gray-400" />
              <div>
                <div className="font-medium">通知设置</div>
                <div className="text-sm text-gray-400">邮件/短信通知</div>
              </div>
            </div>
            <button className="p-2 hover:bg-white/10 rounded-lg">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-gray-400" />
              <div>
                <div className="font-medium">安全设置</div>
                <div className="text-sm text-gray-400">密码/两步验证</div>
              </div>
            </div>
            <button className="p-2 hover:bg-white/10 rounded-lg">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
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

// 辅助函数
function setActiveMenu(id: string) {
  // This would be handled by parent component
}
