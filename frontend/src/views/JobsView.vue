<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'
import BaseCard from '@/components/BaseCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { api, type Job } from '@/api'

const jobs = ref<Job[]>([])
onMounted(async () => (jobs.value = await api.get<Job[]>('/studio/jobs')))
</script>

<template>
  <BaseCard title="All videos">
    <ul class="-my-2 divide-y divide-line">
      <li v-for="j in jobs" :key="j.id">
        <RouterLink :to="`/jobs/${j.id}`" class="group flex items-center gap-4 py-3">
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium">{{ j.topic }}</p>
            <p class="mt-0.5 text-xs text-muted capitalize">
              {{ j.brand.replaceAll('_', ' ') }} · {{ j.stage }}
            </p>
          </div>
          <StatusBadge :status="j.status" />
          <ChevronRight class="size-4 text-muted group-hover:text-fg" />
        </RouterLink>
      </li>
      <li v-if="!jobs.length" class="py-10 text-center text-sm text-muted">No videos yet</li>
    </ul>
  </BaseCard>
</template>
