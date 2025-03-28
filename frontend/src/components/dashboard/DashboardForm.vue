<template>
  <v-form ref="form" @submit.prevent="$emit('submit')" class="dashboard-form">
    <div v-if="$slots.header" class="form-header">
      <slot name="header"></slot>
    </div>
    
    <FormErrors :errors="errors" />
    
    <v-row>
      <slot></slot>
    </v-row>
  </v-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { VForm } from 'vuetify/components'
import { typography, spacing } from '@/styles/typography'
import FormErrors from '@/components/common/FormErrors.vue'

const props = defineProps({
  errors: {
    type: Object as () => Record<string, string[]>,
    default: () => ({})
  }
})

const form = ref<any>(null)

const validate = async () => {
  if (!form.value) return false
  const { valid } = await form.value.validate()
  return valid
}

const reset = () => {
  if (form.value) {
    form.value.reset()
  }
}

defineExpose({
  validate,
  reset
})

defineEmits(['submit'])
</script>

<style scoped>
.dashboard-form {
  font-family: v-bind('typography.body.family');
  font-size: v-bind('typography.body.size');
  font-weight: v-bind('typography.body.weight');
  line-height: v-bind('typography.body.lineHeight');
}

.form-header {
  margin-bottom: v-bind('spacing.text.section');
  padding-bottom: v-bind('spacing.text.paragraph');
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.form-header :deep(h2) {
  font-family: v-bind('typography.h2.family');
  font-size: v-bind('typography.h2.size');
  font-weight: v-bind('typography.h2.weight');
  line-height: v-bind('typography.h2.lineHeight');
  margin: 0;
}

.v-row {
  margin: 0;
  padding: v-bind('spacing.text.section') 0;
}

:deep(.v-label) {
  font-family: v-bind('typography.body.family');
  font-size: v-bind('typography.body.size');
  font-weight: v-bind('typography.body.weight');
}

:deep(.v-input__details) {
  font-family: v-bind('typography.small.family');
  font-size: v-bind('typography.small.size');
  font-weight: v-bind('typography.small.weight');
  line-height: v-bind('typography.small.lineHeight');
}
</style> 