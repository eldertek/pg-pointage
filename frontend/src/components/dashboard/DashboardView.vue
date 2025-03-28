<template>
  <div>
    <!-- En-tête avec titre et actions -->
    <div class="d-flex justify-space-between align-center mb-4">
      <div>
        <Title :level="1">{{ title }}</Title>
        <slot name="subtitle"></slot>
      </div>
      <div class="d-flex gap-2">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- Filtres -->
    <v-card v-if="$slots.filters" class="mb-4">
      <v-card-title>Filtres</v-card-title>
      <v-card-text>
        <slot name="filters"></slot>
      </v-card-text>
    </v-card>

    <!-- Contenu principal -->
    <v-card>
      <slot></slot>
    </v-card>

    <!-- Dialog de formulaire -->
    <v-dialog v-model="showForm" max-width="800px">
      <v-card class="form-dialog">
        <div class="form-dialog-header">
          <div class="form-dialog-title">
            <span class="text-h4">{{ formTitle }}</span>
            <span class="text-subtitle">Remplissez les informations ci-dessous</span>
          </div>
          <v-btn
            icon
            variant="text"
            size="small"
            color="grey"
            @click="closeForm"
            class="close-button"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>
        <v-divider></v-divider>
        <v-card-text>
          <v-container>
            <slot name="form"></slot>
          </v-container>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn 
            color="grey" 
            variant="text" 
            @click="closeForm"
            class="action-button"
          >
            Annuler
          </v-btn>
          <v-btn 
            color="primary" 
            variant="text" 
            @click="$emit('save')"
            :loading="saving"
            class="action-button"
          >
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation -->
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Title } from '@/components/typography'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { typography } from '@/styles/typography'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  formTitle: {
    type: String,
    default: ''
  },
  saving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['save'])

const showForm = ref(false)

const closeForm = () => {
  showForm.value = false
}

defineExpose({
  showForm
})
</script>

<style scoped>
/* Style des boutons colorés */
:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}

:deep(.v-btn[color="success"]) {
  background-color: #00346E !important;
  color: white !important;
}

/* Style des boutons icônes colorés */
:deep(.v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-btn--icon[color="success"]) {
  color: #00346E !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}

/* Espacement entre les éléments */
.gap-2 {
  gap: 8px;
}

/* Style de la boîte de dialogue */
.form-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.form-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.5rem;
  background-color: #f8f9fa;
}

.form-dialog-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-dialog-title .text-h4 {
  font-family: v-bind('typography.h2.family');
  font-size: v-bind('typography.h2.size');
  font-weight: v-bind('typography.h2.weight');
  line-height: v-bind('typography.h2.lineHeight');
  color: #00346E;
  margin: 0;
}

.form-dialog-title .text-subtitle {
  font-family: v-bind('typography.body.family');
  font-size: v-bind('typography.body.size');
  font-weight: v-bind('typography.body.weight');
  line-height: v-bind('typography.body.lineHeight');
  color: #666;
}

.close-button {
  margin-top: -0.5rem;
  margin-right: -0.5rem;
}

.v-card-text {
  padding: 2rem 1.5rem;
}

.v-card-actions {
  padding: 1rem 1.5rem;
}

.action-button {
  font-family: v-bind('typography.button.family');
  font-size: v-bind('typography.button.size');
  font-weight: v-bind('typography.button.weight');
  line-height: v-bind('typography.button.lineHeight');
  padding: 0.5rem 1rem;
}

:deep(.v-divider) {
  margin: 0;
}
</style> 