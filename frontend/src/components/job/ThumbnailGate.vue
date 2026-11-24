<script setup lang="ts">
/** Thumbnail gate: pick one of the AI texts or type your own; the text is redrawn in seconds. */
import { ref } from 'vue'
import { Sparkles, Type } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import type { JobPage } from '@/api'

const props = defineProps<{ thumbnail: NonNullable<JobPage['thumbnail']>; vertical: boolean; saving: boolean }>()
const emit = defineEmits<{ setText: [text: string] }>()
const own = ref('')
</script>

<template>
  <div class="grid gap-5 lg:grid-cols-[auto_1fr]">
    <BaseCard>
      <img
        v-if="thumbnail.image"
        :src="thumbnail.image"
        class="rounded-lg"
        :class="vertical ? 'h-[28rem]' : 'w-[32rem]'"
      />
    </BaseCard>

    <BaseCard title="Text">
      <div class="space-y-2">
        <button
          v-for="t in thumbnail.plan.text_options"
          :key="t"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition"
          :class="t === props.thumbnail.plan.text ? 'bg-accent/15 text-accent' : 'bg-raised hover:text-fg'"
          :disabled="saving"
          @click="emit('setText', t)"
        >
          <Sparkles class="size-3.5 shrink-0" />{{ t }}
        </button>
      </div>
      <form class="mt-4 flex gap-2 border-t border-line pt-4" @submit.prevent="own && emit('setText', own)">
        <input v-model="own" maxlength="40" class="field flex-1 uppercase" placeholder="Your own text" />
        <BaseButton type="submit" variant="ghost" :loading="saving"><Type class="size-4" /></BaseButton>
      </form>
    </BaseCard>
  </div>
</template>
