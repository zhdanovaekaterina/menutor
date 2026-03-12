import axios from 'axios'
import type {
  LoginRequest,
  RegisterRequest,
  RefreshRequest,
  TokenResponse,
  UpdateProfileRequest,
  UserResponse,
} from './types'

const authApi = axios.create({ baseURL: '/api/auth' })

export const register = (data: RegisterRequest) =>
  authApi.post<UserResponse>('/register', data).then((r) => r.data)

export const login = (data: LoginRequest) =>
  authApi.post<TokenResponse>('/login', data).then((r) => r.data)

export const refreshTokens = (data: RefreshRequest) =>
  authApi.post<TokenResponse>('/refresh', data).then((r) => r.data)

export const logout = (data: RefreshRequest) => authApi.post('/logout', data)

export const getMe = (accessToken: string) =>
  authApi
    .get<UserResponse>('/me', {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    .then((r) => r.data)

export const updateMe = (accessToken: string, data: UpdateProfileRequest) =>
  authApi
    .patch<UserResponse>('/me', data, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    .then((r) => r.data)
