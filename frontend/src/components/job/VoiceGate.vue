<script setup lang="ts">
/** Voice gate: listen per scene or all in order; re-record one line (same or edited words). */
import { computed, onUnmounted, ref } from 'vue'
import { Pause, Pencil, Play, RotateCcw } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import type { Scene } from '@/api'

const props = defineProps<{ scenes: Scene[]; pending: number | null }>()
const emit = defineEmits<{ rerecord: [scene: number, text?: string] }>()

const player = new Audio()
const playing = ref<number | null>(null) // 1-based scene
const playAll = ref(false)
const total = computed(() => props.scenes.reduce((sum, s) => sum + (s.seconds ?? 0), 0))

function play(n: number, all = false) {
  if (playing.value === n && !all) return stop()
  const src = props.scenes[n - 1]?.audio
  if (!src) return stop()
  playAll.value = all
  playing.value = n
  player.src = src
  player.play()
}
function stop() {
  player.pause()
  playing.value = null
  playAll.value = false
}
player.onended = () =>
  playAll.value && playing.value! < props.scenes.length ? play(playing.value! + 1, true) : stop()
onUnmounted(stop)

const editing = ref<number | null>(null)
const text = ref('')
const dialog = ref(false)
function edit(n: number) {
  editing.value = n
  text.value = props.scenes[n - 1]!.narration
  dialog.value = true
}
function rerecordEdited() {
  if (editing.value !== null) emit('rerecord', editing.value, text.value)
  dialog.value = false
}
const time = (s: number) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, '0')}`
</script>

<template>
  <BaseCard title="Voice">
    <template #actions>
      <BaseButton variant="ghost" @click="playAll ? stop() : play(1, true)">
        <component :is="playAll ? Pause : Play" class="size-4" />
        {{ playAll ? 'Stop' : 'Play all' }} · {{ time(total) }}
      </BaseButton>
    </template>

    <ol class="-my-2 divide-y divide-line">
      <li v-for="(s, i) in scenes" :key="i" class="group flex items-center gap-4 py-2.5">
        <button
          class="grid size-9 shrink-0 place-items-center rounded-full transition"
          :class="playing === i + 1 ? 'bg-accent text-bg' : 'bg-raised hover:text-fg'"
          :disabled="!s.audio || pending === i + 1"
          @click="play(i + 1)"
        >
          <span
            v-if="pending === i + 1"
            class="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
          />
          <component :is="playing === i + 1 ? Pause : Play" v-else class="size-4" />
        </button>
        <p class="flex-1 text-sm" :class="playing === i + 1 ? 'text-fg' : 'text-muted'">{{ s.narration }}</p>
        <span class="w-10 text-right text-xs tabular-nums text-muted">{{ s.seconds ? time(s.seconds) : '' }}</span>
        <div class="flex opacity-0 transition group-hover:opacity-100">
          <button
            class="grid size-8 place-items-center rounded-lg text-muted hover:bg-raised hover:text-fg"
            title="Record again"
            :disabled="pending !== null"
            @click="emit('rerecord', i + 1)"
          >
            <RotateCcw class="size-4" />
          </button>
          <button
            class="grid size-8 place-items-center rounded-lg text-muted hover:bg-raised hover:text-fg"
            title="Edit words and record"
            :disabled="pending !== null"
            @click="edit(i + 1)"
          >
            <Pencil class="size-4" />
          </button>
        </div>
      </li>
    </ol>
  </BaseCard>

  <BaseDialog v-model="dialog" :title="`Scene ${editing}`">
    <textarea v-model="text" rows="4" class="field" />
    <div class="mt-4 flex justify-end">
      <BaseButton @click="rerecordEdited"><RotateCcw class="size-4" />Record</BaseButton>
    </div>
  </BaseDialog>
</template>
