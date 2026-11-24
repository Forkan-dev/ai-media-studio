<script setup lang="ts">
/** Free list of short values: type and press Enter to add, × to remove. */
import { ref } from 'vue'
import { X } from 'lucide-vue-next'

const tags = defineModel<string[]>({ required: true })
defineProps<{ placeholder?: string }>()
const draft = ref('')

function add() {
  const value = draft.value.trim().toLowerCase().replaceAll(' ', '_')
  if (value && !tags.value.includes(value)) tags.value = [...tags.value, value]
  draft.value = ''
}
</script>

<template>
  <div class="field flex h-auto min-h-9 flex-wrap items-center gap-1.5 py-1.5">
    <span
      v-for="t in tags"
      :key="t"
      class="flex h-6 items-center gap-1 rounded-md bg-surface pr-1 pl-2 text-xs"
    >
      {{ t.replaceAll('_', ' ') }}
      <button
        type="button"
        class="text-muted hover:text-fg"
        @click="tags = tags.filter((x) => x !== t)"
      >
        <X class="size-3" />
      </button>
    </span>
    <input
      v-model="draft"
      class="min-w-24 flex-1 bg-transparent text-sm outline-none placeholder:text-muted/60"
      :placeholder="placeholder ?? 'Add…'"
      @keydown.enter.prevent="add"
      @blur="add"
    />
  </div>
</template>
