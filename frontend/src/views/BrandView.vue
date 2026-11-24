<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Lightbulb, SlidersHorizontal } from 'lucide-vue-next'
import BrandSettings from '@/components/brand/BrandSettings.vue'
import BrandTopics from '@/components/brand/BrandTopics.vue'
import { api, type Brand } from '@/api'

const route = useRoute()
const router = useRouter()
const slug = computed(() => String(route.params.slug))
const brand = ref<Brand>()

const tabs = [
  { id: 'topics', label: 'Topics', icon: Lightbulb },
  { id: 'settings', label: 'Settings', icon: SlidersHorizontal },
]
const tab = computed(() => (route.query.tab === 'settings' ? 'settings' : 'topics'))

onMounted(async () => {
  brand.value = (await api.get<{ brand: Brand }>(`/studio/brands/${slug.value}`)).brand
})
</script>

<template>
  <div v-if="brand">
    <header class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <RouterLink
          to="/studio"
          class="grid size-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg"
        >
          <ArrowLeft class="size-4" />
        </RouterLink>
        <h2 class="text-lg font-semibold tracking-tight">{{ brand.name }}</h2>
        <span class="rounded-md bg-surface px-2 py-0.5 text-xs text-muted capitalize">
          {{ brand.preset }}
        </span>
      </div>

      <nav class="inline-flex rounded-lg bg-surface p-0.5">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="flex h-8 items-center gap-2 rounded-md px-3 text-sm transition"
          :class="tab === t.id ? 'bg-raised text-fg' : 'text-muted hover:text-fg'"
          @click="router.replace({ query: { tab: t.id } })"
        >
          <component :is="t.icon" class="size-4" />
          {{ t.label }}
        </button>
      </nav>
    </header>

    <BrandSettings
      v-if="tab === 'settings'"
      :slug="slug"
      @saved="(c) => brand && (brand.name = c.name)"
    />
    <BrandTopics v-else :brand="brand" />
  </div>
</template>
