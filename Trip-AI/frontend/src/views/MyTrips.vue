<template>
  <div class="my-trips-page">
    <div class="top-bar">
      <a-button @click="$router.push('/')">← 返回首页</a-button>
      <h2>我的行程</h2>
      <div style="width: 100px"></div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!trips.length" description="还没有保存的行程，去生成一个吧">
      <a-button type="primary" @click="$router.push('/')">去规划</a-button>
    </a-empty>

    <div v-else class="trip-grid">
      <a-card v-for="t in trips" :key="t.id" class="trip-card" :bordered="false" hoverable>
        <div class="trip-card-body">
          <div class="trip-city">🏙️ {{ t.city }}</div>
          <div class="trip-meta">{{ t.start_date }} ~ {{ t.end_date }}</div>
          <div class="trip-meta">共 {{ t.travel_days }} 天</div>
          <div class="trip-actions">
            <a-button type="primary" size="small" @click="$router.push(`/my-trips/${t.id}`)">查看</a-button>
            <a-button size="small" @click="handleShare(t.id)">分享</a-button>
            <a-popconfirm title="确定删除此行程吗？" @confirm="handleDelete(t.id)">
              <a-button danger size="small">删除</a-button>
            </a-popconfirm>
          </div>
        </div>
      </a-card>
    </div>

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
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { deleteTrip, listTrips } from '@/api/trips'
import { createShare } from '@/api/share'
import type { TripSummary } from '@/types'

const trips = ref<TripSummary[]>([])
const loading = ref(false)
const shareVisible = ref(false)
const shareUrl = ref('')

onMounted(load)

async function load() {
  loading.value = true
  try {
    trips.value = await listTrips()
  } catch {
    // 错误已由拦截器提示
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteTrip(id)
    message.success('已删除')
    await load()
  } catch {
    // 错误已由拦截器提示
  }
}

async function handleShare(id: number) {
  try {
    const link = await createShare(id)
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
.my-trips-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 16px 60px;
}
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.top-bar h2 {
  margin: 0;
}
.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}
.trip-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.trip-card {
  border-radius: 12px;
}
.trip-city {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
}
.trip-meta {
  color: #888;
  font-size: 14px;
}
.trip-actions {
  margin-top: 14px;
  display: flex;
  gap: 8px;
}
</style>
