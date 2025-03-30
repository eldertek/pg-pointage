<template>
  <DashboardView
    ref="dashboardView"
    title="Gestion des accès"
    :form-title="(editedItem as OrganizationFormData)?.name ? 'Modifier' : 'Nouvelle' + ' organisation'"
    :saving="saving"
    @save="saveOrganization"
  >
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
            @update:model-value="loadOrganizations"
          ></v-text-field>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="openDialog()"
      >
        Nouvelle organisation
      </v-btn>
    </template>

    <!-- Tableau des organisations -->
    <v-data-table
      v-model:page="page"
      :headers="organizationHeaders"
      :items="organizations"
      :loading="loading"
      :items-per-page="itemsPerPage"
      :items-length="totalItems"
      :no-data-text="'Aucune organisation trouvée'"
      :loading-text="'Chargement des organisations...'"
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
          :to="`/dashboard/admin/access/${(item as Organization).id}`"
          @click.stop
        >
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="primary"
          @click.stop="openDialog(item as Organization)"
        >
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="warning"
          @click.stop="toggleStatus(item as Organization)"
        >
          <v-icon>{{ (item as Organization).is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="small"
          color="error"
          @click.stop="confirmDelete(item as Organization)"
        >
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" :errors="formErrors" @submit="saveOrganization">
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).name"
            label="Nom"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).phone"
            label="Téléphone"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).contact_email"
            label="Email de contact"
            type="email"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).address"
            label="Adresse"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).postal_code"
            label="Code postal"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).city"
            label="Ville"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-autocomplete
            v-model="(editedItem as OrganizationFormData).country"
            :items="countries"
            item-title="title"
            item-value="value"
            label="Pays"
            variant="outlined"
            prepend-inner-icon="mdi-earth"
            :search-input.sync="searchCountry"
            :filter="customFilter"
            :error-messages="formErrors.country"
            no-data-text="Aucun pays trouvé"
          ></v-autocomplete>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).siret"
            label="Numéro SIRET"
            :rules="[
              v => !v || v.length <= 14 || 'Le numéro SIRET ne peut pas dépasser 14 caractères'
            ]"
          ></v-text-field>
        </v-col>
        <v-col cols="12">
          <v-textarea
            v-model="(editedItem as OrganizationFormData).notes"
            label="Notes"
            rows="3"
          ></v-textarea>
        </v-col>
        <v-col cols="12" sm="6">
          <v-switch
            v-model="(editedItem as OrganizationFormData).is_active"
            label="Organisation active"
          ></v-switch>
        </v-col>
      </DashboardForm>
    </template>
  </DashboardView>
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { organizationsApi } from '@/services/api'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useRouter } from 'vue-router'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'

// Interface pour les organisations
interface Organization {
  id: number;
  name: string;
  org_id: string;
  address?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  phone?: string;
  contact_email?: string;
  siret?: string;
  logo?: string | null;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// Interface pour le formulaire organisation
interface OrganizationFormData {
  id?: number;
  name: string;
  phone?: string;
  address?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  contact_email?: string;
  siret?: string;
  notes?: string;
  is_active?: boolean;
}

const props = defineProps({
  editId: {
    type: [String, Number],
    default: null
  }
})

// État
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const editedItem = ref<OrganizationFormData | null>(null)
const form = ref()
const dashboardView = ref()
const formErrors = ref<Record<string, string[]>>({})

// Filtres
const filters = ref({
  search: ''
})

// Données
const organizations = ref<Organization[]>([])

// En-têtes du tableau
const organizationHeaders = [
  { title: 'ID', key: 'org_id' },
  { title: 'Nom', key: 'name' },
  { title: 'Téléphone', key: 'phone' },
  { title: 'Email', key: 'contact_email' },
  { title: 'Adresse', key: 'address', component: AddressWithMap },
  { title: 'Ville', key: 'city' },
  { title: 'Actions', key: 'actions', sortable: false }
] as const

// Liste des pays
const countries = [
  { title: 'France', value: 'France' },
  { title: 'Belgique', value: 'Belgique' },
  { title: 'Suisse', value: 'Suisse' },
  { title: 'Canada', value: 'Canada' },
  { title: 'Luxembourg', value: 'Luxembourg' },
  { title: 'Allemagne', value: 'Allemagne' },
  { title: 'Espagne', value: 'Espagne' },
  { title: 'Italie', value: 'Italie' },
  { title: 'Portugal', value: 'Portugal' },
  { title: 'Pays-Bas', value: 'Pays-Bas' },
  { title: 'Royaume-Uni', value: 'Royaume-Uni' },
  { title: 'Irlande', value: 'Irlande' },
  { title: 'Autriche', value: 'Autriche' },
  { title: 'Suède', value: 'Suède' },
  { title: 'Norvège', value: 'Norvège' },
  { title: 'Danemark', value: 'Danemark' },
  { title: 'Finlande', value: 'Finlande' },
  { title: 'Islande', value: 'Islande' },
  { title: 'Grèce', value: 'Grèce' },
  { title: 'Pologne', value: 'Pologne' },
  { title: 'République tchèque', value: 'République tchèque' },
  { title: 'Slovaquie', value: 'Slovaquie' },
  { title: 'Hongrie', value: 'Hongrie' },
  { title: 'Roumanie', value: 'Roumanie' },
  { title: 'Bulgarie', value: 'Bulgarie' },
  { title: 'Croatie', value: 'Croatie' },
  { title: 'Slovénie', value: 'Slovénie' },
  { title: 'Estonie', value: 'Estonie' },
  { title: 'Lettonie', value: 'Lettonie' },
  { title: 'Lituanie', value: 'Lituanie' },
  { title: 'Chypre', value: 'Chypre' },
  { title: 'Malte', value: 'Malte' },
  { title: 'États-Unis', value: 'États-Unis' },
  { title: 'Japon', value: 'Japon' },
  { title: 'Chine', value: 'Chine' },
  { title: 'Inde', value: 'Inde' },
  { title: 'Brésil', value: 'Brésil' },
  { title: 'Russie', value: 'Russie' },
  { title: 'Afrique du Sud', value: 'Afrique du Sud' },
  { title: 'Australie', value: 'Australie' },
  { title: 'Nouvelle-Zélande', value: 'Nouvelle-Zélande' }
]

// Méthodes
const router = useRouter()
const { dialogState, handleConfirm } = useConfirmDialog()

const handleRowClick = (event: any, { item }: any) => {
  if (item?.id) {
    router.push(`/dashboard/admin/access/${item.id}`)
  }
}

const loadOrganizations = async () => {
  loading.value = true
  try {
    const response = await organizationsApi.getAllOrganizations()
    organizations.value = response.data.results || []
    totalItems.value = response.data.count
  } catch (error) {
    console.error('Erreur lors du chargement des organisations:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    search: ''
  }
  loadOrganizations()
}

const openDialog = (item?: Organization) => {
  editedItem.value = item ? {
    id: item.id,
    name: item.name,
    phone: item.phone,
    contact_email: item.contact_email,
    address: item.address,
    postal_code: item.postal_code,
    city: item.city,
    country: item.country,
    siret: item.siret,
    notes: item.notes,
    is_active: item.is_active
  } : {
    name: '',
    phone: '',
    contact_email: '',
    address: '',
    postal_code: '',
    city: '',
    country: '',
    siret: '',
    notes: '',
    is_active: true
  }
  dashboardView.value.showForm = true
}

const saveOrganization = async () => {
  if (!form.value?.validate()) return

  saving.value = true
  formErrors.value = {}
  
  try {
    if (editedItem.value) {
      const orgData = editedItem.value as OrganizationFormData
      if (orgData.id) {
        await organizationsApi.updateOrganization(orgData.id, orgData)
      } else {
        await organizationsApi.createOrganization(orgData)
      }
      await loadOrganizations()
      dashboardView.value.showForm = false
    }
  } catch (error: any) {
    console.error('Erreur lors de la sauvegarde:', error)
    if (error.response?.data) {
      formErrors.value = error.response.data
    }
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: Organization) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de suppression'
  state.message = 'Êtes-vous sûr de vouloir supprimer cette organisation ?'
  state.confirmText = 'Supprimer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    await deleteOrganization(item)
    state.show = false
    state.loading = false
  }
}

const deleteOrganization = async (item: Organization) => {
  try {
    await organizationsApi.deleteOrganization(item.id)
    await loadOrganizations()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const toggleStatus = async (item: Organization) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de changement de statut'
  state.message = `Êtes-vous sûr de vouloir ${item.is_active ? 'désactiver' : 'activer'} cette organisation ?`
  state.confirmText = item.is_active ? 'Désactiver' : 'Activer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'warning'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      const newStatus = !item.is_active;
      await organizationsApi.toggleOrganizationStatus(item.id, newStatus);
      await loadOrganizations();
    } catch (error) {
      console.error('Erreur lors du changement de statut:', error);
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

const searchCountry = ref('')

const customFilter = (item: any, queryText: string) => {
  const text = item.title.toLowerCase()
  const query = queryText.toLowerCase()
  return text.indexOf(query) > -1
}

// Initialisation
onMounted(async () => {
  await loadOrganizations()

  // Si on a un ID d'édition, ouvrir le dialogue
  if (props.editId) {
    try {
      const response = await organizationsApi.getOrganization(Number(props.editId))
      openDialog(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
    }
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

:deep(.v-data-table .v-btn--icon[color="error"]) {
  background-color: transparent !important;
  color: #F78C48 !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  background-color: transparent !important;
  color: #FB8C00 !important;
  opacity: 1 !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}
</style> 