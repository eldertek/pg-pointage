<template>
  <v-dialog v-model="dialogState.show" max-width="400">
    <v-card>
      <v-card-title>{{ dialogState.title }}</v-card-title>
      <v-card-text>{{ dialogState.message }}</v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          color="grey" 
          variant="text" 
          @click="dialogState.show = false"
          :disabled="dialogState.loading"
        >
          {{ dialogState.cancelText }}
        </v-btn>
        <v-btn 
          :color="dialogState.confirmColor"
          variant="text" 
          @click="handleConfirm"
          :loading="dialogState.loading"
        >
          {{ dialogState.confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { useConfirmDialog } from '@/utils/dialogs'

const { dialogState, handleConfirm } = useConfirmDialog()
</script> 