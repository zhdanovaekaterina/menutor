<script setup lang="ts">
import { ref } from 'vue'
import { changePassword } from '@/api/client'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function onSubmit() {
  if (newPassword.value !== confirmPassword.value) {
    toast.show('Новые пароли не совпадают', 'error')
    return
  }
  if (newPassword.value.length < 6) {
    toast.show('Новый пароль должен содержать не менее 6 символов', 'error')
    return
  }
  loading.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    toast.show('Пароль успешно изменён', 'success')
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    toast.show(e?.response?.data?.detail ?? 'Ошибка смены пароля', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-sm space-y-4">
    <h2 class="text-lg font-semibold">Смена пароля</h2>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Текущий пароль</label>
      <input
        v-model="currentPassword"
        type="password"
        autocomplete="current-password"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Новый пароль</label>
      <input
        v-model="newPassword"
        type="password"
        autocomplete="new-password"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      />
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Повторите новый пароль</label>
      <input
        v-model="confirmPassword"
        type="password"
        autocomplete="new-password"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        @keydown.enter="onSubmit"
      />
    </div>

    <button
      :disabled="loading || !currentPassword || !newPassword || !confirmPassword"
      class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      @click="onSubmit"
    >
      {{ loading ? 'Сохранение...' : 'Сменить пароль' }}
    </button>
  </div>
</template>
