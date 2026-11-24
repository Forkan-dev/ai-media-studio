<script setup lang="ts">
/** Research gate: the facts the script is built on. Edit, remove or add facts, then approve. */
import { ref, toRaw } from 'vue'
import { ExternalLink, Plus, X } from 'lucide-vue-next'
import BaseCard from '@/components/BaseCard.vue'
import FormField from '@/components/form/FormField.vue'
import type { ResearchResult } from '@/api'

const props = defineProps<{ research: ResearchResult }>()
// props are reactive proxies, which structuredClone cannot copy: clone the raw object
const draft = ref<ResearchResult>(structuredClone(toRaw(props.research)))
const r = draft.value.research

/** The edited research, for the parent to save before approving. */
defineExpose({ draft })
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[1fr_20rem]">
    <BaseCard title="Facts">
      <div class="space-y-5">
        <FormField label="Core fact">
          <textarea v-model="r.core_fact.text" rows="2" class="field" />
        </FormField>

        <FormField label="Established">
          <div class="space-y-2">
            <div v-for="(f, i) in r.established" :key="i" class="flex gap-2">
              <textarea v-model="f.text" rows="2" class="field" />
              <button
                class="grid size-9 shrink-0 place-items-center rounded-lg text-muted hover:bg-raised hover:text-bad"
                @click="r.established.splice(i, 1)"
              >
                <X class="size-4" />
              </button>
            </div>
            <button
              class="flex h-8 items-center gap-1.5 rounded-lg px-2 text-xs text-muted hover:bg-raised hover:text-fg"
              @click="r.established.push({ text: '', sources: [] })"
            >
              <Plus class="size-3.5" />Add fact
            </button>
          </div>
        </FormField>

        <FormField v-if="r.surprising_details.length" label="Surprising details">
          <div class="space-y-2">
            <textarea
              v-for="(d, i) in r.surprising_details"
              :key="i"
              v-model="d.text"
              rows="2"
              class="field"
            />
          </div>
        </FormField>

        <FormField v-if="r.debated.length" label="Debated (used only as “some studies suggest”)">
          <ul class="space-y-1.5 text-sm text-muted">
            <li v-for="(d, i) in r.debated" :key="i">{{ d.text }}</li>
          </ul>
        </FormField>
      </div>
    </BaseCard>

    <BaseCard title="Sources">
      <ol class="space-y-2">
        <li v-for="(url, i) in draft.urls" :key="url" class="flex gap-2 text-xs">
          <span class="w-4 shrink-0 text-muted tabular-nums">{{ i + 1 }}</span>
          <a :href="url" target="_blank" class="flex min-w-0 items-center gap-1 text-muted hover:text-fg">
            <span class="truncate">{{ url.replace(/^https?:\/\/(www\.)?/, '') }}</span>
            <ExternalLink class="size-3 shrink-0" />
          </a>
        </li>
      </ol>
    </BaseCard>
  </div>
</template>
