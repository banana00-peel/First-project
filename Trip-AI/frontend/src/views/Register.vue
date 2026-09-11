<template>
  <div class="auth-container">
    <a-card class="auth-card" :bordered="false">
      <div class="auth-header">
        <span class="auth-icon">🧳</span>
        <h1>创建账号</h1>
        <p>开启你的智能旅行规划</p>
      </div>
      <a-form :model="form" layout="vertical" @finish="handleSubmit">
        <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
          <a-input v-model:value="form.username" placeholder="用户名" size="large" />
        </a-form-item>
        <a-form-item
          name="email"
          :rules="[{ required: true, type: 'email', message: '请输入有效邮箱' }]"
        >
          <a-input v-model:value="form.email" placeholder="邮箱" size="large" />
        </a-form-item>
        <a-form-item name="password" :rules="[{ required: true, min: 6, message: '密码至少 6 位' }]">
          <a-input-password v-model:value="form.password" placeholder="密码" size="large" />
        </a-form-item>
        <a-button type="primary" html-type="submit" block size="large" :loading="loading">
          注册
        </a-button>
      </a-form>
      <div class="auth-footer">
        已有账号？
        <router-link to="/login">去登录</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { register } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', email: '', password: '' })

async function handleSubmit() {
  loading.value = true
  try {
    const res = await register(form)
    auth.setSession(res.access_token, res.user)
    message.success('注册成功')
    router.push('/')
  } catch {
    // 错误已由拦截器提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.auth-card {
  width: 400px;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 8px;
}
.auth-header {
  text-align: center;
  margin-bottom: 24px;
}
.auth-icon {
  font-size: 48px;
}
.auth-header h1 {
  margin: 8px 0 4px;
  font-size: 28px;
}
.auth-header p {
  color: #888;
  margin: 0;
}
.auth-footer {
  text-align: center;
  margin-top: 16px;
  color: #888;
}
</style>
