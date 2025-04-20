<!-- Title.vue -->
<template>
  <component
    :is="tag"
    :class="[`title-${level}`, className]"
    v-bind="$attrs"
  >
    <slot></slot>
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { typography } from '@/styles/typography';

export interface TitleProps {
  level?: 1 | 2 | 3;
  className?: string;
}

const props = withDefaults(defineProps<TitleProps>(), {
  level: 1,
  className: '',
});

const tag = computed(() => `h${props.level}`);

defineOptions({
  name: 'AppTitle',
})
</script>

<style scoped>
.title-1 {
  font-family: v-bind('typography.h1.family');
  font-size: v-bind('typography.h1.size');
  font-weight: v-bind('typography.h1.weight');
  line-height: v-bind('typography.h1.lineHeight');
}

.title-2 {
  font-family: v-bind('typography.h2.family');
  font-size: v-bind('typography.h2.size');
  font-weight: v-bind('typography.h2.weight');
  line-height: v-bind('typography.h2.lineHeight');
}

.title-3 {
  font-family: v-bind('typography.h3.family');
  font-size: v-bind('typography.h3.size');
  font-weight: v-bind('typography.h3.weight');
  line-height: v-bind('typography.h3.lineHeight');
}
</style> 