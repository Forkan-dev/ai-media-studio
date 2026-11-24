import { onUnmounted, ref, watch, type Ref } from 'vue'
import { api, type JobPage } from '@/api'

const POLL_MS = 3000

/** The job screen data; polls while the job is queued or working (a stage, or one image / voice line). */
export function useJob(id: Ref<number>) {
  const page = ref<JobPage>()
  const error = ref('')
  let timer: ReturnType<typeof setTimeout> | undefined

  async function load() {
    clearTimeout(timer)
    try {
      page.value = await api.get<JobPage>(`/studio/jobs/${id.value}`)
      error.value = ''
    } catch (e) {
      error.value = (e as Error).message
    }
    const status = page.value?.job.status
    if (status === 'running' || status === 'queued') timer = setTimeout(load, POLL_MS)
  }

  watch(id, load, { immediate: true })
  onUnmounted(() => clearTimeout(timer))

  return { page, error, load }
}
