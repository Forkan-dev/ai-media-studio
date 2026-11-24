<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'

const open = defineModel<boolean>({ required: true })
defineProps<{ title: string }>()

const dialog = ref<HTMLDialogElement>()
watch(open, (value) => (value ? dialog.value?.showModal() : dialog.value?.close()))
</script>

<template>
  <dialog
    ref="dialog"
    class="m-auto w-full max-w-lg rounded-xl border border-line bg-surface p-0 text-fg backdrop:bg-black/50"
    @close="open = false"
    @click.self="open = false"
  >
    <header class="flex h-14 items-center justify-between border-b border-line px-5">
      <h2 class="text-sm font-semibold">{{ title }}</h2>
      <button class="rounded-md p-1 text-muted hover:bg-raised hover:text-fg" @click="open = false">
        <X class="size-4" />
      </button>
    </header>
    <div class="p-5">
      <slot />
    </div>
  </dialog>
</template>
