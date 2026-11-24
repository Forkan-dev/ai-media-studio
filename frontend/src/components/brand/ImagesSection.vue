<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronDown, Plus, Star, Trash2 } from 'lucide-vue-next'
import BaseCard from '@/components/BaseCard.vue'
import FormField from '@/components/form/FormField.vue'
import type { BrandConfig } from '@/api'

const config = defineModel<BrandConfig>({ required: true })

const selected = ref(config.value.images.default_style)
const style = computed(() => config.value.images.styles[selected.value])
const advanced = ref(false)
const newName = ref<string | null>(null) // null = not adding

function addStyle() {
  const name = newName.value?.trim().toLowerCase().replaceAll(' ', '_')
  newName.value = null
  if (!name || config.value.images.styles[name] || !style.value) return
  config.value.images.styles[name] = { ...style.value } // starts as a copy of the current style
  selected.value = name
}

function removeStyle() {
  delete config.value.images.styles[selected.value]
  selected.value = config.value.images.default_style
}
</script>

<template>
  <BaseCard title="Image styles">
    <div class="space-y-4">
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-for="(_, name) in config.images.styles"
          :key="name"
          type="button"
          class="flex h-7 items-center gap-1.5 rounded-md px-2.5 text-xs transition"
          :class="selected === name ? 'bg-raised text-fg ring-1 ring-line' : 'text-muted hover:text-fg'"
          @click="selected = name"
        >
          <Star
            v-if="config.images.default_style === name"
            class="size-3 fill-accent text-accent"
          />
          {{ String(name).replaceAll('_', ' ') }}
        </button>
        <input
          v-if="newName !== null"
          v-model="newName"
          class="field h-7 w-36 text-xs"
          placeholder="style name"
          autofocus
          @keydown.enter.prevent="addStyle"
          @keydown.esc="newName = null"
          @blur="addStyle"
        />
        <button
          v-else
          type="button"
          class="grid size-7 place-items-center rounded-md text-muted hover:bg-raised hover:text-fg"
          title="Add style"
          @click="newName = ''"
        >
          <Plus class="size-4" />
        </button>
      </div>

      <template v-if="style">
        <FormField label="Main character">
          <textarea v-model="style.character" rows="2" class="field" />
        </FormField>
        <FormField label="Other people">
          <input v-model="style.others" class="field" />
        </FormField>
        <FormField label="Style words">
          <textarea v-model="style.style" rows="3" class="field" />
        </FormField>
        <FormField label="Avoid">
          <textarea v-model="style.negative" rows="2" class="field" />
        </FormField>

        <div class="flex items-center justify-between">
          <div class="flex gap-1">
            <button
              v-if="config.images.default_style !== selected"
              type="button"
              class="flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-xs text-muted hover:bg-raised hover:text-fg"
              @click="config.images.default_style = selected"
            >
              <Star class="size-3.5" />Make default
            </button>
            <button
              v-if="config.images.default_style !== selected"
              type="button"
              class="grid size-8 place-items-center rounded-lg text-muted hover:bg-raised hover:text-bad"
              title="Delete style"
              @click="removeStyle"
            >
              <Trash2 class="size-3.5" />
            </button>
          </div>
          <button
            type="button"
            class="flex items-center gap-1 text-xs text-muted hover:text-fg"
            @click="advanced = !advanced"
          >
            Advanced
            <ChevronDown class="size-3.5 transition" :class="advanced && 'rotate-180'" />
          </button>
        </div>

        <div v-if="advanced" class="grid grid-cols-2 gap-4 border-t border-line pt-4">
          <FormField label="Checkpoint" class="col-span-2">
            <input v-model="config.images.checkpoint" class="field" />
          </FormField>
          <FormField label="LoRA">
            <input v-model="config.images.lora" class="field" />
          </FormField>
          <FormField label="LoRA weight">
            <input v-model.number="style.lora_weight" type="number" step="0.05" class="field" />
          </FormField>
          <FormField label="Steps">
            <input v-model.number="config.images.steps" type="number" class="field" />
          </FormField>
          <FormField label="CFG">
            <input v-model.number="config.images.cfg" type="number" step="0.5" class="field" />
          </FormField>
          <FormField label="Sampler">
            <input v-model="config.images.sampler" class="field" />
          </FormField>
          <FormField label="Scheduler">
            <input v-model="config.images.scheduler" class="field" />
          </FormField>
        </div>
      </template>
    </div>
  </BaseCard>
</template>
