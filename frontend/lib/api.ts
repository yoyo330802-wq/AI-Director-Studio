/**
 * 漫AI - API客户端
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

// 本地开发: 通过 Next.js rewrite 代理
// 生产: 直接请求
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.token = null
          if (typeof window !== 'undefined') {
            localStorage.removeItem('token')
          }
        }
        return Promise.reject(error)
      }
    )
  }

  setToken(token: string | null) {
    this.token = token
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('token', token)
      } else {
        localStorage.removeItem('token')
      }
    }
  }

  getToken(): string | null {
    if (this.token) return this.token
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token')
    }
    return null
  }

  // ============ 认证相关 ============

  async register(name: string, email: string, password: string) {
    const response = await this.client.post('/v1/auth/register', {
      name,
      email,
      password,
    })
    return response.data
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/v1/auth/login', {
      email,
      password,
    })
    if (response.data.access_token) {
      this.setToken(response.data.access_token)
    }
    return response.data
  }

  async logout() {
    this.setToken(null)
  }

  // ============ 用户相关 ============

  async getCurrentUser() {
    const response = await this.client.get('/v1/users/me')
    return response.data
  }

  async getBalance() {
    const response = await this.client.get('/v1/users/me')
    return { balance: response.data.token_balance }
  }

  // ============ 生成相关 ============

  async createTask(params: {
    quality_mode: string  // 'cost' | 'balanced' | 'quality'
    prompt: string
    negative_prompt?: string
    duration?: 5 | 10
    aspect_ratio?: '16:9' | '9:16' | '1:1'
    resolution?: '480p' | '720p' | '1080p'
    image_url?: string
  }) {
    const response = await this.client.post('/v1/generate', params)
    return response.data
  }

  async getTaskStatus(taskId: string) {
    const response = await this.client.get(`/v1/generate/${taskId}`)
    return response.data
  }

  async cancelTask(taskId: string) {
    const response = await this.client.post(`/v1/generate/${taskId}/cancel`)
    return response.data
  }

  async previewRoute(mode: string, duration: number) {
    const response = await this.client.get('/v1/generate/route/preview', {
      params: { mode, duration },
    })
    return response.data
  }

  // ============ 计费相关 ============

  async recharge(amount: number, paymentMethod: 'alipay' | 'wechat') {
    const response = await this.client.post('/v1/bill/recharge', {
      amount,
      payment_method: paymentMethod,
    })
    return response.data
  }

  async getTransactions(limit = 20) {
    const response = await this.client.get('/v1/bill/transactions', {
      params: { limit },
    })
    return response.data
  }

  async getPackages() {
    const response = await this.client.get('/v1/bill/packages')
    return response.data
  }

  // 通用方法
  async get<T = any>(url: string, config?: any): Promise<T> {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.post(url, data, config)
    return response.data
  }
}

export const api = new ApiClient()
export default api
