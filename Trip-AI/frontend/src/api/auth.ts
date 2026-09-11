import http from './http'
import type { TokenResponse, User } from '@/types'

export async function register(data: { email: string; username: string; password: string }): Promise<TokenResponse> {
  const res = await http.post('/auth/register', data)
  return res.data
}

export async function login(data: { email: string; password: string }): Promise<TokenResponse> {
  const res = await http.post('/auth/login', data)
  return res.data
}

export async function fetchMe(): Promise<User> {
  const res = await http.get('/auth/me')
  return res.data
}
