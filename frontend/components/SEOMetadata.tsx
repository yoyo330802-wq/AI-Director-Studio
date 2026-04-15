'use client'

/**
 * SEO Metadata Component
 * Sprint 4: S4-F5 SEO优化
 * 
 * 在页面中使用:
 * <SEOMetadata page="/gallery" />
 */

import { useEffect } from 'react'
import Head from 'next/head'
import { siteConfig, generateTitle, generateDescription, generateOGTags } from '@/lib/seo'

interface SEOMetadataProps {
  page?: string
  title?: string
  description?: string
  image?: string
  noIndex?: boolean
}

export default function SEOMetadata({
  page,
  title,
  description,
  image,
  noIndex = false
}: SEOMetadataProps) {
  const pageTitle = title || generateTitle(page ? undefined : undefined)
  const pageDescription = description || generateDescription()
  const ogTags = generateOGTags(page)
  const canonicalUrl = `${siteConfig.url}${page || '/'}`
  const ogImage = image || `${siteConfig.url}/og-image.jpg`

  useEffect(() => {
    // 更新文档标题
    document.title = pageTitle
    
    // 设置 meta description
    const metaDesc = document.querySelector('meta[name="description"]')
    if (metaDesc) {
      metaDesc.setAttribute('content', pageDescription)
    }
  }, [pageTitle, pageDescription])

  return (
    <Head>
      {/* 基础SEO */}
      <title>{pageTitle}</title>
      <meta name="description" content={pageDescription} />
      <meta name="keywords" content={siteConfig.keywords} />
      <meta name="author" content="漫AI" />
      <link rel="canonical" href={canonicalUrl} />
      
      {/* 搜索引擎 */}
      <meta name="robots" content={noIndex ? 'noindex,nofollow' : 'index,follow'} />
      <meta name="googlebot" content="index,follow" />
      <meta name="Baiduspider" content="index,follow" />
      
      {/* Open Graph */}
      <meta property="og:type" content={ogTags.type} />
      <meta property="og:title" content={pageTitle} />
      <meta property="og:description" content={pageDescription} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:site_name" content={ogTags.site_name} />
      <meta property="og:locale" content={ogTags.locale} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      
      {/* Twitter Card */}
      <meta name="twitter:card" content={ogTags.twitter.card} />
      <meta name="twitter:site" content={ogTags.twitter.site} />
      <meta name="twitter:title" content={pageTitle} />
      <meta name="twitter:description" content={pageDescription} />
      <meta name="twitter:image" content={ogImage} />
      
      {/* 移动端 */}
      <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
      <meta name="theme-color" content="#0a0a0f" />
      
      {/* 移动端图标 */}
      <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      
      {/* 网站验证 */}
      <meta name="baidu-site-verification" content="YOUR_BAIDU_CODE" />
      <meta name="google-site-verification" content="YOUR_GOOGLE_CODE" />
    </Head>
  )
}
