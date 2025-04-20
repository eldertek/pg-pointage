<template>
  <div class="d-flex align-center">
    <template v-for="action in actions" :key="action.icon">
      <v-btn
        v-if="action.visible"
        icon
        variant="text"
        size="small"
        :color="action.color"
        :to="action.route"
        @click.stop="action.action"
      >
        <v-icon>{{ action.icon }}</v-icon>
        <v-tooltip activator="parent">{{ action.tooltip }}</v-tooltip>
      </v-btn>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { ActionButton, ActionConfig } from '@/composables/useDetailActions'
import { useDetailActions } from '@/composables/useDetailActions'
import { computed } from 'vue'

const props = defineProps<{
  item: any
  config: ActionConfig
}>()

const { getDetailActions } = useDetailActions(props.config)

const actions = computed<ActionButton[]>(() => getDetailActions(props.item))
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-btn--icon[color="primary"]) {
  background-color: transparent !important;
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon[color="error"]) {
  background-color: transparent !important;
  color: #F78C48 !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon[color="warning"]) {
  background-color: transparent !important;
  color: #FB8C00 !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon[color="grey"]) {
  background-color: transparent !important;
  color: #999999 !important;
  opacity: 0.5 !important;
  cursor: default !important;
  pointer-events: none !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}
</style> 