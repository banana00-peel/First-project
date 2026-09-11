// ---------- 表单 ----------
export interface TripFormData {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text: string
}

// ---------- 计划结构（与后端 schema 对应） ----------
export interface Location {
  name: string
  address?: string
  longitude: number
  latitude: number
}

export interface Attraction {
  name: string
  description?: string
  address?: string
  location?: Location
  suggested_duration?: string
  image_url?: string
}

export interface Meal {
  name: string
  description?: string
  cuisine?: string
  price_range?: string
}

export interface Hotel {
  name: string
  address?: string
  price_range?: string
  rating?: string
  location?: Location
}

export interface RouteSegment {
  from_name?: string
  to_name?: string
  mode?: string // walking / driving / transit
  distance_m?: number
  duration_s?: number
  summary?: string
  steps?: string[]
}

export interface WeatherInfo {
  date: string
  weather?: string
  temperature?: string
  wind?: string
  humidity?: string
}

export interface Budget {
  total?: string
  breakdown?: Record<string, unknown>
}

export interface DayPlan {
  day: number
  date?: string
  title?: string
  attractions: Attraction[]
  meals: Meal[]
  hotel?: Hotel
  transportation_tips?: string
  routes?: RouteSegment[]
  notes?: string
}

export interface TripPlan {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  overview?: string
  days: DayPlan[]
  weather: WeatherInfo[]
  budget?: Budget
  tips: string[]
}

export interface PlanResponse {
  success: boolean
  message: string
  data?: TripPlan
}

// ---------- 行程列表 / 详情 ----------
export interface TripSummary {
  id: number
  city: string
  start_date: string
  end_date: string
  travel_days: number
  status: string
  created_at: string
}

export interface TripDetail extends TripSummary {
  transportation: string
  accommodation: string
  preferences: string[]
  free_text: string
  plan: TripPlan
}

// ---------- 认证 ----------
export interface User {
  id: number
  email: string
  username: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

// ---------- 分享 ----------
export interface ShareLinkOut {
  token: string
  url: string
  expires_at?: string | null
}

export interface SharedTrip {
  city: string
  start_date: string
  end_date: string
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text: string
  plan: TripPlan
  shared_at?: string
}
