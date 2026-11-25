<script setup lang="ts">
/** One scene: its image (click to enlarge), the line it shows in the video, the prompt and style
 *  (saved when changed, drawn only on Test / Redraw), and the check result. */
import { ref, watch } from 'vue'
import { AlertTriangle, CheckCircle2, ImageOff, PenLine, RotateCcw } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import ImageViewer from '@/components/ImageViewer.vue'
import type { Scene } from '@/api'

const props = defineProps<{
  scene: Scene
  number: number
  styles: string[]
  vertical: boolean
  pending: boolean // this scene is being drawn
  disabled: boolean // another change is running
  label: string // "Test" or "Redraw"
}>()
// draw sends the current prompt + style, so a click right after typing never draws the old prompt
const emit = defineEmits<{ draw: [prompt: string, style: string]; save: [prompt: string, style: string] }>()

const prompt = ref('')
const style = ref('')
const enlarged = ref(false)
watch(
  () => [props.scene.image_prompt, props.scene.style],
  () => {
    prompt.value = props.scene.image_prompt
    style.value = props.scene.style
  },
  { immediate: true },
)

/** Save edits (no drawing); the next Test / Redraw / Approve uses them. */
function save() {
  if (prompt.value.trim() && (prompt.value !== props.scene.image_prompt || style.value !== props.scene.style)) {
    emit('save', prompt.value, style.value)
  }
}
</script>

<template>
  <li class="flex gap-4 rounded-lg border border-line p-3">
    <div
      class="relative shrink-0 overflow-hidden rounded-md bg-raised"
      :class="vertical ? 'aspect-[9/16] w-32' : 'aspect-video w-52'"
    >
      <img
        v-if="scene.image"
        :src="scene.image"
        class="size-full cursor-zoom-in object-cover"
        loading="lazy"
        @click="enlarged = true"
      />
      <ImageOff v-else class="absolute inset-0 m-auto size-5 text-muted/50" />
      <div v-if="pending" class="absolute inset-0 grid place-items-center bg-black/50">
        <span class="size-6 animate-spin rounded-full border-2 border-fg border-t-transparent" />
      </div>
      <span class="absolute top-1.5 left-1.5 rounded bg-black/60 px-1.5 text-[10px] tabular-nums">
        {{ number }}
      </span>
    </div>

    <div class="flex min-w-0 flex-1 flex-col gap-2">
      <p class="text-sm">“{{ scene.narration }}”</p>
      <textarea v-model="prompt" rows="4" class="field flex-1 text-xs text-muted" @blur="save" />
      <p v-if="scene.outdated" class="flex items-center gap-1.5 text-xs text-warn">
        <PenLine class="size-3.5" />Prompt changed · {{ label.toLowerCase() }} to update the image
      </p>
      <p
        v-else-if="scene.check"
        class="flex items-start gap-1.5 text-xs"
        :class="scene.check.ok ? 'text-good' : 'text-warn'"
      >
        <component :is="scene.check.ok ? CheckCircle2 : AlertTriangle" class="mt-px size-3.5 shrink-0" />
        {{ scene.check.ok ? 'Matches the prompt' : scene.check.reason }}
      </p>
      <div class="flex items-center justify-between gap-2">
        <select v-model="style" class="field h-8 w-44 text-xs capitalize" @change="save">
          <option v-for="s in styles" :key="s" :value="s">{{ s.replaceAll('_', ' ') }}</option>
        </select>
        <BaseButton variant="ghost" :disabled="disabled" @click="emit('draw', prompt, style)">
          <RotateCcw class="size-4" />{{ label }}
        </BaseButton>
      </div>
    </div>

    <ImageViewer v-if="enlarged && scene.image" :src="scene.image" @close="enlarged = false" />
  </li>
</template>
