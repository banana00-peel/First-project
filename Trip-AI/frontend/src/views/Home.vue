<template>
  <div class="home-container">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <div class="brand" @click="$router.push('/')">
        <span>✈️</span> Trip-AI
      </div>
      <div class="nav-actions">
        <template v-if="auth.user">
          <a-dropdown>
            <span class="user-chip">👤 {{ auth.user.username }}</span>
            <template #overlay>
              <a-menu>
                <a-menu-item key="trips" @click="$router.push('/my-trips')">我的行程</a-menu-item>
                <a-menu-item key="logout" @click="handleLogout">退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </template>
        <template v-else>
          <a-button type="text" class="nav-link" @click="$router.push('/login')">登录</a-button>
          <a-button type="primary" @click="$router.push('/register')">注册</a-button>
        </template>
      </div>
    </div>

    <!-- 标题 -->
    <div class="page-header">
      <div class="icon-wrapper"><span class="icon">✈️</span></div>
      <h1 class="page-title">AI 智能旅行规划</h1>
      <p class="page-subtitle">输入目的地与偏好，AI 为你生成专属旅行计划</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form :model="formData" layout="vertical" @finish="handleSubmit">
        <!-- 目的地与日期 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">📍</span>
            <span class="section-title">目的地与日期</span>
          </div>
          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>目的地城市</template>
                <a-input v-model:value="formData.city" placeholder="例如：北京" size="large" />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
                <template #label>开始日期</template>
                <a-date-picker v-model:value="formData.start_date" style="width: 100%" size="large" />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
                <template #label>结束日期</template>
                <a-date-picker v-model:value="formData.end_date" style="width: 100%" size="large" />
              </a-form-item>
            </a-col>
            <a-col :span="4">
              <a-form-item>
                <template #label>旅行天数</template>
                <div class="days-display">{{ formData.travel_days }} 天</div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 偏好设置 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">⚙️</span>
            <span class="section-title">偏好设置</span>
          </div>
          <a-row :gutter="24">
            <a-col :span="8">
              <a-form-item name="transportation">
                <template #label>交通方式</template>
                <a-select v-model:value="formData.transportation" size="large">
                  <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                  <a-select-option value="自驾">🚗 自驾</a-select-option>
                  <a-select-option value="步行">🚶 步行</a-select-option>
                  <a-select-option value="混合">🔀 混合</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="accommodation">
                <template #label>住宿偏好</template>
                <a-select v-model:value="formData.accommodation" size="large">
                  <a-select-option value="经济型酒店">💰 经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">🏨 舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">⭐ 豪华酒店</a-select-option>
                  <a-select-option value="民宿">🏡 民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item name="preferences">
                <template #label>旅行偏好</template>
                <a-checkbox-group v-model:value="formData.preferences" class="pref-group">
                  <a-checkbox value="历史文化">🏛️ 历史文化</a-checkbox>
                  <a-checkbox value="自然风光">🏞️ 自然风光</a-checkbox>
                  <a-checkbox value="美食">🍜 美食</a-checkbox>
                  <a-checkbox value="购物">🛍️ 购物</a-checkbox>
                  <a-checkbox value="艺术">🎨 艺术</a-checkbox>
                  <a-checkbox value="休闲">☕ 休闲</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <span class="section-icon">💬</span>
            <span class="section-title">额外要求</span>
          </div>
          <a-form-item name="free_text">
            <a-textarea
              v-model:value="formData.free_text"
              placeholder="例如：想看升旗、需要无障碍设施、对海鲜过敏等..."
              :rows="3"
              size="large"
            />
          </a-form-item>
        </div>

        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading" size="large" block class="submit-button">
            {{ loading ? '正在生成...' : '🚀 开始规划我的旅行' }}
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import { generateTrip } from '@/api/trips'
import { useAuthStore } from '@/stores/auth'
import type { TripFormData } from '@/types'

const router = useRouter()
const auth = useAuthStore()
auth.restore()
const loading = ref(false)

type FormState = Omit<TripFormData, 'start_date' | 'end_date'> & {
  start_date: Dayjs | null
  end_date: Dayjs | null
}

const formData = reactive<FormState>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text: '',
})

watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过 30 天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

function handleLogout() {
  auth.logout()
  message.success('已退出登录')
}

async function handleSubmit() {
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }
  loading.value = true
  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text: formData.free_text,
    }
    const res = await generateTrip(requestData)
    if (res.success && res.data) {
      sessionStorage.setItem('tripPlan', JSON.stringify(res.data))
      sessionStorage.setItem('tripRequest', JSON.stringify(requestData))
      message.success('旅行计划生成成功！')
      router.push('/result')
    } else {
      message.error(res.message || '生成失败')
    }
  } catch {
    // 错误已由拦截器提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding-bottom: 60px;
}
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
}
.brand {
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  cursor: pointer;
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-link {
  color: #fff;
}
.user-chip {
  color: #fff;
  cursor: pointer;
  font-size: 15px;
}
.page-header {
  text-align: center;
  padding: 40px 20px 30px;
}
.icon {
  font-size: 64px;
  display: inline-block;
}
.page-title {
  color: #fff;
  font-size: 42px;
  font-weight: 800;
  margin: 12px 0 8px;
}
.page-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 18px;
  margin: 0;
}
.form-card {
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f7f9fc;
  border-radius: 14px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}
.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}
.days-display {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  border-radius: 10px;
}
.pref-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.submit-button {
  height: 52px;
  border-radius: 26px;
  font-size: 17px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}
</style>
