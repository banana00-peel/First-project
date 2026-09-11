<template>
  <div class="trip-map">
    <div v-if="!ready" class="map-placeholder">
      <a-spin />
      <span>地图加载中...</span>
    </div>
    <div ref="mapEl" class="map-canvas" :style="{ display: ready ? 'block' : 'none' }"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import type { Attraction } from '@/types'

declare global {
  interface Window {
    _AMapSecurityConfig?: { securityJsCode: string }
    AMap?: any
  }
}

const props = defineProps<{
  points: Attraction[]
  dayRoutes?: Attraction[][]
}>()

const mapEl = ref<HTMLElement | null>(null)
const ready = ref(false)
let map: any = null
let markers: any[] = []
let polylines: any[] = []

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`)
    if (existing) {
      resolve()
      return
    }
    const s = document.createElement('script')
    s.src = src
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('地图脚本加载失败'))
    document.head.appendChild(s)
  })
}

async function initMap() {
  const key = import.meta.env.VITE_AMAP_WEB_JS_KEY
  if (!key) {
    ready.value = true
    return
  }
  try {
    await loadScript(`https://webapi.amap.com/maps?v=2.0&key=${key}`)
    await new Promise((r) => setTimeout(r, 200))
    if (!window.AMap || !mapEl.value) return
    map = new window.AMap.Map(mapEl.value, { zoom: 11 })
    ready.value = true
    renderMarkers()
  } catch (e) {
    console.error(e)
    ready.value = true
  }
}

function renderMarkers() {
  if (!map) return
  markers.forEach((m) => m.remove())
  markers = []
  const valid = props.points.filter((p) => p.location && p.location.longitude && p.location.latitude)
  valid.forEach((p) => {
    const marker = new window.AMap.Marker({
      position: [p.location!.longitude, p.location!.latitude],
      title: p.name,
    })
    marker.setMap(map)
    markers.push(marker)
  })
  if (valid.length) {
    map.setFitView(markers)
  }
  renderPolylines()
}

function renderPolylines() {
  polylines.forEach((p) => p.setMap(null))
  polylines = []
  if (!map || !props.dayRoutes) return
  const colors = ['#667eea', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1']
  props.dayRoutes.forEach((day, i) => {
    if (!day || day.length < 2) return
    const path = day.map((a) => [a.location!.longitude, a.location!.latitude])
    const polyline = new window.AMap.Polyline({
      path,
      strokeColor: colors[i % colors.length],
      strokeWeight: 4,
      strokeOpacity: 0.7,
    })
    polyline.setMap(map)
    polylines.push(polyline)
  })
}

watch(() => props.points, renderMarkers, { deep: true })
watch(() => props.dayRoutes, renderPolylines, { deep: true })

onMounted(initMap)
onBeforeUnmount(() => {
  if (map) map.destroy()
})
</script>

<style scoped>
.trip-map {
  width: 100%;
  height: 100%;
  min-height: 320px;
  border-radius: 12px;
  overflow: hidden;
}
.map-canvas {
  width: 100%;
  height: 100%;
  min-height: 320px;
}
.map-placeholder {
  width: 100%;
  height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #f0f2f5;
  color: #999;
}
</style>
