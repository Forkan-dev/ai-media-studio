<script setup lang="ts">
import BaseCard from '@/components/BaseCard.vue'
import ChipSelect from '@/components/form/ChipSelect.vue'
import FormField from '@/components/form/FormField.vue'
import SegmentedControl from '@/components/form/SegmentedControl.vue'
import TagInput from '@/components/form/TagInput.vue'
import ToggleSwitch from '@/components/form/ToggleSwitch.vue'
import type { BrandConfig, BrandOptions } from '@/api'

const config = defineModel<BrandConfig>({ required: true })
defineProps<{ options: BrandOptions }>()
</script>

<template>
  <BaseCard title="Script">
    <div class="space-y-4">
      <FormField label="Mode">
        <SegmentedControl v-model="config.script_mode" :options="options.script_modes" />
      </FormField>
      <div class="divide-y divide-line rounded-lg border border-line px-3">
        <ToggleSwitch v-model="config.pipeline.research" label="Web research" />
        <ToggleSwitch v-model="config.pipeline.fact_check" label="Fact-check" />
      </div>
      <FormField label="Structures">
        <TagInput v-model="config.script_structures" placeholder="story, myth_vs_fact…" />
      </FormField>
      <FormField label="Review criteria">
        <ChipSelect v-model="config.review_criteria" :options="options.review_criteria" />
      </FormField>
      <FormField label="Topic criteria">
        <TagInput v-model="config.topic_criteria" placeholder="curiosity, visual…" />
      </FormField>
      <div class="flex gap-4">
        <FormField label="Pass score">
          <input
            v-model.number="config.min_quality_score"
            type="number"
            min="1"
            max="10"
            step="0.5"
            class="field w-24"
          />
        </FormField>
        <FormField label="Reviewer model" class="flex-1">
          <input v-model="config.review_model" class="field" placeholder="default" />
        </FormField>
      </div>
    </div>
  </BaseCard>
</template>
