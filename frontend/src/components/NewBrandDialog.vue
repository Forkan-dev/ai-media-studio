<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { BookOpen, Laugh } from 'lucide-vue-next'
import BaseButton from './BaseButton.vue'
import BaseDialog from './BaseDialog.vue'
import FormField from './form/FormField.vue'
import { api, type Brand, type Preset } from '@/api'

const open = defineModel<boolean>({ required: true })
const emit = defineEmits<{ created: [brand: Brand] }>()

const icons: Record<string, typeof BookOpen> = { facts: BookOpen, story: Laugh }
const presets = ref<Preset[]>([])
const form = reactive({ preset: 'facts', name: '', niche: '', tone: '' })
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  presets.value = await api.get<Preset[]>('/studio/presets')
})

async function submit() {
  saving.value = true
  error.value = ''
  try {
    const brand = await api.post<Brand>('/studio/brands', form)
    emit('created', brand)
    Object.assign(form, { name: '', niche: '', tone: '' })
    open.value = false
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <BaseDialog v-model="open" title="New brand">
    <form class="space-y-5" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="p in presets"
          :key="p.name"
          type="button"
          class="rounded-lg border p-3 text-left transition"
          :class="form.preset === p.name ? 'border-accent bg-raised' : 'border-line hover:bg-raised'"
          @click="form.preset = p.name"
        >
          <component
            :is="icons[p.name] ?? BookOpen"
            class="size-5"
            :class="form.preset === p.name ? 'text-accent' : 'text-muted'"
          />
          <p class="mt-2 text-sm font-medium capitalize">{{ p.name }}</p>
          <p class="mt-0.5 text-xs text-muted">{{ p.description }}</p>
        </button>
      </div>

      <FormField label="Name">
        <input v-model="form.name" required minlength="2" class="field" placeholder="Space Bits" />
      </FormField>
      <FormField label="Niche">
        <input
          v-model="form.niche"
          required
          minlength="3"
          class="field"
          placeholder="space facts for teens"
        />
      </FormField>
      <FormField label="Tone">
        <textarea
          v-model="form.tone"
          required
          minlength="3"
          rows="2"
          class="field"
          placeholder="curious, playful, easy to follow"
        />
      </FormField>

      <p v-if="error" class="text-sm text-bad">{{ error }}</p>

      <div class="flex justify-end gap-2">
        <BaseButton variant="ghost" type="button" @click="open = false">Cancel</BaseButton>
        <BaseButton type="submit" :loading="saving">Create</BaseButton>
      </div>
    </form>
  </BaseDialog>
</template>

