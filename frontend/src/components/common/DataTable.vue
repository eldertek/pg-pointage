<template>
  <v-data-table
    v-model:page="page"
    :headers="headers"
    :items="items"
    :items-per-page="itemsPerPage"
    :no-data-text="$t('common.noData')"
    :loading-text="$t('common.loading')"
    :items-per-page-text="$t('common.rowsPerPage')"
    :page-text="`{0}-{1} ${$t('common.pageInfo')} {2}`"
    :items-per-page-options="itemsPerPageOptions || defaultItemsPerPageOptions"
    class="elevation-1"
    @click:row="handleRowClick"
  >
    <template #top>
      <v-toolbar flat>
        <v-toolbar-title>{{ title }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <slot name="toolbar-actions"></slot>
      </v-toolbar>
    </template>

    <!-- Slots dynamiques pour les colonnes personnalisées -->
    <template v-for="slot in customSlots" :key="slot.key" #[`item.${slot.key}`]="{ item: rowItem }">
      <component :is="slot.component" v-bind="slot.props(rowItem)" />
    </template>

    <!-- Forward parent-defined cell slots for each header -->
    <template v-for="header in headers" :key="header.key" #[`item.${header.key}`]="{ item: rowItem }">
      <slot :name="'item.' + header.key" :item="rowItem">
        {{ rowItem[header.key] }}
      </slot>
    </template>

    <!-- Slot par défaut pour les actions -->
    <template #item.actions="{ item: rowItem }">
      <slot name="actions" :item="rowItem">
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          :to="formatDetailRoute(rowItem)"
          @click.stop
        >
          <v-icon>mdi-eye</v-icon>
          <v-tooltip activator="parent">{{ $t('common.view') }}</v-tooltip>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          :to="formatEditRoute(rowItem)"
          @click.stop
        >
          <v-icon>mdi-pencil</v-icon>
          <v-tooltip activator="parent">{{ $t('common.edit') }}</v-tooltip>
        </v-btn>
        <template v-if="!isManager">
          <v-btn
            icon
            variant="text"
            size="small"
            color="warning"
            @click.stop="$emit('toggle-status', rowItem)"
          >
            <v-icon>{{ rowItem.is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
            <v-tooltip activator="parent">{{ rowItem.is_active ? $t('users.inactive') : $t('users.active') }}</v-tooltip>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click.stop="$emit('delete', rowItem)"
          >
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent">{{ $t('common.delete') }}</v-tooltip>
          </v-btn>
        </template>
      </slot>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface TableHeader {
  title: string
  key: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
}

interface TableSlot {
  key: string
  component: any
  props: any
}

export interface TableItem {
  id: number;
  is_active?: boolean;
  [key: string]: any;
}

interface ItemsPerPageOption {
  title: string;
  value: number;
}

const props = defineProps<{
  title: string;
  headers: TableHeader[];
  items: TableItem[];
  itemsPerPage?: number;
  itemsPerPageOptions?: ItemsPerPageOption[];
  customSlots?: TableSlot[];
  detailRoute?: string;
  editRoute?: string;
  isManager?: boolean;
}>()

// Valeurs par défaut pour les textes
const defaultItemsPerPageOptions = [
  { title: '5', value: 5 },
  { title: '10', value: 10 },
  { title: '15', value: 15 },
  { title: '20', value: 20 }
]

const emit = defineEmits<{
  'toggle-status': [item: TableItem]
  'delete': [item: TableItem]
  'row-click': [item: TableItem]
}>()

const page = ref(1)

const handleRowClick = (event: Event, rowData: { item: TableItem }) => {
  emit('row-click', rowData.item)
}

const formatDetailRoute = (item: TableItem): string => {
  if (!props.detailRoute) return ''
  return props.detailRoute.replace(':id', item.id.toString())
}

const formatEditRoute = (item: TableItem): string => {
  if (!props.editRoute) return ''
  return props.editRoute.replace(':id', item.id.toString())
}
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-data-table .v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-data-table .v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-data-table .v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  color: #FB8C00 !important;
}

:deep(.v-data-table .v-btn--icon[color="grey"]) {
  color: #999999 !important;
  opacity: 0.5 !important;
  cursor: default !important;
  pointer-events: none !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}

/* Style des puces */
:deep(.v-chip) {
  font-size: 0.875rem !important;
  font-weight: 500 !important;
}

:deep(.v-chip.v-chip--size-small) {
  font-size: 0.75rem !important;
}

/* Style de la barre d'outils */
:deep(.v-toolbar) {
  padding: 0 16px;
}

:deep(.v-toolbar-title) {
  font-size: 1.25rem;
  font-weight: 500;
}
</style>