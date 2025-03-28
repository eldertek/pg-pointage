<template>
  <DashboardView
    title="Gestion des accès"
    :saving="saving"
  >
    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" sm="4">
          <v-select
            v-model="filters.site"
            :items="sites"
            item-title="name"
            item-value="id"
            label="Site"
            variant="outlined"
            prepend-inner-icon="mdi-map-marker"
            clearable
            @update:model-value="applyFilters"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.role"
            :items="roles"
            item-title="title"
            item-value="value"
            label="Rôle"
            variant="outlined"
            prepend-inner-icon="mdi-account-key"
            clearable
            @update:model-value="applyFilters"
          ></v-select>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Tableau des droits d'accès -->
    <v-data-table
      v-model:page="page"
      :headers="headers"
      :items="accessRights"
      :loading="loading"
      :items-per-page="itemsPerPage"
      :items-length="totalItems"
      :no-data-text="'Aucun droit d\'accès trouvé'"
      :loading-text="'Chargement des droits d\'accès...'"
      :items-per-page-text="'Lignes par page'"
      :page-text="'{0}-{1} sur {2}'"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: 'Tout', value: -1 }
      ]"
      class="elevation-1"
    >
      <!-- Utilisateur -->
      <template v-slot:item.user="{ item }">
        {{ item.user_name }}
      </template>

      <!-- Rôle -->
      <template v-slot:item.role="{ item }">
        <v-chip
          :color="getRoleColor(item.role)"
          size="small"
        >
          {{ item.role }}
        </v-chip>
      </template>

      <!-- Sites autorisés -->
      <template v-slot:item.sites="{ item }">
        <v-chip-group>
          <v-chip
            v-for="site in item.sites"
            :key="site.id"
            size="small"
            color="primary"
          >
            {{ site.name }}
          </v-chip>
        </v-chip-group>
      </template>

      <!-- Actions -->
      <template v-slot:item.actions="{ item }">
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          @click="openDialog(item)"
        >
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Dialog pour modification des droits -->
    <v-dialog v-model="dialog" max-width="800px">
      <v-card>
        <v-card-title>
          <span class="text-h5">Modifier les droits d'accès</span>
        </v-card-title>

        <v-card-text>
          <v-container>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="userName"
                  label="Utilisateur"
                  disabled
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="userRole"
                  :items="roles"
                  label="Rôle"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="userSites"
                  :items="sites"
                  item-title="name"
                  item-value="id"
                  label="Sites autorisés"
                  multiple
                  chips
                ></v-select>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="saveAccessRights"
          >
            Enregistrer
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            @click="dialog = false"
          >
            Annuler
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </DashboardView>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { accessManagementApi, sitesApi } from '@/services/api'
import type { User } from '@/types/api'
import { RoleEnum } from '@/types/api'
import type { Site } from '@/services/api'
import { Title } from '@/components/typography'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'

interface AccessRight {
  user_id: number
  user_name: string
  role: RoleEnum
  sites: Site[]
}

// État
const loading = ref(false)
const dialog = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const accessRights = ref<AccessRight[]>([])
const sites = ref<Site[]>([])
const editedItem = ref<AccessRight | null>(null)

// Computed properties for form fields
const userName = computed({
  get: () => editedItem.value?.user_name ?? '',
  set: (value: string) => {
    if (editedItem.value) editedItem.value.user_name = value
  }
})

const userRole = computed({
  get: () => editedItem.value?.role ?? null,
  set: (value: RoleEnum | null) => {
    if (editedItem.value) editedItem.value.role = value as RoleEnum
  }
})

const userSites = computed({
  get: () => editedItem.value?.sites ?? [],
  set: (value: Site[]) => {
    if (editedItem.value) editedItem.value.sites = value
  }
})

const filters = ref({
  site: null as number | null,
  role: null as RoleEnum | null,
})

const roles = [
  { title: 'Super Admin', value: RoleEnum.SUPER_ADMIN },
  { title: 'Manager', value: RoleEnum.MANAGER },
  { title: 'Employé', value: RoleEnum.EMPLOYEE },
]

const headers = [
  { title: 'Utilisateur', key: 'user_name' },
  { title: 'Rôle', key: 'role' },
  { title: 'Sites autorisés', key: 'sites' },
  { title: 'Actions', key: 'actions', sortable: false },
]

// Méthodes
const loadAccessRights = async () => {
  loading.value = true
  try {
    const response = await accessManagementApi.getAllAccessRights(page.value, itemsPerPage.value)
    accessRights.value = response.data.results.map(result => ({
      user_id: result.user_id,
      user_name: result.user_name,
      role: result.role as RoleEnum,
      sites: result.sites,
    }))
    totalItems.value = response.data.count
  } catch (error) {
    console.error('Erreur lors du chargement des droits d\'accès:', error)
  } finally {
    loading.value = false
  }
}

const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    sites.value = response.data.results
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  }
}

const openDialog = (item: AccessRight) => {
  editedItem.value = { ...item }
  dialog.value = true
}

const saveAccessRights = async () => {
  saving.value = true
  try {
    if (!editedItem.value) return
    await accessManagementApi.updateUserAccessRights(editedItem.value.user_id, {
      role: editedItem.value.role,
      sites: editedItem.value.sites.map(site => site.id),
    })
    dialog.value = false
    loadAccessRights()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde des droits d\'accès:', error)
  } finally {
    saving.value = false
  }
}

const getRoleColor = (role: RoleEnum): string => {
  switch (role) {
    case RoleEnum.SUPER_ADMIN:
      return 'error'
    case RoleEnum.MANAGER:
      return 'warning'
    case RoleEnum.EMPLOYEE:
      return 'success'
    default:
      return 'grey'
  }
}

const applyFilters = () => {
  loadAccessRights()
}

const resetFilters = () => {
  filters.value.site = null
  filters.value.role = null
  loadAccessRights()
}

// Lifecycle hooks
onMounted(() => {
  loadAccessRights()
  loadSites()
})
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-data-table .v-btn--icon[color="primary"]) {
  background-color: transparent !important;
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="error"]) {
  background-color: transparent !important;
  color: #F78C48 !important;
  opacity: 1 !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}
</style> 