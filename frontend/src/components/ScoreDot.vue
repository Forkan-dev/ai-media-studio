<script setup lang="ts">
/** A 1-10 score as a colored dot + number: green 8+, amber 6-8, red below 6. */
const props = defineProps<{ score: number }>()
const color = () => (props.score >= 8 ? 'bg-good' : props.score >= 6 ? 'bg-warn' : 'bg-bad')
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-xs tabular-nums text-muted">
    <span class="size-1.5 rounded-full" :class="color()" />
    {{ score.toFixed(1) }}
  </span>
</template>
