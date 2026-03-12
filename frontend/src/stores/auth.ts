import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import type { LoginRequest, RegisterRequest, UserResponse } from '@/api/types'
import { useToastStore } from './toast'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserResponse | null>(null)
  const accessToken = ref(localStorage.getItem(ACCESS_TOKEN_KEY) || '')
  const refreshToken = ref(localStorage.getItem(REFRESH_TOKEN_KEY) || '')

  const isAuthenticated = computed(() => !!accessToken.value)

  function saveTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }

  function clearTokens() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  async function register(data: RegisterRequest) {
    const created = await authApi.register(data)
    useToastStore().show('Регистрация успешна! Войдите в аккаунт.', 'success')
    return created
  }

  async function login(data: LoginRequest) {
    const tokens = await authApi.login(data)
    saveTokens(tokens.access_token, tokens.refresh_token)
    await fetchUser()
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const tokens = await authApi.refreshTokens({
        refresh_token: refreshToken.value,
      })
      saveTokens(tokens.access_token, tokens.refresh_token)
      return true
    } catch {
      clearTokens()
      return false
    }
  }

  async function fetchUser() {
    if (!accessToken.value) return
    try {
      user.value = await authApi.getMe(accessToken.value)
    } catch {
      user.value = null
    }
  }

  async function logout() {
    if (refreshToken.value) {
      try {
        await authApi.logout({ refresh_token: refreshToken.value })
      } catch {
        /* ignore logout errors */
      }
    }
    clearTokens()
  }

  async function init() {
    if (!accessToken.value) return
    try {
      await fetchUser()
    } catch {
      const ok = await refresh()
      if (ok) await fetchUser()
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    register,
    login,
    refresh,
    fetchUser,
    logout,
    init,
  }
})
