<template>
  <v-row>
    <slot></slot>
    <v-col cols="12" class="d-flex align-center justify-end">
      <v-btn
        color="error"
        variant="outlined"
        prepend-icon="mdi-refresh"
        class="px-4"
        @click="$emit('reset')"
      >
        {{ $t('common.resetFilters') }}
      </v-btn>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">
defineEmits(['reset'])
</script>

<style scoped>
.v-row {
  margin: 0;
  gap: 16px;
}

.v-col {
  padding: 8px;
}
</style>