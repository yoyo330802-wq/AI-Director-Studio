/**
 * SEO Configuration
 * Sprint 4: S4-F5 SEO优化
 */

// 站点基本信息
export const siteConfig = {
  name: '漫AI - 动漫创作Token平台',
  title: '漫AI - AI视频生成，比官网便宜30%',
  description: '漫AI是国内领先的AI视频生成平台，支持文生视频、图生视频多种模式。比官网便宜30%，支持Wan2.1、Vidu、可灵等多种模型。',
  keywords: 'AI视频生成,文生视频,图生视频,Wan2.1,Vidu,可灵,AI动漫,AI创作',
  url: 'https://manai.com',
  locale: 'zh_CN',
  social: {
    weibo: '@漫AI',
    twitter: '@manai_video',
  }
}

// 页面SEO配置
export const pageSEO = {
  '/': {
    title: '漫AI - AI视频生成，比官网便宜30%',
    description: '国内领先的AI视频生成平台，支持多种AI模型，文生视频、图生视频一键创作',
    keywords: 'AI视频生成,文生视频,图生视频,Wan2.1,Vidu,可灵'
  },
  '/gallery': {
    title: '作品广场 - 漫AI',
    description: '浏览漫AI社区的精彩AI视频作品，获取创作灵感',
    keywords: 'AI视频作品,作品广场,AI创作案例'
  },
  '/templates': {
    title: '提示词模板 - 漫AI',
    description: '精选AI视频生成提示词模板，快速开始你的创作',
    keywords: 'AI提示词,视频模板,创作模板'
  },
  '/studio': {
    title: '创作工作室 - 漫AI',
    description: '使用AI视频生成工具，创作你的专属视频',
    keywords: 'AI创作,视频生成工具,文生视频'
  },
  '/pricing': {
    title: '定价套餐 - 漫AI',
    description: '灵活的AI视频生成套餐，比官网便宜30%',
    keywords: 'AI视频价格,套餐,Token充值'
  },
  '/about': {
    title: '关于我们 - 漫AI',
    description: '了解漫AI团队和技术',
    keywords: '漫AI,关于我们,AI视频技术'
  },
  '/help': {
    title: '帮助中心 - 漫AI',
    description: '常见问题和使用教程',
    keywords: '帮助中心,FAQ,使用教程'
  },
  '/privacy': {
    title: '隐私政策 - 漫AI',
    description: '漫AI隐私政策说明',
    keywords: '隐私政策'
  },
  '/terms': {
    title: '服务条款 - 漫AI',
    description: '漫AI服务条款',
    keywords: '服务条款,用户协议'
  }
}

// 生成完整标题
export function generateTitle(pageTitle?: string): string {
  if (!pageTitle) return siteConfig.title
  return `${pageTitle} | ${siteConfig.name}`
}

// 生成完整描述
export function generateDescription(pageDescription?: string): string {
  if (!pageDescription) return siteConfig.description
  return pageDescription
}

// Open Graph标签
export function generateOGTags(page?: string) {
  const config = page ? pageSEO[page as keyof typeof pageSEO] : null
  const title = config?.title || siteConfig.title
  const description = config?.description || siteConfig.description
  
  return {
    title,
    description,
    url: `${siteConfig.url}${page || '/'}`,
    site_name: siteConfig.name,
    locale: siteConfig.locale,
    type: page === '/' ? 'website' : 'article',
    // 图片
    images: [
      {
        url: `${siteConfig.url}/og-image.jpg`,
        width: 1200,
        height: 630,
        alt: title,
      }
    ],
    // Twitter
    twitter: {
      card: 'summary_large_image',
      site: siteConfig.social.twitter,
      title,
      description,
      image: `${siteConfig.url}/og-image.jpg`,
    }
  }
}

// 结构化数据 (JSON-LD)
export function generateJSONLD(page?: string) {
  const baseLD = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: siteConfig.name,
    url: siteConfig.url,
    description: siteConfig.description,
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${siteConfig.url}/search?q={search_term_string}`
      },
      'query-input': 'required name=search_term_string'
    }
  }
  
  if (page === '/') {
    return {
      ...baseLD,
      '@type': 'WebSite',
      // 主页特定
    }
  }
  
  if (page === '/pricing') {
    return {
      ...baseLD,
      '@type': 'WebPage',
      name: '定价页面',
      // 定价页特定
    }
  }
  
  return baseLD
}
