<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import BaseButton from '@/components/BaseButton.vue'
import BasicsSection from './BasicsSection.vue'
import ImagesSection from './ImagesSection.vue'
import LookSection from './LookSection.vue'
import ScriptSection from './ScriptSection.vue'
import VoiceSection from './VoiceSection.vue'
import { api, type BrandConfig, type BrandOptions } from '@/api'

const props = defineProps<{ slug: string }>()
const emit = defineEmits<{ saved: [config: BrandConfig] }>()

const config = ref<BrandConfig>()
const options = ref<BrandOptions>()
const saved = ref('') // last saved config as JSON, to know if there are changes
const saving = ref(false)
const error = ref('')

const dirty = computed(() => !!config.value && JSON.stringify(config.value) !== saved.value)

function set(c: BrandConfig) {
  config.value = structuredClone(c)
  saved.value = JSON.stringify(c)
}

onMounted(async () => {
  const data = await api.get<{ config: BrandConfig; options: BrandOptions }>(
    `/studio/brands/${props.slug}/settings`,
  )
  options.value = data.options
  set(data.config)
})

/** Empty optional text fields mean "not set". */
function clean(c: BrandConfig): BrandConfig {
  const empty = (v: string | null) => (v?.trim() ? v : null)
  return {
    ...c,
    review_model: empty(c.review_model),
    voice: { ...c.voice, voice_ref: empty(c.voice.voice_ref) },
    images: { ...c.images, lora: empty(c.images.lora) },
  }
}

async function save() {
  if (!config.value) return
  saving.value = true
  error.value = ''
  try {
    const result = await api.put<BrandConfig>(`/studio/brands/${props.slug}`, clean(config.value))
    set(result)
    emit('saved', result)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="config && options" class="pb-20">
    <div class="grid gap-5 xl:grid-cols-2">
      <div class="space-y-5">
        <BasicsSection v-model="config" :options="options" />
        <ScriptSection v-model="config" :options="options" />
      </div>
      <div class="space-y-5">
        <ImagesSection v-model="config" />
        <VoiceSection v-model="config" :options="options" />
        <LookSection v-model="config" :options="options" />
      </div>
    </div>

    <Transition
      enter-from-class="translate-y-4 opacity-0"
      leave-to-class="translate-y-4 opacity-0"
      enter-active-class="transition"
      leave-active-class="transition"
    >
      <div
        v-if="dirty || error"
        class="fixed right-8 bottom-6 flex max-w-md items-center gap-3 rounded-xl border border-line bg-surface p-2 pl-4 shadow-2xl"
      >
        <p class="text-sm whitespace-pre-line" :class="error ? 'text-bad' : 'text-muted'">
          {{ error || 'Unsaved changes' }}
        </p>
        <BaseButton variant="ghost" @click="set(JSON.parse(saved)), (error = '')">Discard</BaseButton>
        <BaseButton :loading="saving" @click="save">Save</BaseButton>
      </div>
    </Transition>
  </div>
</template>
