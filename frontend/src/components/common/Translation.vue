<template>
  <span>{{ translatedText }}</span>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  keyPath: {
    type: String,
    required: true
  },
  params: {
    type: Object,
    default: () => ({})
  },
  fallback: {
    type: String,
    default: ''
  }
});

const { t } = useI18n();

const translatedText = computed(() => {
  try {
    return t(props.keyPath, props.params);
  } catch (error) {
    console.warn(`Translation key not found: ${props.keyPath}`);
    return props.fallback || props.keyPath;
  }
});
</script>
