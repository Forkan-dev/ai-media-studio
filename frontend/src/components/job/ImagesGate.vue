<script setup lang="ts">
/** Storyboard gate (label "Test": draw one scene before drawing all) and images gate (label "Redraw",
 *  plus an on-demand vision check of every image). */
import { ScanSearch } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import SceneCard from './SceneCard.vue'
import type { Scene } from '@/api'

defineProps<{
  scenes: Scene[]
  styles: string[]
  vertical: boolean
  pending: number | null // scene being drawn
  checking: boolean
  busy: boolean
  mode: 'storyboard' | 'images'
}>()
const emit = defineEmits<{
  draw: [scene: number, prompt: string, style: string]
  save: [scene: number, prompt: string, style: string]
  check: []
}>()
</script>

<template>
  <BaseCard :title="mode === 'storyboard' ? 'Scenes' : 'Images'">
    <template v-if="mode === 'images'" #actions>
      <BaseButton variant="ghost" :loading="checking" :disabled="busy" @click="emit('check')">
        <ScanSearch v-if="!checking" class="size-4" />Check images
      </BaseButton>
    </template>
    <ol class="grid gap-4 xl:grid-cols-2">
      <SceneCard
        v-for="(s, i) in scenes"
        :key="i"
        :scene="s"
        :number="i + 1"
        :styles="styles"
        :vertical="vertical"
        :pending="pending === i + 1"
        :disabled="busy"
        :label="mode === 'storyboard' ? 'Test' : 'Redraw'"
        @draw="(prompt, style) => emit('draw', i + 1, prompt, style)"
        @save="(prompt, style) => emit('save', i + 1, prompt, style)"
      />
    </ol>
  </BaseCard>
</template>
