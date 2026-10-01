import http from './http'
import type { TaskAcceptedResponse, TaskStatusResponse, TripDetail, TripFormData, TripPlan, TripSummary } from '@/types'

export async function generateTrip(data: TripFormData): Promise<TaskAcceptedResponse> {
  const res = await http.post('/trips/generate', data)
  return res.data
}

export async function getGenerateTask(taskId: string): Promise<TaskStatusResponse> {
  const res = await http.get(`/trips/generate/${taskId}`)
  return res.data
}

export async function saveTrip(data: TripFormData & { plan: TripPlan }): Promise<TripSummary> {
  const res = await http.post('/trips', data)
  return res.data
}

export async function listTrips(): Promise<TripSummary[]> {
  const res = await http.get('/trips')
  return res.data
}

export async function getTrip(id: number): Promise<TripDetail> {
  const res = await http.get(`/trips/${id}`)
  return res.data
}

export async function deleteTrip(id: number): Promise<{ success: boolean; message: string }> {
  const res = await http.delete(`/trips/${id}`)
  return res.data
}
