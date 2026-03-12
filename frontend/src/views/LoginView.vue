<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { AxiosError } from 'axios'

const auth = useAuthStore()
const toast = useToastStore()
const router = useRouter()

const isRegister = ref(false)
const email = ref('')
const password = ref('')
const nickname = ref('')
const loading = ref(false)

function errorMessage(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data?.detail) {
    return String(err.response.data.detail)
  }
  return 'Произошла ошибка'
}

async function handleSubmit() {
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.register({
        email: email.value,
        password: password.value,
        nickname: nickname.value || undefined,
      })
      isRegister.value = false
    } else {
      await auth.login({ email: email.value, password: password.value })
      router.push('/')
    }
  } catch (err) {
    toast.show(errorMessage(err), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-sm space-y-6">
      <div class="text-center">
        <h1 class="text-2xl font-bold text-gray-900">Планировщик меню</h1>
        <p class="mt-1 text-sm text-gray-500">
          {{ isRegister ? 'Создание аккаунта' : 'Вход в аккаунт' }}
        </p>
      </div>

      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
          />
        </div>

        <div v-if="isRegister">
          <label for="nickname" class="block text-sm font-medium text-gray-700">Имя</label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            autocomplete="name"
            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:outline-none disabled:opacity-50"
        >
          {{ loading ? '...' : isRegister ? 'Зарегистрироваться' : 'Войти' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500">
        <template v-if="isRegister">
          Уже есть аккаунт?
          <button class="font-medium text-emerald-600 hover:text-emerald-500" @click="isRegister = false">
            Войти
          </button>
        </template>
        <template v-else>
          Нет аккаунта?
          <button class="font-medium text-emerald-600 hover:text-emerald-500" @click="isRegister = true">
            Зарегистрироваться
          </button>
        </template>
      </p>
    </div>
  </div>
</template>
