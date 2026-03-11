<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'
import ToastNotification from '@/components/ui/ToastNotification.vue'
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <AppSidebar />
    <main class="flex-1 overflow-y-auto pb-16 lg:pb-0">
      <RouterView />
    </main>
    <MobileBottomNav />
    <ToastNotification />
  </div>
</template>
