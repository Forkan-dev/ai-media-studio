<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ChevronRight, Plus } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import BaseCard from '@/components/BaseCard.vue'
import NewBrandDialog from '@/components/NewBrandDialog.vue'
import { api, type Brand } from '@/api'

const brands = ref<Brand[]>([])
const error = ref('')
const creating = ref(false)

async function load() {
  try {
    brands.value = await api.get<Brand[]>('/studio/brands')
  } catch (e) {
    error.value = (e as Error).message
  }
}

onMounted(load)
</script>

<template>
  <BaseCard title="Brands">
    <template #actions>
      <BaseButton @click="creating = true"><Plus class="size-4" />New brand</BaseButton>
    </template>

    <p v-if="error" class="text-sm text-bad">{{ error }}</p>

    <ul class="-my-2 divide-y divide-line">
      <li v-for="b in brands" :key="b.slug">
        <RouterLink
          :to="`/studio/${b.slug}`"
          class="group flex w-full items-center justify-between py-3 text-left"
        >
          <div>
            <p class="text-sm font-medium">{{ b.name }}</p>
            <p class="mt-0.5 text-xs text-muted">
              <span class="capitalize">{{ b.preset }}</span> · {{ b.format }} · {{ b.duration }}s
            </p>
          </div>
          <ChevronRight
            class="size-4 text-muted transition group-hover:translate-x-0.5 group-hover:text-fg"
          />
        </RouterLink>
      </li>
    </ul>
  </BaseCard>

  <NewBrandDialog v-model="creating" @created="load" />
</template>
