<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<!-- a div, not a <label>: a label forwards clicks to its first button (e.g. a tag's ×) -->
<template>
  <div>
    <span class="mb-1.5 block text-xs text-muted">{{ label }}</span>
    <slot />
  </div>
</template>
