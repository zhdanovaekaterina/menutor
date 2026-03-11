import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/planner' },
    {
      path: '/planner',
      component: () => import('@/views/MenuPlannerView.vue'),
    },
    {
      path: '/shopping-list',
      component: () => import('@/views/ShoppingListView.vue'),
    },
    {
      path: '/recipes',
      component: () => import('@/views/RecipeListView.vue'),
    },
    {
      path: '/products',
      component: () => import('@/views/ProductListView.vue'),
    },
    {
      path: '/settings',
      component: () => import('@/views/SettingsView.vue'),
      redirect: '/settings/family',
      children: [
        {
          path: 'family',
          component: () => import('@/components/settings/FamilyPanel.vue'),
        },
        {
          path: 'product-categories',
          component: () => import('@/components/settings/CategoryPanel.vue'),
          props: { type: 'product' as const },
        },
        {
          path: 'recipe-categories',
          component: () => import('@/components/settings/CategoryPanel.vue'),
          props: { type: 'recipe' as const },
        },
        {
          path: 'about',
          component: () => import('@/components/settings/AboutPanel.vue'),
        },
      ],
    },
  ],
})

export default router
