<template>
  <DashboardView
    title="Sites"
    :form-title="editedItem.id ? 'Modifier' : 'Nouveau' + ' site'"
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
    >
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
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.name"
            label="Nom"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.address"
            label="Adresse"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.city"
            label="Ville"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.postal_code"
            label="Code postal"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.country"
            label="Pays"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.phone"
            label="Téléphone"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.email"
            label="Email"
            type="email"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="editedItem.website"
            label="Site web"
            required
          ></v-text-field>
        </v-col>
      </DashboardForm>
    </template>
  </DashboardView>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { sitesApi } from '@/services/api'
import type { Site } from '@/services/api'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'

// État
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const editedItem = ref<Site | null>(null)
const form = ref()

// Filtres
const filters = ref({
  search: ''
})

// Données
const sites = ref<Site[]>([])

// En-têtes du tableau
const headers = [
  { title: 'Nom', key: 'name' },
  { title: 'Adresse', key: 'address' },
  { title: 'Ville', key: 'city' },
  { title: 'Code postal', key: 'postal_code' },
  { title: 'Pays', key: 'country' },
  { title: 'Téléphone', key: 'phone' },
  { title: 'Email', key: 'email' },
  { title: 'Site web', key: 'website' },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Méthodes
const loadSites = async () => {
  loading.value = true
  try {
    const response = await sitesApi.getSites({
      page: page.value,
      per_page: itemsPerPage.value,
      search: filters.value.search
    })
    sites.value = response.data
    totalItems.value = response.total
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

const openDialog = (item?: Site) => {
  editedItem.value = item || {
    name: '',
    address: '',
    city: '',
    postal_code: '',
    country: '',
    phone: '',
    email: '',
    website: ''
  }
}

const saveSite = async () => {
  if (!form.value?.validate()) return

  saving.value = true
  try {
    if (editedItem.value?.id) {
      await sitesApi.updateSite(editedItem.value.id, editedItem.value)
    } else {
      await sitesApi.createSite(editedItem.value)
    }
    await loadSites()
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

// Initialisation
onMounted(async () => {
  await loadSites()
})

// Observateurs
watch(page, () => {
  loadSites()
})

watch(itemsPerPage, () => {
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