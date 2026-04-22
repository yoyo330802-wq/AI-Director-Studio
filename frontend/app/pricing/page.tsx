'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { 
  Check, Zap, Crown, Building2, Sparkles,
  CreditCard, Wallet, ArrowRight, Star,
  Shield, Clock, HeadphonesIcon, Video
} from 'lucide-react'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { cn, formatCurrency } from '@/lib/utils'

// 套餐配置（备用）
const DEFAULT_PACKAGES = [
  {
    id: 1,
    name: '体验版',
    level: 'L1_TRIAL',
    price: 0,
    original_price: 0,
    video_minutes: 5,
    duration_days: 0,
    features: [
      '5分钟创作额度',
      '基础生成模式',
      '标准生成速度',
      '720p输出',
      '社区作品浏览',
    ],
    not_features: [
      '无优先队列',
      '无专属客服',
    ],
    is_active: true,
    is_recommended: false,
  },
  {
    id: 2,
    name: '创作者',
    level: 'L2_CREATOR',
    price: 39,
    original_price: 59,
    video_minutes: 60,
    duration_days: 30,
    features: [
      '60分钟创作额度',
      '全模式支持',
      '优先生成队列',
      '1080p输出',
      '无水印下载',
      'API调用权限',
      '邮件客服支持',
    ],
    not_features: [
      '无专属客服',
    ],
    is_active: true,
    is_recommended: true,
  },
  {
    id: 3,
    name: '工作室',
    level: 'L3_STUDIO',
    price: 199,
    original_price: 299,
    video_minutes: 300,
    duration_days: 30,
    features: [
      '300分钟创作额度',
      '全模式支持',
      '极速优先队列',
      '1080p输出',
      '无水印下载',
      '完整API权限',
      '批量生成',
      '专属客服',
    ],
    not_features: [],
    is_active: true,
    is_recommended: false,
  },
  {
    id: 4,
    name: '企业版',
    level: 'L4_ENTERPRISE',
    price: 9999,
    original_price: 0,
    video_minutes: 99999,
    duration_days: 365,
    features: [
      '无限创作额度',
      '全模式支持',
      '专属GPU通道',
      '4K输出',
      '无水印下载',
      '完整API权限',
      '无限批量生成',
      '7x24专属客服',
      '定制化服务',
      'SLA保障',
    ],
    not_features: [],
    is_active: true,
    is_recommended: false,
  },
]

const LEVEL_CONFIG = {
  L1_TRIAL: { icon: Zap, color: 'from-gray-500 to-gray-600', label: '体验版' },
  L2_CREATOR: { icon: Sparkles, color: 'from-blue-500 to-purple-500', label: '创作者' },
  L3_STUDIO: { icon: Crown, color: 'from-amber-500 to-orange-500', label: '工作室' },
  L4_ENTERPRISE: { icon: Building2, color: 'from-green-500 to-emerald-500', label: '企业版' },
}

interface Package {
  id: number
  name: string
  level: string
  price: number
  original_price: number | null
  video_minutes: number
  duration_days: number
  features: string[]
  not_features: string[]
  priority_queue: boolean
  no_watermark: boolean
  api_access: boolean
  batch_generation: boolean
  dedicated_support: boolean
  is_active: boolean
  is_recommended: boolean
}

export default function PricingPage() {
  const router = useRouter()
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [selectedPackage, setSelectedPackage] = useState<number | null>(null)

  // 获取套餐列表
  const { data, isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: () => api.get('/v1/payments/packages'),
    staleTime: 5 * 60 * 1000,
  })

  const packages: Package[] = data || DEFAULT_PACKAGES

  // 选择套餐
  const handleSelectPackage = async (pkg: Package) => {
    setSelectedPackage(pkg.id)
    
    try {
      // 创建订单
      const order = await api.post('/v1/payments/create', {
        package_id: pkg.id,
        payment_method: 'alipay',
      })
      
      // 跳转到支付页面或显示支付二维码
      if (order.pay_url) {
        window.location.href = order.pay_url
      } else {
        toast.success('订单创建成功')
        router.push('/dashboard?tab=orders')
      }
    } catch (error) {
      toast.error('创建订单失败，请重试')
      setSelectedPackage(null)
    }
  }

  // 计算年付折扣
  const getYearlyPrice = (price: number) => {
    if (price === 0) return 0
    return Math.round(price * 10) // 年付8折
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* 头部 */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 via-purple-500/10 to-pink-500/20" />
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-cyan-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 py-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              选择您的创作方案
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              灵活的定价方案，满足不同创作需求
            </p>
            
            {/* 计费切换 */}
            <div className="inline-flex items-center bg-white/5 rounded-full p-1">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={cn(
                  "px-6 py-2 rounded-full text-sm font-medium transition-all",
                  billingCycle === 'monthly'
                    ? "bg-gradient-to-r from-cyan-500 to-purple-500 text-white"
                    : "text-gray-400 hover:text-white"
                )}
              >
                月付
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={cn(
                  "px-6 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2",
                  billingCycle === 'yearly'
                    ? "bg-gradient-to-r from-cyan-500 to-purple-500 text-white"
                    : "text-gray-400 hover:text-white"
                )}
              >
                年付
                <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs">
                  省20%
                </span>
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* 套餐列表 */}
      <div className="max-w-7xl mx-auto px-4 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {packages.map((pkg, index) => {
            const levelInfo = LEVEL_CONFIG[pkg.level as keyof typeof LEVEL_CONFIG]
            const IconComponent = levelInfo?.icon || Zap
            const currentPrice = billingCycle === 'yearly' && pkg.price > 0 
              ? getYearlyPrice(pkg.price) 
              : pkg.price
            const isSelected = selectedPackage === pkg.id
            
            return (
              <motion.div
                key={pkg.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "relative bg-white/5 rounded-2xl border transition-all duration-300",
                  pkg.is_recommended 
                    ? "border-cyan-500/50 shadow-lg shadow-cyan-500/10" 
                    : "border-white/10 hover:border-white/20"
                )}
              >
                {/* 推荐标签 */}
                {pkg.is_recommended && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full text-sm font-medium">
                    最受欢迎
                  </div>
                )}
                
                <div className="p-6">
                  {/* 标题 */}
                  <div className="text-center mb-6">
                    <div className={cn(
                      "w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br flex items-center justify-center",
                      levelInfo?.color || 'from-gray-500 to-gray-600'
                    )}>
                      <IconComponent className="w-7 h-7 text-white" />
                    </div>
                    <h3 className="text-xl font-bold">{pkg.name}</h3>
                    <p className="text-sm text-gray-400 mt-1">
                      {pkg.duration_days > 0 ? `${pkg.duration_days}天` : '永久'}
                    </p>
                  </div>
                  
                  {/* 价格 */}
                  <div className="text-center mb-6">
                    <div className="flex items-end justify-center gap-1">
                      <span className="text-4xl font-bold">
                        {currentPrice === 0 ? '免费' : `¥${currentPrice}`}
                      </span>
                      {currentPrice > 0 && (
                        <span className="text-gray-400 mb-1">
                          /{billingCycle === 'yearly' ? '年' : '月'}
                        </span>
                      )}
                    </div>
                    {pkg.original_price && pkg.original_price > currentPrice && (
                      <div className="text-sm text-gray-500 line-through mt-1">
                        ¥{pkg.original_price}/{billingCycle === 'yearly' ? '年' : '月'}
                      </div>
                    )}
                  </div>
                  
                  {/* 额度 */}
                  <div className="text-center py-4 border-y border-white/10 mb-6">
                    <div className="text-3xl font-bold text-cyan-400">
                      {pkg.video_minutes >= 99999 ? '∞' : pkg.video_minutes}
                    </div>
                    <div className="text-sm text-gray-400">创作分钟数</div>
                  </div>
                  
                  {/* 特性列表 */}
                  <div className="space-y-3 mb-6">
                    {pkg.features.map((feature, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-300">{feature}</span>
                      </div>
                    ))}
                    {pkg.not_features?.map((feature, i) => (
                      <div key={i} className="flex items-start gap-2 opacity-50">
                        <div className="w-4 h-4 mt-0.5 flex-shrink-0 flex items-center justify-center">
                          <div className="w-3 h-0.5 bg-gray-500" />
                        </div>
                        <span className="text-sm text-gray-500">{feature}</span>
                      </div>
                    ))}
                  </div>
                  
                  {/* 按钮 */}
                  <button
                    onClick={() => handleSelectPackage(pkg)}
                    disabled={isSelected || !pkg.is_active}
                    className={cn(
                      "w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2",
                      pkg.is_recommended
                        ? "bg-gradient-to-r from-cyan-500 to-purple-500 hover:opacity-90"
                        : "bg-white/10 hover:bg-white/20",
                      (isSelected || !pkg.is_active) && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {isSelected ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        处理中...
                      </>
                    ) : pkg.price === 0 ? (
                      '免费开始'
                    ) : (
                      <>
                        立即购买
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
                
                {/* 企业版特殊标识 */}
                {pkg.level === 'L4_ENTERPRISE' && (
                  <div className="absolute -right-2 top-20">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* FAQ */}
        <div className="mt-20">
          <h2 className="text-2xl font-bold text-center mb-10">
            常见问题
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="font-semibold mb-2">额度用完怎么办？</h4>
              <p className="text-sm text-gray-400">
                可以单独购买分钟包，或升级到更高套餐。企业版用户享无限额度。
              </p>
            </div>
            
            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="font-semibold mb-2">可以退款吗？</h4>
              <p className="text-sm text-gray-400">
                7天内无理由退款，VIP会员可申请延长至30天。
              </p>
            </div>
            
            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="font-semibold mb-2">如何获取API权限？</h4>
              <p className="text-sm text-gray-400">
                创作者及以上套餐用户可在个人中心获取API Key。
              </p>
            </div>
            
            <div className="bg-white/5 rounded-xl p-6">
              <h4 className="font-semibold mb-2">支持哪些支付方式？</h4>
              <p className="text-sm text-gray-400">
                支持支付宝、微信支付、银行卡等主流支付方式。
              </p>
            </div>
          </div>
        </div>

        {/* 底部CTA */}
        <div className="mt-20 text-center">
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-white/5 rounded-full">
            <span className="text-gray-400">还有疑问？</span>
            <a href="/contact" className="text-cyan-400 hover:text-cyan-300">
              联系客服
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
