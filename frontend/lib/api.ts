/**
 * 漫AI - API客户端
 */
import axios, { AxiosInstance, AxiosError } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
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
          // Token过期，清除
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

  // ============ 用户相关 ============

  async register(username: string, email: string, password: string) {
    const response = await this.client.post('/v1/users/register', {
      username,
      email,
      password,
    })
    return response.data
  }

  async login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await this.client.post('/v1/users/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    this.setToken(response.data.access_token)
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/v1/users/me')
    return response.data
  }

  async getBalance() {
    const response = await this.client.get('/v1/users/balance')
    return response.data
  }

  // ============ 生成相关 ============

  async createTask(params: {
    mode: 'fast' | 'balanced' | 'premium'
    prompt: string
    negative_prompt?: string
    duration: 5 | 10
    aspect_ratio: '16:9' | '9:16' | '1:1'
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
}

export const api = new ApiClient()
export default api
