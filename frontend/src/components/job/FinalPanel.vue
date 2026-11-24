<script setup lang="ts">
/** Finished video: player, thumbnail and the publishing text with copy buttons. */
import { ref } from 'vue'
import { Check, Copy, Download } from 'lucide-vue-next'
import BaseCard from '@/components/BaseCard.vue'
import type { JobPage } from '@/api'

defineProps<{ page: JobPage; vertical: boolean }>()
const copied = ref('')

async function copy(label: string, text: string) {
  await navigator.clipboard.writeText(text)
  copied.value = label
  setTimeout(() => (copied.value = ''), 1500)
}
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[auto_1fr]">
    <BaseCard>
      <video
        v-if="page.video"
        :src="page.video"
        controls
        class="rounded-lg bg-black"
        :class="vertical ? 'h-[32rem]' : 'w-[36rem]'"
      />
      <a
        v-if="page.video"
        :href="page.video"
        download
        class="mt-3 flex items-center justify-center gap-2 text-xs text-muted hover:text-fg"
      >
        <Download class="size-3.5" />Download
      </a>
    </BaseCard>

    <div class="space-y-5">
      <BaseCard v-if="page.metadata" title="Publishing">
        <div class="space-y-4 text-sm">
          <div v-for="[label, text] in [
            ['Title', page.metadata.youtube_title],
            ['Description', page.metadata.youtube_description],
            ['Tags', page.metadata.tags.join(', ')],
          ]" :key="label" class="group">
            <div class="mb-1 flex items-center justify-between">
              <span class="text-xs text-muted">{{ label }}</span>
              <button class="text-muted hover:text-fg" @click="copy(label!, text!)">
                <Check v-if="copied === label" class="size-3.5 text-good" />
                <Copy v-else class="size-3.5" />
              </button>
            </div>
            <p class="whitespace-pre-line">{{ text }}</p>
          </div>
        </div>
      </BaseCard>

      <BaseCard v-if="page.thumbnail?.image" title="Thumbnail">
        <img :src="page.thumbnail.image" class="rounded-lg" :class="vertical ? 'h-64' : 'w-80'" />
      </BaseCard>
    </div>
  </div>
</template>
