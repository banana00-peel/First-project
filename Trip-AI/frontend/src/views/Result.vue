<template>
  <div class="result-page">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <a-button @click="$router.push('/')">← 返回首页</a-button>
      <div class="actions" v-if="plan">
        <template v-if="!tripId">
          <a-button v-if="auth.isLoggedIn()" type="primary" :loading="saving" @click="handleSave">
            保存到我的行程
          </a-button>
          <a-button v-else @click="$router.push('/login')">登录后保存</a-button>
        </template>
        <template v-else>
          <a-button type="primary" @click="openShare">分享行程</a-button>
        </template>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <a-spin size="large" tip="加载中..." />
    </div>

    <template v-else-if="plan">
      <!-- 概览 -->
      <a-card class="block" :bordered="false">
        <div class="overview">
          <h1>🏙️ {{ plan.city }} 旅行计划</h1>
          <p class="meta">{{ plan.start_date }} ~ {{ plan.end_date }} · {{ plan.travel_days }} 天</p>
          <p v-if="plan.overview" class="desc">{{ plan.overview }}</p>
        </div>
      </a-card>

      <!-- 地图 -->
      <a-card class="block" :bordered="false" title="🗺️ 行程地图">
        <TripMap :points="allAttractions" :day-routes="dayRoutes" />
      </a-card>

      <!-- 天气 -->
      <a-card class="block" :bordered="false" title="🌤️ 天气预报" v-if="plan.weather.length">
        <div class="weather-grid">
          <div v-for="w in plan.weather" :key="w.date" class="weather-item">
            <div class="w-date">{{ w.date }}</div>
            <div class="w-weather">{{ w.weather }}</div>
            <div class="w-temp">{{ w.temperature }}</div>
          </div>
        </div>
      </a-card>

      <!-- 每日行程 -->
      <a-card
        class="block"
        :bordered="false"
        :title="`📅 每日行程`"
      >
        <a-timeline>
          <a-timeline-item v-for="day in plan.days" :key="day.day" color="#667eea">
            <div class="day-block">
              <div class="day-header">
                <span class="day-title">第 {{ day.day }} 天</span>
                <span class="day-date" v-if="day.date">{{ day.date }}</span>
              </div>
              <div v-if="day.title" class="day-subtitle">{{ day.title }}</div>

              <div v-if="day.attractions.length" class="day-section">
                <div class="sec-label">🎡 景点</div>
                <div class="attraction-list">
                  <div v-for="a in day.attractions" :key="a.name" class="attraction-item">
                    <div class="attr-name">
                      {{ a.name }}
                      <a-tag v-if="a.suggested_duration" color="blue">{{ a.suggested_duration }}</a-tag>
                    </div>
                    <div v-if="a.description" class="attr-desc">{{ a.description }}</div>
                    <div v-if="a.address" class="attr-addr">📍 {{ a.address }}</div>
                  </div>
                </div>
              </div>

              <div v-if="day.meals.length" class="day-section">
                <div class="sec-label">🍽️ 餐饮</div>
                <div class="meal-list">
                  <div v-for="m in day.meals" :key="m.name" class="meal-item">
                    <span class="meal-name">{{ m.name }}</span>
                    <span v-if="m.cuisine" class="meal-cuisine">{{ m.cuisine }}</span>
                    <span v-if="m.price_range" class="meal-price">{{ m.price_range }}</span>
                  </div>
                </div>
              </div>

              <div v-if="day.hotel" class="day-section">
                <div class="sec-label">🏨 住宿</div>
                <div class="hotel-item">
                  <span class="hotel-name">{{ day.hotel.name }}</span>
                  <span v-if="day.hotel.price_range" class="hotel-price">{{ day.hotel.price_range }}</span>
                </div>
              </div>

              <div v-if="day.routes && day.routes.length" class="day-section">
                <div class="sec-label">🚏 交通路线</div>
                <div class="route-list">
                  <div v-for="(r, idx) in day.routes" :key="idx" class="route-item">
                    <div class="route-seg">
                      <span class="route-from">{{ r.from_name }}</span>
                      <span class="route-arrow">→</span>
                      <span class="route-to">{{ r.to_name }}</span>
                    </div>
                    <div class="route-summary">{{ r.summary }}</div>
                    <ul v-if="r.steps && r.steps.length" class="route-steps">
                      <li v-for="(s, i) in r.steps" :key="i">{{ s }}</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div v-if="day.transportation_tips" class="day-note">🚗 {{ day.transportation_tips }}</div>
              <div v-if="day.notes" class="day-note">📝 {{ day.notes }}</div>
            </div>
          </a-timeline-item>
        </a-timeline>
      </a-card>

      <!-- 预算 -->
      <a-card class="block" :bordered="false" title="💰 预算估算" v-if="plan.budget">
        <div class="budget">
          <div v-if="plan.budget.total" class="budget-total">总计：{{ plan.budget.total }}</div>
          <div v-for="(v, k) in plan.budget.breakdown" :key="k" class="budget-row">
            <span>{{ k }}</span>
            <span>{{ v }}</span>
          </div>
        </div>
      </a-card>

      <!-- 小贴士 -->
      <a-card class="block" :bordered="false" title="💡 旅行小贴士" v-if="plan.tips.length">
        <ul class="tips">
          <li v-for="t in plan.tips" :key="t">{{ t }}</li>
        </ul>
      </a-card>
    </template>

    <!-- 分享弹窗 -->
    <a-modal v-model:open="shareVisible" title="分享行程" :footer="null">
      <p>通过下方链接分享此行程（他人可只读查看）：</p>
      <a-input-group compact>
        <a-input v-model:value="shareUrl" readonly style="width: calc(100% - 90px)" />
        <a-button type="primary" @click="copyShare">复制</a-button>
      </a-input-group>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import TripMap from '@/components/TripMap.vue'
import { getTrip, saveTrip } from '@/api/trips'
import { createShare } from '@/api/share'
import { useAuthStore } from '@/stores/auth'
import type { Attraction, TripFormData, TripPlan } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
auth.restore()

const plan = ref<TripPlan | null>(null)
const requestData = ref<TripFormData | null>(null)
const tripId = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const shareVisible = ref(false)
const shareUrl = ref('')

const allAttractions = computed<Attraction[]>(() => {
  if (!plan.value) return []
  return plan.value.days.flatMap((d) => d.attractions)
})

const dayRoutes = computed<Attraction[][]>(() => {
  if (!plan.value) return []
  return plan.value.days
    .map((d) => d.attractions.filter((a) => a.location && a.location.longitude && a.location.latitude))
    .filter((list) => list.length >= 2)
})

onMounted(async () => {
  const id = route.params.id
  if (id) {
    loading.value = true
    try {
      const detail = await getTrip(Number(id))
      tripId.value = detail.id
      plan.value = detail.plan
    } catch {
      router.push('/my-trips')
    } finally {
      loading.value = false
    }
  } else {
    const raw = sessionStorage.getItem('tripPlan')
    const reqRaw = sessionStorage.getItem('tripRequest')
    if (raw) {
      plan.value = JSON.parse(raw)
    }
    if (reqRaw) {
      requestData.value = JSON.parse(reqRaw)
    }
    if (!plan.value) {
      message.warning('未找到行程计划')
      router.push('/')
    }
  }
})

async function handleSave() {
  if (!plan.value || !requestData.value) {
    message.warning('缺少保存所需数据')
    return
  }
  saving.value = true
  try {
    const saved = await saveTrip({ ...requestData.value, plan: plan.value })
    tripId.value = saved.id
    message.success('行程已保存')
  } catch {
    // 错误已由拦截器提示
  } finally {
    saving.value = false
  }
}

async function openShare() {
  if (!tripId.value) {
    message.warning('请先保存行程')
    return
  }
  try {
    const link = await createShare(tripId.value)
    shareUrl.value = link.url
    shareVisible.value = true
  } catch {
    // 错误已由拦截器提示
  }
}

async function copyShare() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    message.success('链接已复制')
  } catch {
    message.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
.result-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.actions {
  display: flex;
  gap: 8px;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}
.block {
  margin-bottom: 20px;
  border-radius: 14px;
}
.overview h1 {
  margin: 0 0 8px;
  font-size: 28px;
}
.meta {
  color: #667eea;
  font-weight: 600;
  margin: 0 0 8px;
}
.desc {
  color: #666;
  line-height: 1.7;
}
.weather-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}
.weather-item {
  background: #f7f9fc;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}
.w-date {
  color: #999;
  font-size: 13px;
}
.w-weather {
  font-size: 18px;
  margin: 6px 0;
}
.w-temp {
  color: #667eea;
  font-weight: 600;
}
.day-block {
  padding-bottom: 8px;
}
.day-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.day-title {
  font-size: 18px;
  font-weight: 700;
}
.day-date {
  color: #999;
}
.day-subtitle {
  color: #667eea;
  margin: 4px 0 10px;
}
.day-section {
  margin: 10px 0;
}
.sec-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}
.attraction-item {
  margin-bottom: 10px;
  padding: 10px;
  background: #fafafa;
  border-radius: 8px;
}
.attr-name {
  font-weight: 600;
}
.attr-desc {
  color: #666;
  margin-top: 4px;
  line-height: 1.6;
}
.attr-addr {
  color: #999;
  font-size: 13px;
  margin-top: 4px;
}
.meal-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.meal-item {
  background: #fafafa;
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.meal-name {
  font-weight: 600;
}
.meal-cuisine,
.meal-price {
  color: #999;
  font-size: 13px;
}
.hotel-item {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px;
  background: #fafafa;
  border-radius: 8px;
}
.hotel-name {
  font-weight: 600;
}
.hotel-price {
  color: #999;
}
.route-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.route-item {
  padding: 10px 12px;
  background: #f0f4ff;
  border-left: 3px solid #667eea;
  border-radius: 8px;
}
.route-seg {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.route-from,
.route-to {
  font-weight: 600;
}
.route-arrow {
  color: #667eea;
}
.route-summary {
  color: #667eea;
  font-size: 14px;
  margin-top: 4px;
}
.route-steps {
  margin: 6px 0 0;
  padding-left: 18px;
  color: #888;
  font-size: 13px;
  line-height: 1.7;
}
.day-note {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}
.budget-total {
  font-size: 18px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 10px;
}
.budget-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px dashed #eee;
}
.tips {
  margin: 0;
  padding-left: 20px;
  line-height: 1.8;
}
</style>
