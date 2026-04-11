/**
 * 漫AI - Zustand状态管理
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  balance: number
  level: 'free' | 'basic' | 'pro' | 'enterprise'
}

interface Task {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  video_url?: string
  error?: string
  created_at: string
}

interface GenerationState {
  mode: 'fast' | 'balanced' | 'premium'
  prompt: string
  negativePrompt: string
  duration: 5 | 10
  aspectRatio: '16:9' | '9:16' | '1:1'
  resolution: '480p' | '720p' | '1080p'
  referenceImage: File | null
  referenceImagePreview: string
}

interface AppState {
  // 用户
  user: User | null
  token: string | null
  isAuthenticated: boolean
  
  // 生成状态
  generation: GenerationState
  currentTask: Task | null
  tasks: Task[]
  
  // UI状态
  isGenerating: boolean
  showBalanceModal: boolean
  
  // Actions - 用户
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void
  
  // Actions - 生成
  setGenerationParam: <K extends keyof GenerationState>(
    key: K,
    value: GenerationState[K]
  ) => void
  resetGeneration: () => void
  setCurrentTask: (task: Task | null) => void
  addTask: (task: Task) => void
  updateTask: (taskId: string, updates: Partial<Task>) => void
  setIsGenerating: (isGenerating: boolean) => void
  
  // Actions - UI
  setShowBalanceModal: (show: boolean) => void
}

const initialGenerationState: GenerationState = {
  mode: 'balanced',
  prompt: '',
  negativePrompt: '',
  duration: 5,
  aspectRatio: '16:9',
  resolution: '720p',
  referenceImage: null,
  referenceImagePreview: '',
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // 初始状态
      user: null,
      token: null,
      isAuthenticated: false,
      generation: initialGenerationState,
      currentTask: null,
      tasks: [],
      isGenerating: false,
      showBalanceModal: false,
      
      // Actions - 用户
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      
      // Actions - 生成
      setGenerationParam: (key, value) =>
        set((state) => ({
          generation: { ...state.generation, [key]: value },
        })),
      resetGeneration: () => set({ generation: initialGenerationState }),
      setCurrentTask: (task) => set({ currentTask: task }),
      addTask: (task) =>
        set((state) => ({ tasks: [task, ...state.tasks] })),
      updateTask: (taskId, updates) =>
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.task_id === taskId ? { ...t, ...updates } : t
          ),
          currentTask:
            state.currentTask?.task_id === taskId
              ? { ...state.currentTask, ...updates }
              : state.currentTask,
        })),
      setIsGenerating: (isGenerating) => set({ isGenerating }),
      
      // Actions - UI
      setShowBalanceModal: (showBalanceModal) => set({ showBalanceModal }),
    }),
    {
      name: 'manai-storage',
      partialize: (state) => ({
        token: state.token,
      }),
    }
  )
)
