<template>
  <div class="share-page">
    <div class="top-bar">
      <a-button @click="$router.push('/')">← 返回首页</a-button>
      <div class="copy-btn" v-if="data">
        <a-button type="primary" @click="copyTrip">复制此行程到我的账号</a-button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <a-spin size="large" />
    </div>

    <a-result v-else-if="error" status="404" title="无法查看">
      <template #subTitle>{{ error }}</template>
    </a-result>

    <template v-else-if="data && data.plan">
      <a-card class="block" :bordered="false">
        <div class="overview">
          <h1>🏙️ {{ data.plan.city }} 旅行计划</h1>
          <p class="meta">{{ data.plan.start_date }} ~ {{ data.plan.end_date }} · {{ data.plan.travel_days }} 天</p>
          <a-tag color="orange">分享行程 · 只读</a-tag>
        </div>
      </a-card>

      <a-card class="block" :bordered="false" title="📅 每日行程">
        <a-timeline>
          <a-timeline-item v-for="day in data.plan.days" :key="day.day" color="#667eea">
            <div class="day-title">第 {{ day.day }} 天 <span v-if="day.date" class="day-date">{{ day.date }}</span></div>
            <div v-if="day.title" class="day-subtitle">{{ day.title }}</div>
            <ul v-if="day.attractions.length" class="day-list">
              <li v-for="a in day.attractions" :key="a.name">
                {{ a.name }}
                <span v-if="a.suggested_duration" class="dur">({{ a.suggested_duration }})</span>
              </li>
            </ul>
            <div v-if="day.meals.length" class="day-note">🍽️ {{ day.meals.map((m) => m.name).join('、') }}</div>
            <div v-if="day.hotel" class="day-note">🏨 {{ day.hotel.name }}</div>
          </a-timeline-item>
        </a-timeline>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getSharedTrip } from '@/api/share'
import { saveTrip } from '@/api/trips'
import { useAuthStore } from '@/stores/auth'
import type { SharedTrip } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
auth.restore()

const data = ref<SharedTrip | null>(null)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  const token = route.params.token as string
  loading.value = true
  try {
    data.value = await getSharedTrip(token)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '分享链接无效或已过期'
  } finally {
    loading.value = false
  }
})

async function copyTrip() {
  if (!auth.isLoggedIn()) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (!data.value) return
  const d = data.value
  try {
    await saveTrip({
      city: d.city,
      start_date: d.start_date,
      end_date: d.end_date,
      travel_days: d.travel_days,
      transportation: d.transportation,
      accommodation: d.accommodation,
      preferences: d.preferences,
      free_text: d.free_text,
      plan: d.plan,
    })
    message.success('已复制到你的行程')
    router.push('/my-trips')
  } catch {
    // 错误已由拦截器提示
  }
}
</script>

<style scoped>
.share-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
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
}
.day-title {
  font-size: 17px;
  font-weight: 700;
}
.day-date {
  color: #999;
  font-weight: 400;
}
.day-subtitle {
  color: #667eea;
  margin: 4px 0;
}
.day-list {
  margin: 4px 0;
  padding-left: 20px;
}
.dur {
  color: #999;
  font-size: 13px;
}
.day-note {
  color: #666;
  margin-top: 4px;
}
</style>
