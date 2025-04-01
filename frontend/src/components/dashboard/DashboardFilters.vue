<template>
  <v-row>
    <slot></slot>
    <v-col cols="12" class="d-flex align-center">
      <v-btn 
        color="error" 
        variant="outlined" 
        prepend-icon="mdi-refresh"
        class="px-4"
        @click="$emit('reset')"
      >
        Réinitialiser les filtres
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
}
</style> 