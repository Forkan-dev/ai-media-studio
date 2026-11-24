<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Aperture } from 'lucide-vue-next'
import { routes } from '@/router'

const top = routes.filter((r) => r.meta?.nav === 'top')
const bottom = routes.filter((r) => r.meta?.nav === 'bottom')
</script>

<template>
  <nav class="flex w-56 shrink-0 flex-col border-r border-line bg-surface px-3 py-4">
    <div class="mb-6 flex h-8 items-center gap-2.5 px-3">
      <Aperture class="size-5 text-accent" />
      <span class="font-semibold tracking-tight">Framewise</span>
    </div>

    <div class="flex flex-col gap-0.5">
      <RouterLink v-for="r in top" :key="r.path" :to="r.path" class="nav-item">
        <component :is="r.meta?.icon" class="size-4" />
        {{ r.meta?.title }}
      </RouterLink>
    </div>

    <div class="mt-auto flex flex-col gap-0.5">
      <RouterLink v-for="r in bottom" :key="r.path" :to="r.path" class="nav-item">
        <component :is="r.meta?.icon" class="size-4" />
        {{ r.meta?.title }}
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
@reference '../assets/main.css';

.nav-item {
  @apply flex h-9 items-center gap-3 rounded-lg px-3 text-sm text-muted transition hover:bg-raised hover:text-fg;
}
.nav-item.router-link-active {
  @apply bg-raised text-fg;
}
</style>
