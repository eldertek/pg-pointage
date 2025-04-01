<template>
  <v-snackbar
    v-model="show"
    :color="color"
    :timeout="timeout"
    @update:model-value="handleClose"
  >
    {{ text }}
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: boolean;
  text: string;
  color?: string;
  timeout?: number;
}

const props = withDefaults(defineProps<Props>(), {
  color: 'success',
  timeout: 3000
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const show = ref(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  show.value = newValue
})

watch(() => show.value, (newValue) => {
  emit('update:modelValue', newValue)
})

const handleClose = () => {
  show.value = false
}
</script> 