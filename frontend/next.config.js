/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'manai.com', 'vidu.cn', 'siliconflow.cn'],
  },
  async rewrites() {
    return [
      {
        // 代理API请求到后端
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        // 代理OpenAPI Schema到后端
        source: '/openapi.json',
        destination: 'http://localhost:8000/openapi.json',
      },
      {
        // 代理Swagger UI静态资源
        source: '/docs',
        destination: 'http://localhost:8000/docs',
      },
    ]
  },
}

module.exports = nextConfig
