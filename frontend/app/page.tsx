import Link from 'next/link'
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/studio')
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-pink-500">
            漫AI
          </span>
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          动漫创作Token平台 - 比官网便宜30%
        </p>
        <Link
          href="/studio"
          className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold rounded-full hover:shadow-lg transition-all"
        >
          立即开始创作
          <span>→</span>
        </Link>
      </div>
    </div>
  )
}
