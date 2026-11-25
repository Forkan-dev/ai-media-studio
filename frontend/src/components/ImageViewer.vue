<script setup lang="ts">
/** Full-screen view of one image; click anywhere or press Esc to close. */
import { onMounted, onUnmounted } from 'vue'

defineProps<{ src: string }>()
const emit = defineEmits<{ close: [] }>()
const onKey = (e: KeyboardEvent) => e.key === 'Escape' && emit('close')
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 grid cursor-zoom-out place-items-center bg-black/85 p-6"
      @click="emit('close')"
    >
      <img :src="src" class="max-h-full max-w-full rounded-lg shadow-2xl" />
    </div>
  </Teleport>
</template>
