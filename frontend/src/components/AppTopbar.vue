<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'

const route = useRoute()
const services = ref<Record<string, boolean> | null>(null)

const allUp = computed(() => services.value && Object.values(services.value).every(Boolean))
const tooltip = computed(() =>
  services.value
    ? Object.entries(services.value)
        .map(([name, up]) => `${name}: ${up ? 'up' : 'down'}`)
        .join('\n')
    : 'checking…',
)

onMounted(async () => {
  services.value = await api.get<Record<string, boolean>>('/health').catch(() => ({ backend: false }))
})
</script>

<template>
  <header class="flex h-16 shrink-0 items-center justify-between border-b border-line bg-surface px-8">
    <div class="flex items-center gap-3">
      <span class="grid size-8 place-items-center rounded-lg bg-raised text-muted">
        <component :is="route.meta.icon" class="size-4" />
      </span>
      <h1 class="text-[15px] font-semibold tracking-tight">{{ route.meta.title }}</h1>
    </div>

    <span
      :title="tooltip"
      class="flex items-center gap-2 rounded-full bg-raised px-3 py-1.5 text-xs text-muted"
    >
      <span
        class="size-1.5 rounded-full"
        :class="services === null ? 'bg-muted' : allUp ? 'bg-good' : 'bg-bad'"
      />
      {{ services === null ? 'Checking' : allUp ? 'Online' : 'Issue' }}
    </span>
  </header>
</template>
