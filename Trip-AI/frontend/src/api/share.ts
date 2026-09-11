import http from './http'
import type { SharedTrip, ShareLinkOut } from '@/types'

export async function createShare(tripId: number, expiresInDays?: number): Promise<ShareLinkOut> {
  const res = await http.post(`/share/trips/${tripId}`, { expires_in_days: expiresInDays })
  return res.data
}

export async function listLinks(tripId: number): Promise<ShareLinkOut[]> {
  const res = await http.get(`/share/trips/${tripId}/links`)
  return res.data
}

export async function getSharedTrip(token: string): Promise<SharedTrip> {
  const res = await http.get(`/share/${token}`)
  return res.data
}
