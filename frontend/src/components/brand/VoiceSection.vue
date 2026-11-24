<script setup lang="ts">
import { computed, ref } from 'vue'
import { Pause, Play, Upload } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import FormField from '@/components/form/FormField.vue'
import SegmentedControl from '@/components/form/SegmentedControl.vue'
import ToggleSwitch from '@/components/form/ToggleSwitch.vue'
import { api, type BrandConfig, type BrandOptions } from '@/api'

const config = defineModel<BrandConfig>({ required: true })
const props = defineProps<{ options: BrandOptions }>()

// Kokoro voice ids: a/b = American/British, f/m = female/male, then the name
const groups = computed(() => {
  const label: Record<string, string> = { af: 'US female', am: 'US male', bf: 'UK female', bm: 'UK male' }
  const out: Record<string, { id: string; name: string }[]> = {}
  for (const id of props.options.kokoro_voices) {
    const group = label[id.slice(0, 2)] ?? 'Other'
    ;(out[group] ??= []).push({ id, name: id.slice(3).replace(/^\w/, (c) => c.toUpperCase()) })
  }
  return out
})
const sampleName = computed(() => config.value.voice.voice_ref?.split('/').pop() ?? '')

// preview of the CURRENT (unsaved) settings
const player = new Audio()
const previewing = ref(false)
const playing = ref(false)
const error = ref('')
player.onended = () => (playing.value = false)

async function preview() {
  if (playing.value) return (player.pause(), (playing.value = false))
  previewing.value = true
  error.value = ''
  try {
    const { url } = await api.post<{ url: string }>('/studio/voice-preview', { voice: config.value.voice })
    player.src = url
    await player.play()
    playing.value = true
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    previewing.value = false
  }
}

const uploading = ref(false)
async function upload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  error.value = ''
  try {
    const { path } = await api.upload<{ path: string }>(`/studio/brands/${config.value.slug}/voice-sample`, file)
    config.value.voice.voice_ref = path
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <BaseCard title="Voice">
    <template #actions>
      <BaseButton variant="ghost" :loading="previewing" @click="preview">
        <component :is="playing ? Pause : Play" v-if="!previewing" class="size-4" />Preview
      </BaseButton>
    </template>

    <div class="space-y-4">
      <FormField label="Engine">
        <SegmentedControl v-model="config.voice.engine" :options="options.engines" />
      </FormField>

      <div v-if="config.voice.engine === 'kokoro'" class="flex gap-4">
        <FormField label="Voice" class="flex-1">
          <select v-model="config.voice.voice" class="field">
            <optgroup v-for="(voices, group) in groups" :key="group" :label="String(group)">
              <option v-for="v in voices" :key="v.id" :value="v.id">{{ v.name }}</option>
            </optgroup>
          </select>
        </FormField>
        <FormField label="Speed">
          <input
            v-model.number="config.voice.speed"
            type="number"
            step="0.05"
            min="0.5"
            max="2"
            class="field w-24"
          />
        </FormField>
      </div>

      <template v-else>
        <FormField label="Voice to clone">
          <div class="flex items-center gap-2">
            <span class="field flex items-center truncate text-muted">
              {{ sampleName || 'Default voice' }}
            </span>
            <label
              class="flex h-9 shrink-0 cursor-pointer items-center gap-2 rounded-lg px-3 text-sm text-muted hover:bg-raised hover:text-fg"
            >
              <span
                v-if="uploading"
                class="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
              />
              <Upload v-else class="size-4" />Upload
              <input type="file" accept="audio/*" class="hidden" @change="upload" />
            </label>
            <button
              v-if="sampleName"
              class="h-9 shrink-0 rounded-lg px-2 text-xs text-muted hover:text-fg"
              @click="config.voice.voice_ref = null"
            >
              Reset
            </button>
          </div>
        </FormField>
        <div class="grid grid-cols-2 gap-4">
          <FormField :label="`Emotion · ${config.voice.exaggeration.toFixed(2)}`">
            <input
              v-model.number="config.voice.exaggeration"
              type="range"
              min="0.25"
              max="1"
              step="0.05"
              class="w-full accent-accent"
            />
          </FormField>
          <FormField :label="`Pace · ${config.voice.cfg_weight.toFixed(2)}`">
            <input
              v-model.number="config.voice.cfg_weight"
              type="range"
              min="0.2"
              max="0.8"
              step="0.05"
              class="w-full accent-accent"
            />
          </FormField>
        </div>
        <ToggleSwitch v-model="config.voice.scene_emotions" label="Emotion per scene" />
      </template>

      <p v-if="error" class="text-sm text-bad">{{ error }}</p>
    </div>
  </BaseCard>
</template>
