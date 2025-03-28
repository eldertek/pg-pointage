<template>
  <DashboardView
    ref="dashboardView"
    title="Sites"
    :form-title="editedItem?.id ? 'Modifier le site' : 'Nouveau site'"
    :saving="saving"
    @save="saveSite"
  >
    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="openDialog()"
      >
        Nouveau site
      </v-btn>
    </template>

    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="filters.search"
            label="Rechercher"
            variant="outlined"
            prepend-inner-icon="mdi-magnify"
            clearable
            @update:model-value="loadSites"
          ></v-text-field>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Tableau -->
    <v-data-table
      v-model:page="page"
      :headers="headers"
      :items="sites"
      :loading="loading"
      :items-per-page="itemsPerPage"
      :items-length="totalItems"
      :no-data-text="'Aucun site trouvé'"
      :loading-text="'Chargement des sites...'"
      :items-per-page-text="'Lignes par page'"
      :page-text="'{0}-{1} sur {2}'"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: 'Tout', value: -1 }
      ]"
      class="elevation-1"
      @click:row="handleRowClick"
    >
      <!-- Adresse -->
      <template v-slot:item.address="{ item }">
        <AddressWithMap
          :address="item.address"
          :postal-code="item.postal_code"
          :city="item.city"
          :country="item.country"
        />
      </template>

      <!-- Actions -->
      <template v-slot:item.actions="{ item }">
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          :to="`/dashboard/admin/sites/${item.id}`"
        >
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          @click="openDialog(item)"
        >
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="warning"
          @click="toggleSiteStatus(item)"
        >
          <v-icon>{{ item.is_active ? 'mdi-domain-off' : 'mdi-domain' }}</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="error"
          @click="confirmDelete(item)"
        >
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" @submit="saveSite">
        <v-row>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="editedItem.name"
              label="Nom"
              :rules="[v => !!v || 'Le nom est requis']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-select
              v-model="editedItem.organization"
              :items="organizations"
              label="Organisation"
              item-title="name"
              item-value="id"
              :rules="[v => !!v || 'L\'organisation est requise']"
              required
              @update:model-value="loadManagers"
            ></v-select>
          </v-col>
          <v-col cols="12" sm="6">
            <v-select
              v-model="editedItem.manager"
              :items="managers"
              label="Manager"
              item-title="name"
              item-value="id"
              :rules="[v => !!v || 'Le manager est requis']"
              required
              :disabled="!editedItem.organization"
              :no-data-text="'Aucun manager disponible'"
              :loading-text="'Chargement des managers...'"
            ></v-select>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="editedItem.address"
              label="Adresse"
              :rules="[v => !!v || 'L\'adresse est requise']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="editedItem.postal_code"
              label="Code postal"
              :rules="[v => !!v || 'Le code postal est requis']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="editedItem.city"
              label="Ville"
              :rules="[v => !!v || 'La ville est requise']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="editedItem.country"
              label="Pays"
              :rules="[v => !!v || 'Le pays est requis']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12">
            <v-divider class="mb-3">Paramètres de géolocalisation</v-divider>
            <v-switch
              v-model="editedItem.require_geolocation"
              label="Géolocalisation requise"
              color="primary"
            ></v-switch>
            <v-text-field
              v-if="editedItem.require_geolocation"
              v-model="editedItem.geolocation_radius"
              label="Rayon de géolocalisation (mètres)"
              type="number"
              :rules="[v => !!v || 'Le rayon de géolocalisation est requis']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12">
            <v-divider class="mb-3">Paramètres de synchronisation</v-divider>
            <v-switch
              v-model="editedItem.allow_offline_mode"
              label="Autoriser le mode hors ligne"
              color="primary"
            ></v-switch>
            <v-text-field
              v-if="editedItem.allow_offline_mode"
              v-model="editedItem.max_offline_duration"
              label="Durée maximale hors ligne (heures)"
              type="number"
              :rules="[v => !!v || 'La durée maximale hors ligne est requise']"
              required
            ></v-text-field>
          </v-col>
          <v-col cols="12">
            <v-divider class="mb-3">Statut du site</v-divider>
            <v-switch
              v-model="editedItem.is_active"
              label="Site actif"
              color="success"
            ></v-switch>
          </v-col>
        </v-row>
      </DashboardForm>
    </template>
  </DashboardView>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { sitesApi, organizationsApi, usersApi } from '@/services/api'
import type { Site, Organization } from '@/services/api'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'

interface Manager {
  id: number
  name: string
}

interface ApiUser {
  id: number
  first_name: string
  last_name: string
}

interface EditedSite {
  id?: number
  name: string
  address: string
  postal_code: string
  city: string
  country: string
  organization: number | undefined
  manager: number | undefined
  require_geolocation: boolean
  geolocation_radius: number
  allow_offline_mode: boolean
  max_offline_duration: number
  is_active: boolean
}

// État
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const editedItem = ref<EditedSite>({
  name: '',
  address: '',
  postal_code: '',
  city: '',
  country: 'France',
  organization: undefined,
  manager: undefined,
  require_geolocation: true,
  geolocation_radius: 100,
  allow_offline_mode: true,
  max_offline_duration: 24,
  is_active: true
})
const form = ref()

// Filtres
const filters = ref({
  search: ''
})

// Données
const sites = ref<Site[]>([])
const organizations = ref<Organization[]>([])
const managers = ref<Manager[]>([])

// En-têtes du tableau
const headers = [
  { title: 'Nom', key: 'name' },
  { title: 'Adresse', key: 'address' },
  { title: 'Organisation', key: 'organization_name' },
  { title: 'Manager', key: 'manager_name' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Méthodes
const loadSites = async () => {
  loading.value = true
  try {
    const response = await sitesApi.getAllSites(page.value, itemsPerPage.value)
    sites.value = response.data.results || []
    totalItems.value = response.data.count || 0
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    search: ''
  }
  loadSites()
}

const loadOrganizations = async () => {
  try {
    const response = await organizationsApi.getAllOrganizations()
    organizations.value = response.data.results || []
  } catch (error) {
    console.error('Erreur lors du chargement des organisations:', error)
  }
}

const loadManagers = async () => {
  if (!editedItem.value.organization) {
    console.log('[Sites][LoadManagers] Pas d\'organisation sélectionnée')
    return
  }
  
  console.log('[Sites][LoadManagers] Chargement pour l\'organisation:', editedItem.value.organization)
  
  try {
    const params = {
      role: 'MANAGER',
      organization: editedItem.value.organization,
      is_active: true
    }
    console.log('[Sites][LoadManagers] Paramètres de la requête:', params)
    
    const response = await usersApi.getAllUsers(params)
    console.log('[Sites][API] URL de la requête:', response.config?.url)
    console.log('[Sites][API] Paramètres de la requête:', response.config?.params)
    console.log('[Sites][API] Réponse des managers:', response.data)
    
    if (response.data.count === 0) {
      console.warn('[Sites][Warning] Aucun manager trouvé pour cette organisation. Vérifiez que les managers ont bien une organisation assignée.')
    }
    
    managers.value = response.data.results.map((manager: ApiUser) => ({
      id: manager.id,
      name: `${manager.first_name} ${manager.last_name}`
    }))
    console.log('[Sites][LoadManagers] Managers chargés:', managers.value)
  } catch (error) {
    console.error('[Sites][Error] Erreur lors du chargement des managers:', error)
  }
}

const dashboardView = ref()

const openDialog = (item?: Site) => {
  if (item) {
    editedItem.value = {
      ...item,
      organization: item.organization || undefined,
      manager: item.manager || undefined
    }
  } else {
    editedItem.value = {
      name: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      organization: undefined,
      manager: undefined,
      require_geolocation: true,
      geolocation_radius: 100,
      allow_offline_mode: true,
      max_offline_duration: 24,
      is_active: true
    }
  }
  dashboardView.value.showForm = true
}

const saveSite = async () => {
  if (!form.value?.validate()) return

  saving.value = true
  try {
    if (editedItem.value.id) {
      await sitesApi.updateSite(editedItem.value.id, editedItem.value)
    } else {
      await sitesApi.createSite(editedItem.value)
    }
    await loadSites()
    dashboardView.value.showForm = false
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: Site) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer ce site ?')) {
    deleteSite(item)
  }
}

const deleteSite = async (item: Site) => {
  try {
    await sitesApi.deleteSite(item.id)
    await loadSites()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const toggleSiteStatus = async (item: Site) => {
  try {
    await sitesApi.updateSite(item.id, {
      ...item,
      is_active: !item.is_active,
      organization: item.organization || undefined,
      manager: item.manager || undefined
    })
    await loadSites()
  } catch (error) {
    console.error('Erreur lors de la mise à jour du statut:', error)
  }
}

const handleRowClick = (event: any, { item }: any) => {
  if (item?.id) {
    router.push(`/dashboard/sites/${item.id}`)
  }
}

// Initialisation
onMounted(async () => {
  await Promise.all([
    loadSites(),
    loadOrganizations()
  ])
})

// Observateurs
watch(page, () => {
  loadSites()
})

watch(itemsPerPage, () => {
  loadSites()
})

watch(() => editedItem.value.organization, async (newOrgId) => {
  if (newOrgId) {
    editedItem.value.manager = undefined
    await loadManagers()
  } else {
    managers.value = []
  }
})
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-data-table .v-btn--icon[color="primary"]) {
  background-color: transparent !important;
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  background-color: transparent !important;
  color: #FB8C00 !important;
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