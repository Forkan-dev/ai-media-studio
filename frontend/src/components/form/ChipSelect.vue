<script setup lang="ts">
/** Pick several values from a fixed list. */
const selected = defineModel<string[]>({ required: true })
defineProps<{ options: string[] }>()

function toggle(value: string) {
  selected.value = selected.value.includes(value)
    ? selected.value.filter((v) => v !== value)
    : [...selected.value, value]
}
</script>

<template>
  <div class="flex flex-wrap gap-1.5">
    <button
      v-for="o in options"
      :key="o"
      type="button"
      class="h-7 rounded-md px-2.5 text-xs transition"
      :class="
        selected.includes(o)
          ? 'bg-accent/15 text-accent ring-1 ring-accent/40'
          : 'bg-raised text-muted hover:text-fg'
      "
      @click="toggle(o)"
    >
      {{ o.replaceAll('_', ' ') }}
    </button>
  </div>
</template>
