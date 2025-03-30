<template>
  <v-dialog 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800px"
    persistent
  >
    <v-card class="form-dialog">
      <div class="form-dialog-header">
        <div class="form-dialog-title">
          <span class="text-h4">{{ title }}</span>
          <span class="text-subtitle">{{ subtitle }}</span>
        </div>
        <v-btn
          icon
          variant="text"
          size="small"
          color="grey"
          @click="$emit('update:modelValue', false)"
          class="close-button"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </div>
      <v-divider></v-divider>
      <v-card-text>
        <DashboardForm ref="form" @submit="handleSubmit">
          <v-row>
            <v-col cols="12">
              <v-autocomplete
                v-model="selectedItem"
                :items="items"
                item-value="id"
                :label="label"
                :placeholder="placeholder"
                return-object
                :loading="loading"
                :no-data-text="noDataText"
                :item-title="getItemTitle"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:prepend>
                      <v-icon :icon="itemIcon" class="mr-2"></v-icon>
                    </template>
                    <v-list-item-title>{{ getItemTitle(item.raw) }}</v-list-item-title>
                    <v-list-item-subtitle>
                      <slot name="item-subtitle" :item="item.raw">
                        {{ item.raw.email }}
                      </slot>
                    </v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-autocomplete>
            </v-col>
          </v-row>
        </DashboardForm>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          color="grey" 
          variant="text" 
          @click="$emit('update:modelValue', false)"
          class="action-button"
        >
          Annuler
        </v-btn>
        <v-btn 
          color="primary" 
          variant="text" 
          @click="handleSubmit"
          :disabled="!selectedItem"
          :loading="saving"
          class="action-button"
        >
          Assigner
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import { typography } from '@/styles/typography'

export interface ListItem {
  address: any;
  city: any;
  is_active: any;
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  organization: number;
  employee?: number;
  role?: string;
  site_name?: string;
  employee_name?: string;
  name?: string;
}

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: 'Sélectionnez un élément à assigner'
  },
  items: {
    type: Array as () => ListItem[],
    required: true,
    default: () => []
  },
  itemIcon: {
    type: String,
    default: 'mdi-account'
  },
  label: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: 'Rechercher un employé...'
  },
  loading: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  },
  noDataText: {
    type: String,
    default: 'Aucun élément disponible'
  }
})

const emit = defineEmits(['update:modelValue', 'assign'])

const selectedItem = ref<ListItem | null>(null)
const form = ref(null)

const getItemTitle = (item: ListItem) => {
  if (item.name) {
    return item.name;
  }
  return `${item.first_name} ${item.last_name}`;
}

const handleSubmit = async () => {
  if (!selectedItem.value) return
  emit('assign', selectedItem.value)
}

// Reset le formulaire quand le dialog se ferme
watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    selectedItem.value = null
  }
})
</script>

<style scoped>
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

/* Style des éléments de la liste */
:deep(.v-list-item) {
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

:deep(.v-list-item:hover) {
  background-color: rgba(0, 52, 110, 0.04);
}

:deep(.v-list-item-title) {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 4px;
}

:deep(.v-list-item-subtitle) {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
}

:deep(.v-list-item .v-icon) {
  color: #00346E;
  opacity: 0.8;
}

/* Style de l'autocomplete */
:deep(.v-autocomplete) {
  .v-field__input {
    padding: 8px 12px;
  }
  
  .v-field__outline {
    border-color: rgba(0, 0, 0, 0.12);
  }
  
  &:hover .v-field__outline {
    border-color: rgba(0, 0, 0, 0.24);
  }
  
  &.v-field--focused .v-field__outline {
    border-color: #00346E;
  }
}

/* Style des puces */
:deep(.v-chip.v-chip--size-x-small) {
  font-size: 0.625rem;
  height: 20px;
}

.gap-2 {
  gap: 8px;
}

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
</style> 