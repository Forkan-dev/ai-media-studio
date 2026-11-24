<script setup lang="ts">
/** Pick one value from a few options. */
const value = defineModel<string>({ required: true })
defineProps<{ options: string[] }>()
</script>

<template>
  <div class="inline-flex rounded-lg bg-raised p-0.5">
    <button
      v-for="o in options"
      :key="o"
      type="button"
      class="h-8 rounded-md px-3 text-sm capitalize transition"
      :class="value === o ? 'bg-surface text-fg shadow-sm' : 'text-muted hover:text-fg'"
      @click="value = o"
    >
      {{ o }}
    </button>
  </div>
</template>
