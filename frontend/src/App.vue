<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import ToastNotification from '@/components/ui/ToastNotification.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

onMounted(() => auth.init())
</script>

<template>
  <div v-if="route.meta.public" class="h-screen bg-gray-50">
    <RouterView />
    <ToastNotification />
  </div>
  <div v-else class="flex h-screen bg-gray-50">
    <AppSidebar />
    <main class="flex-1 overflow-y-auto pb-16 lg:pb-0">
      <RouterView />
    </main>
    <MobileBottomNav />
    <ToastNotification />
  </div>
</template>
