<script setup lang="ts">
import BaseCard from '@/components/BaseCard.vue'
import FormField from '@/components/form/FormField.vue'
import SegmentedControl from '@/components/form/SegmentedControl.vue'
import type { BrandConfig, BrandOptions } from '@/api'

const config = defineModel<BrandConfig>({ required: true })
defineProps<{ options: BrandOptions }>()
</script>

<template>
  <BaseCard title="Basics">
    <div class="space-y-4">
      <FormField label="Name"><input v-model="config.name" class="field" /></FormField>
      <FormField label="Niche"><input v-model="config.niche" class="field" /></FormField>
      <FormField label="Tone"><textarea v-model="config.tone" rows="3" class="field" /></FormField>
      <div class="flex flex-wrap items-end gap-4">
        <FormField label="Format">
          <SegmentedControl v-model="config.format" :options="options.formats" />
        </FormField>
        <FormField label="Length (s)">
          <input v-model.number="config.duration" type="number" min="10" class="field w-24" />
        </FormField>
        <FormField label="Language">
          <input v-model="config.language" class="field w-20" />
        </FormField>
      </div>
    </div>
  </BaseCard>
</template>
