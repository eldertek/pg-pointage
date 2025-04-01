<template>
  <v-chip
    :color="color"
    size="small"
  >
    {{ label }}
  </v-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status: string | boolean;
  type?: 'active' | 'timesheet' | 'anomaly' | 'report';
  activeLabel?: string;
  inactiveLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'active',
  activeLabel: 'Actif',
  inactiveLabel: 'Inactif'
})

const color = computed(() => {
  if (props.type === 'active') {
    return props.status ? 'success' : 'error'
  }
  if (props.type === 'timesheet') {
    switch (props.status) {
      case 'VALIDATED':
        return 'success'
      case 'REJECTED':
        return 'error'
      default:
        return 'warning'
    }
  }
  if (props.type === 'anomaly') {
    switch (typeof props.status === 'string' ? props.status.toLowerCase() : props.status) {
      case 'résolu':
        return 'success'
      case 'ignoré':
        return 'grey'
      default:
        return 'warning'
    }
  }
  if (props.type === 'report') {
    switch (typeof props.status === 'string' ? props.status.toLowerCase() : props.status) {
      case 'approuvé':
        return 'success'
      case 'rejeté':
        return 'error'
      default:
        return 'warning'
    }
  }
  return 'grey'
})

const label = computed(() => {
  if (props.type === 'active') {
    return props.status ? props.activeLabel : props.inactiveLabel
  }
  return props.status
})
</script> 