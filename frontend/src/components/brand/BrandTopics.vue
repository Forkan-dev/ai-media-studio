<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, Play, Sparkles } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import ScoreDot from '@/components/ScoreDot.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { api, type Brand, type Job, type Topic } from '@/api'

const props = defineProps<{ brand: Brand }>()
const router = useRouter()

const topics = ref<Topic[]>([])
const jobs = ref<Job[]>([])
const ownTopic = ref('')
const style = ref(props.brand.default_style)
const discovering = ref(false)
const starting = ref<string | null>(null) // topic being started
const error = ref('')

async function load() {
  const page = await api.get<{ topics: Topic[]; jobs: Job[] }>(`/studio/brands/${props.brand.slug}`)
  topics.value = page.topics
  jobs.value = page.jobs
}

async function discover() {
  discovering.value = true
  error.value = ''
  try {
    await api.post(`/studio/brands/${props.brand.slug}/topics/discover`)
    await load()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    discovering.value = false
  }
}

async function make(topic: string) {
  if (!topic.trim()) return
  starting.value = topic
  error.value = ''
  try {
    const job = await api.post<Job>('/studio/jobs', {
      brand: props.brand.slug,
      topic: topic.trim(),
      style: style.value,
    })
    router.push(`/jobs/${job.id}`)
  } catch (e) {
    error.value = (e as Error).message
    starting.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[1fr_22rem]">
    <BaseCard title="Topics">
      <template #actions>
        <BaseButton variant="ghost" :loading="discovering" @click="discover">
          <Sparkles v-if="!discovering" class="size-4" />
          {{ discovering ? 'Finding topics…' : 'Get topics' }}
        </BaseButton>
      </template>

      <form class="flex gap-2" @submit.prevent="make(ownTopic)">
        <input v-model="ownTopic" class="field flex-1" placeholder="Your own topic…" />
        <select v-model="style" class="field w-40 capitalize">
          <option v-for="s in brand.styles" :key="s" :value="s">{{ s.replaceAll('_', ' ') }}</option>
        </select>
        <BaseButton type="submit" :loading="starting === ownTopic && !!ownTopic">
          <Play class="size-4" />
        </BaseButton>
      </form>

      <p v-if="error" class="mt-3 text-sm text-bad">{{ error }}</p>

      <ul class="mt-4 divide-y divide-line border-t border-line">
        <li v-for="t in topics" :key="t.id" class="group flex items-center gap-4 py-3">
          <ScoreDot :score="t.score" class="w-10 shrink-0" />
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium">{{ t.title }}</p>
            <p class="mt-0.5 truncate text-xs text-muted">{{ t.angle }}</p>
          </div>
          <button
            class="grid size-8 shrink-0 place-items-center rounded-lg text-muted opacity-0 transition group-hover:opacity-100 hover:bg-accent hover:text-bg disabled:opacity-100"
            :disabled="!!starting"
            title="Make video"
            @click="make(t.title)"
          >
            <span
              v-if="starting === t.title"
              class="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            />
            <Play v-else class="size-4" />
          </button>
        </li>
        <li v-if="!topics.length" class="py-10 text-center text-sm text-muted">
          <Sparkles class="mx-auto mb-2 size-5" />
          No topics yet
        </li>
      </ul>
    </BaseCard>

    <BaseCard title="Recent videos">
      <ul class="-my-2 divide-y divide-line">
        <li v-for="j in jobs" :key="j.id">
          <RouterLink :to="`/jobs/${j.id}`" class="group flex items-center gap-3 py-2.5">
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm">{{ j.topic }}</p>
              <StatusBadge :status="j.status" />
            </div>
            <ChevronRight class="size-4 text-muted group-hover:text-fg" />
          </RouterLink>
        </li>
        <li v-if="!jobs.length" class="py-6 text-center text-xs text-muted">None yet</li>
      </ul>
    </BaseCard>
  </div>
</template>
