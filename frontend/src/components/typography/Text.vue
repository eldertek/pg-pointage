<!-- Text.vue -->
<template>
  <p
    :class="[
      'text',
      { 'text-small': small },
      { 'text-button': button },
      className
    ]"
    v-bind="$attrs"
  >
    <slot></slot>
  </p>
</template>

<script setup lang="ts">
import { typography, spacing } from '@/styles/typography';

export interface TextProps {
  small?: boolean;
  button?: boolean;
  className?: string;
}

withDefaults(defineProps<TextProps>(), {
  small: false,
  button: false,
  className: '',
});

defineOptions({
  name: 'AppText',
})
</script>

<style scoped>
.text {
  font-family: v-bind('typography.body.family');
  font-size: v-bind('typography.body.size');
  font-weight: v-bind('typography.body.weight');
  line-height: v-bind('typography.body.lineHeight');
  margin-bottom: v-bind('spacing.text.paragraph');
}

.text-small {
  font-family: v-bind('typography.small.family');
  font-size: v-bind('typography.small.size');
  font-weight: v-bind('typography.small.weight');
  line-height: v-bind('typography.small.lineHeight');
}

.text-button {
  font-family: v-bind('typography.button.family');
  font-size: v-bind('typography.button.size');
  font-weight: v-bind('typography.button.weight');
  line-height: v-bind('typography.button.lineHeight');
}
</style> 