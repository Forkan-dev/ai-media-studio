<script setup lang="ts">
/** Bottom bar of every gate: redo the step (optionally with instructions for the AI), approve it,
 *  or approve and run to the end without stopping. */
import { ref } from 'vue'
import { Check, FastForward, RotateCcw } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseDialog from '@/components/BaseDialog.vue'

const props = defineProps<{
  busy?: boolean
  redoLabel?: string
  notes?: string | null // null = this step takes no instructions; a string = suggested instructions
}>()
const emit = defineEmits<{ redo: [notes: string]; approve: [auto: boolean] }>()

const dialog = ref(false)
const draft = ref('')

function redo() {
  if (props.notes === null || props.notes === undefined) return emit('redo', '')
  draft.value = props.notes
  dialog.value = true
}
function send() {
  dialog.value = false
  emit('redo', draft.value)
}
</script>

<template>
  <div class="mt-5 flex items-center justify-between border-t border-line pt-4">
    <BaseButton variant="ghost" :disabled="busy" @click="redo">
      <RotateCcw class="size-4" />{{ redoLabel ?? 'Redo' }}
    </BaseButton>
    <div class="flex gap-2">
      <BaseButton
        variant="ghost"
        :disabled="busy"
        title="Approve and finish without stopping"
        @click="emit('approve', true)"
      >
        <FastForward class="size-4" />Run to end
      </BaseButton>
      <BaseButton :loading="busy" @click="emit('approve', false)">
        <Check class="size-4" />Approve
      </BaseButton>
    </div>
  </div>

  <BaseDialog v-model="dialog" title="Redo with instructions">
    <textarea
      v-model="draft"
      rows="7"
      class="field"
      placeholder="Tell the AI what to change, e.g. make the hook shorter, explain the study more simply…"
    />
    <div class="mt-4 flex justify-end gap-2">
      <BaseButton variant="ghost" @click="draft = ''">Clear</BaseButton>
      <BaseButton @click="send"><RotateCcw class="size-4" />Redo</BaseButton>
    </div>
  </BaseDialog>
</template>
