<template>
  <v-data-table
    v-bind="$attrs"
    :headers="headers"
    :items="items"
    :loading="loading"
    :items-per-page-options="[5, 10, 20, 50, 100]"
    :items-per-page="itemsPerPage"
    :no-data-text="noDataText || 'Aucune donnée trouvée'"
    :loading-text="loadingText || 'Chargement...'"
    :items-per-page-text="'Lignes par page'"
    :page-text="'{0}-{1} sur {2}'"
    @click:row="handleRowClick"
  >
    <template v-for="(_, name) in $slots" v-slot:[name]="slotData">
      <slot :name="name" v-bind="slotData"></slot>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface TableHeader {
  key: string
  title: string
  value?: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
  width?: string | number
  [key: string]: any
}

interface TableItem {
  [key: string]: any
}

const props = defineProps({
  headers: {
    type: Array as () => TableHeader[],
    required: true
  },
  items: {
    type: Array as () => TableItem[],
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  noDataText: {
    type: String,
    default: ''
  },
  loadingText: {
    type: String,
    default: ''
  },
  itemsPerPage: {
    type: Number,
    default: 10
  },
  clickAction: {
    type: String,
    default: 'view', // 'view' | 'edit' | 'none'
    validator: (value: string) => ['view', 'edit', 'none'].includes(value)
  }
})

const emit = defineEmits(['row-click', 'edit-item', 'view-details'])

const handleRowClick = (event: Event, { item }: { item: TableItem }) => {
  // Vérifier si le clic vient d'un élément interactif (bouton, lien, etc.)
  const target = event.target as HTMLElement
  const clickedElement = target.closest('.v-btn, a, button, [data-no-row-click]')
  
  if (clickedElement || target.hasAttribute('data-no-row-click')) {
    event.stopPropagation()
    return
  }

  switch (props.clickAction) {
    case 'view':
      emit('view-details', item)
      break
    case 'edit':
      emit('edit-item', item)
      break
    default:
      emit('row-click', item)
  }
}
</script>

<style scoped>
:deep(.v-data-table) {
  cursor: pointer;
}

:deep(.v-data-table-footer) {
  border-top: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Désactiver le curseur pointer si clickAction est 'none' */
:deep(.v-data-table[data-click-action="none"]) {
  cursor: default;
}
</style> 