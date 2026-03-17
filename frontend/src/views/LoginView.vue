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
const showPassword = ref(false)

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
  <div class="flex min-h-[100dvh] items-center justify-center bg-gray-50 px-6">
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
            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2.5 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
          />
        </div>

        <div v-if="isRegister">
          <label for="nickname" class="block text-sm font-medium text-gray-700">Имя</label>
          <input
            id="nickname"
            v-model="nickname"
            type="text"
            autocomplete="name"
            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2.5 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Пароль</label>
          <div class="relative">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autocomplete="current-password"
              class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2.5 pr-10 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 focus:outline-none sm:text-sm"
            />
            <button
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
              <svg v-else class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
              </svg>
            </button>
          </div>
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
