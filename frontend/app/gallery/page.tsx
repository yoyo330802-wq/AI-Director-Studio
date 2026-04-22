'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { 
  Search, Filter, Grid, List, Heart, Share2, 
  Play, Eye, MoreVertical, Tag, User, Clock,
  TrendingUp, Star, Flame, X, ChevronDown
} from 'lucide-react'
import { toast } from 'sonner'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

// 分类
const CATEGORIES = [
  { id: 'all', name: '全部', icon: Grid },
  { id: 'anime', name: '动漫', icon: Star },
  { id: '3d', name: '3D', icon: TrendingUp },
  { id: 'realistic', name: '写实', icon: Eye },
  { id: 'abstract', name: '抽象', icon: Flame },
  { id: 'music', name: '音乐', icon: Play },
]

// 排序选项
const SORT_OPTIONS = [
  { id: 'latest', name: '最新' },
  { id: 'popular', name: '热门' },
  { id: 'trending', name: '趋势' },
]

interface Video {
  id: number
  title: string
  description: string
  video_url: string
  cover_url: string
  thumbnail_url: string
  duration: number
  width: number
  height: number
  view_count: number
  like_count: number
  share_count: number
  is_featured: boolean
  is_ai_recommended: boolean
  tags: string[]
  category: string
  created_at: string
  user: {
    id: number
    username: string
    nickname: string
    avatar: string
  }
}

export default function GalleryPage() {
  const [category, setCategory] = useState('all')
  const [sortBy, setSortBy] = useState('latest')
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'masonry' | 'list'>('masonry')
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [page, setPage] = useState(1)
  
  // 无限滚动加载
  const observerRef = useRef<IntersectionObserver | null>(null)
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // 获取视频列表 - 无限滚动
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch
  } = useInfiniteQuery({
    queryKey: ['videos', category, sortBy, searchQuery],
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams({
        page: pageParam.toString(),
        page_size: '20',
        sort: sortBy,
      })
      if (category !== 'all') {
        params.append('category', category)
      }
      if (searchQuery) {
        params.append('search', searchQuery)
      }
      return api.get(`/v1/videos?${params}`)
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.total_pages) {
        return lastPage.page + 1
      }
      return undefined
    },
    initialPageParam: 1,
  })

  const videos: Video[] = data?.pages.flatMap(page => page.items || []) || []

  // 无限滚动监听
  const handleObserver = useCallback((entries: IntersectionObserverEntry[]) => {
    const [target] = entries
    if (target.isIntersecting && hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [fetchNextPage, hasNextPage, isFetchingNextPage])

  useEffect(() => {
    const element = loadMoreRef.current
    if (!element) return
    
    observerRef.current = new IntersectionObserver(handleObserver, {
      threshold: 0.1,
      rootMargin: '100px'
    })
    observerRef.current.observe(element)
    
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [handleObserver])

  // 格式化时长
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 格式化数字
  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k'
    }
    return num.toString()
  }

  // 格式化时间
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return '今天'
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    if (days < 30) return `${Math.floor(days / 7)}周前`
    if (days < 365) return `${Math.floor(days / 30)}月前`
    return `${Math.floor(days / 365)}年前`
  }

  // 点赞
  const handleLike = async (videoId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/v1/videos/${videoId}/like`)
      toast.success('点赞成功')
      refetch()
    } catch (error) {
      toast.error('点赞失败')
    }
  }

  // 分享
  const handleShare = async (video: Video, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/video/${video.id}`)
      toast.success('链接已复制')
    } catch {
      toast.error('复制失败')
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* 头部 */}
      <div className="sticky top-0 z-40 bg-[#0a0a0f]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* 标题 */}
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                作品广场
              </h1>
              <p className="text-sm text-gray-400">发现AI创作的精彩视频</p>
            </div>

            {/* 搜索框 */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="搜索视频、标签、作者..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-cyan-400/50 transition-colors"
                />
              </div>
            </div>

            {/* 视图切换 */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('masonry')}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  viewMode === 'masonry' 
                    ? "bg-cyan-400/20 text-cyan-400" 
                    : "text-gray-400 hover:text-white"
                )}
                title="瀑布流"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  viewMode === 'grid' 
                    ? "bg-cyan-400/20 text-cyan-400" 
                    : "text-gray-400 hover:text-white"
                )}
                title="网格"
              >
                <Grid className="w-4 h-4" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  "p-2 rounded-lg transition-colors",
                  viewMode === 'list' 
                    ? "bg-cyan-400/20 text-cyan-400" 
                    : "text-gray-400 hover:text-white"
                )}
                title="列表"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 分类标签 */}
          <div className="flex items-center gap-2 mt-4 overflow-x-auto pb-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap",
                  category === cat.id
                    ? "bg-gradient-to-r from-cyan-500 to-purple-500 text-white shadow-lg shadow-cyan-500/25"
                    : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
                )}
              >
                <cat.icon className="w-4 h-4" />
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 主内容 */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* 排序和筛选 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {SORT_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => setSortBy(option.id)}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium transition-colors",
                  sortBy === option.id
                    ? "bg-white/10 text-white"
                    : "text-gray-400 hover:text-white"
                )}
              >
                {option.name}
              </button>
            ))}
          </div>
          
          <div className="text-sm text-gray-400">
            {videos.length}+ 个作品
          </div>
        </div>

        {/* 视频列表 */}
        {isLoading ? (
          <div className={viewMode === 'masonry' ? 'columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4' : 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'}>
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="aspect-video bg-white/5 rounded-xl animate-pulse"
              />
            ))}
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
              <Play className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-medium text-gray-400 mb-2">
              暂无作品
            </h3>
            <p className="text-sm text-gray-500">
              快去创作你的第一个AI视频吧！
            </p>
          </div>
        ) : viewMode === 'masonry' ? (
          /* 瀑布流布局 */
          <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="break-inside-avoid group relative bg-white/5 rounded-xl overflow-hidden hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => setSelectedVideo(video)}
              >
                {/* 封面 */}
                <div className="relative overflow-hidden">
                  <img
                    src={video.cover_url || video.thumbnail_url}
                    alt={video.title}
                    className="w-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                  />
                  
                  {/* 播放按钮 */}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <Play className="w-6 h-6 text-white ml-1" />
                    </div>
                  </div>
                  
                  {/* 时长 */}
                  <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/70 rounded text-xs">
                    {formatDuration(video.duration)}
                  </div>
                  
                  {/* 标签 */}
                  {video.is_featured && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full text-xs font-medium">
                      精选
                    </div>
                  )}
                </div>
                
                {/* 信息 */}
                <div className="p-3">
                  <h3 className="font-medium text-sm line-clamp-2 mb-2">
                    {video.title || '无标题'}
                  </h3>
                  
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      <span>{video.user?.nickname || video.user?.username}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {formatNumber(video.view_count)}
                      </span>
                      <button
                        onClick={(e) => handleLike(video.id, e)}
                        className="flex items-center gap-1 hover:text-rose-400 transition-colors"
                      >
                        <Heart className="w-3 h-3" />
                        {formatNumber(video.like_count)}
                      </button>
                    </div>
                  </div>
                  
                  {/* 标签 */}
                  {video.tags && video.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      {video.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 bg-white/5 rounded text-xs text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        ) : viewMode === 'grid' ? (
          /* 网格布局 */
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="group relative bg-white/5 rounded-xl overflow-hidden hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => setSelectedVideo(video)}
              >
                {/* 封面 */}
                <div className="aspect-video relative overflow-hidden">
                  <img
                    src={video.cover_url || video.thumbnail_url}
                    alt={video.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  
                  {/* 播放按钮 */}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <Play className="w-6 h-6 text-white ml-1" />
                    </div>
                  </div>
                  
                  {/* 时长 */}
                  <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/70 rounded text-xs">
                    {formatDuration(video.duration)}
                  </div>
                  
                  {/* 标签 */}
                  {video.is_featured && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-full text-xs font-medium">
                      精选
                    </div>
                  )}
                </div>
                
                {/* 信息 */}
                <div className="p-3">
                  <h3 className="font-medium text-sm line-clamp-2 mb-2">
                    {video.title || '无标题'}
                  </h3>
                  
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      <span>{video.user?.nickname || video.user?.username}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {formatNumber(video.view_count)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        {formatNumber(video.like_count)}
                      </span>
                    </div>
                  </div>
                  
                  {/* 标签 */}
                  {video.tags && video.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      {video.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 bg-white/5 rounded text-xs text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          /* 列表布局 */
          <div className="space-y-4">
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => setSelectedVideo(video)}
              >
                {/* 封面 */}
                <div className="w-48 h-28 relative rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={video.cover_url || video.thumbnail_url}
                    alt={video.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-1 right-1 px-1.5 py-0.5 bg-black/70 rounded text-xs">
                    {formatDuration(video.duration)}
                  </div>
                </div>
                
                {/* 信息 */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium mb-1 line-clamp-1">
                    {video.title || '无标题'}
                  </h3>
                  <p className="text-sm text-gray-400 line-clamp-2 mb-2">
                    {video.description}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {video.user?.nickname || video.user?.username}
                    </span>
                    <span>{formatTime(video.created_at)}</span>
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {formatNumber(video.view_count)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Heart className="w-3 h-3" />
                      {formatNumber(video.like_count)}
                    </span>
                  </div>
                </div>
                
                {/* 操作 */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleLike(video.id, e)}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <Heart className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleShare(video, e)}
                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  >
                    <Share2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* 加载更多 */}
        <div ref={loadMoreRef} className="py-8 text-center">
          {isFetchingNextPage && (
            <div className="flex items-center justify-center gap-2 text-gray-400">
              <div className="w-5 h-5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
              加载中...
            </div>
          )}
          {!hasNextPage && videos.length > 0 && (
            <p className="text-gray-500">— 已加载全部 {videos.length} 个作品 —</p>
          )}
        </div>
      </div>

      {/* 视频详情弹窗 */}
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
              className="bg-[#16161d] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="aspect-video bg-black relative">
                <video
                  src={selectedVideo.video_url}
                  controls
                  className="w-full h-full"
                  autoPlay
                />
                <button
                  onClick={() => setSelectedVideo(null)}
                  className="absolute top-4 right-4 p-2 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="p-6 max-h-[50vh] overflow-y-auto">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold mb-2">
                      {selectedVideo.title || '无标题'}
                    </h2>
                    <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
                      <span className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        {selectedVideo.user?.nickname || selectedVideo.user?.username}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatTime(selectedVideo.created_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {formatNumber(selectedVideo.view_count)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="w-4 h-4" />
                        {formatNumber(selectedVideo.like_count)}
                      </span>
                    </div>
                    
                    {selectedVideo.description && (
                      <p className="text-gray-400 mb-4">
                        {selectedVideo.description}
                      </p>
                    )}
                    
                    {selectedVideo.tags && selectedVideo.tags.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap">
                        {selectedVideo.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-3 py-1 bg-white/10 rounded-full text-sm"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handleLike(selectedVideo.id, e)}
                      className="flex items-center gap-2 px-4 py-2 bg-rose-500/20 text-rose-400 rounded-lg hover:bg-rose-500/30 transition-colors"
                    >
                      <Heart className="w-4 h-4" />
                      点赞
                    </button>
                    <button
                      onClick={(e) => handleShare(selectedVideo, e)}
                      className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                    >
                      <Share2 className="w-4 h-4" />
                      分享
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}