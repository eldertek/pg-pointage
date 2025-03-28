<template>
  <v-dialog 
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800px"
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
              />
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

interface ListItem {
  id: number;
  name: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization: number;
  phone_number: string;
  is_active: boolean;
  employee_id: string;
  date_joined: string;
  organization_name: string;
  scan_preference: string;
  simplified_mobile_view: boolean;
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

const getItemTitle = (item: ListItem) => item.name

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