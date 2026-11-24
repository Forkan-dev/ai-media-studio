<script setup lang="ts">
import BaseCard from '@/components/BaseCard.vue'
import ChipSelect from '@/components/form/ChipSelect.vue'
import FormField from '@/components/form/FormField.vue'
import type { BrandConfig, BrandOptions } from '@/api'

const config = defineModel<BrandConfig>({ required: true })
defineProps<{ options: BrandOptions }>()
</script>

<template>
  <BaseCard title="Look">
    <div class="space-y-4">
      <FormField label="Camera motions">
        <ChipSelect v-model="config.look.motions" :options="options.motions" />
      </FormField>
      <FormField label="Transitions">
        <ChipSelect v-model="config.look.transitions" :options="options.transitions" />
      </FormField>
      <div class="flex flex-wrap gap-4">
        <FormField label="Transition (s)">
          <input
            v-model.number="config.look.transition_seconds"
            type="number"
            step="0.1"
            min="0"
            class="field w-24"
          />
        </FormField>
        <FormField label="Caption size">
          <input v-model.number="config.look.caption_font_size" type="number" class="field w-24" />
        </FormField>
        <FormField label="Words per caption">
          <input
            v-model.number="config.look.caption_max_words"
            type="number"
            min="1"
            max="8"
            class="field w-24"
          />
        </FormField>
      </div>
    </div>
  </BaseCard>
</template>
