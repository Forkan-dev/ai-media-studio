<script setup lang="ts">
const on = defineModel<boolean>({ required: true })
defineProps<{ label: string }>()
</script>

<template>
  <button
    type="button"
    class="flex w-full items-center justify-between py-1.5 text-sm"
    :aria-pressed="on"
    @click="on = !on"
  >
    {{ label }}
    <span
      class="relative h-5 w-9 rounded-full transition"
      :class="on ? 'bg-accent' : 'bg-raised ring-1 ring-line'"
    >
      <span
        class="absolute top-0.5 left-0.5 size-4 rounded-full bg-fg transition"
        :class="on && 'translate-x-4'"
      />
    </span>
  </button>
</template>
