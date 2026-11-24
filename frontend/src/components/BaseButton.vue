<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'primary' | 'ghost'; loading?: boolean }>(), {
  variant: 'primary',
  loading: false,
})
</script>

<template>
  <button
    class="inline-flex h-9 items-center justify-center gap-2 rounded-lg px-3.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
    :class="
      variant === 'primary'
        ? 'bg-accent text-bg hover:brightness-110'
        : 'text-muted hover:bg-raised hover:text-fg'
    "
    :disabled="loading"
  >
    <span
      v-if="loading"
      class="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
    />
    <slot />
  </button>
</template>
