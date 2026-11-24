<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<template>
  <section class="rounded-xl border border-line bg-surface">
    <header v-if="title || $slots.actions" class="flex min-h-14 items-center justify-between border-b border-line px-5 py-3">
      <h2 class="text-sm font-medium">{{ title }}</h2>
      <slot name="actions" />
    </header>
    <div class="p-5">
      <slot />
    </div>
  </section>
</template>
