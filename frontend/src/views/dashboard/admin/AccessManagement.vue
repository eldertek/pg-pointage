<template>
  <DashboardView
    ref="dashboardView"
    :title="$t('dashboard.gestion_des_accs')"
    :form-title="(editedItem as OrganizationFormData)?.id ? $t('organizations.editOrganization') : $t('organizations.addOrganization')"
    :saving="saving"
    @save="saveOrganization"
  >
    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="filters.search"
            :label="$t('common.search')"
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
        {{ $t('dashboard.nouvelle_organisation') }}
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
      :no-data-text="$t('dashboard.aucune_organisation_trouve')"
      :loading-text="$t('dashboard.chargement_des_organisations')"
      :items-per-page-text="$t('dashboard.lignes_par_page')"
      :page-text="$t('dashboard.01_sur_2')"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: t('common.all'), value: -1 }
      ]"
      class="elevation-1"
      @click:row="handleRowClick"
    >
      <!-- Adresse -->
      <template #item.address="{ item }">
        <AddressWithMap
          :address="item.address"
          :postal-code="item.postal_code"
          :city="item.city"
          :country="item.country"
        />
      </template>

      <!-- Actions -->
      <template #item.actions="{ item }">
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
            :label="$t('profile.lastName')"
            required
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).phone"
            :label="$t('profile.phone')"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).contact_email"
            :label="$t('organizations.contactEmail')"
            type="email"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).address"
            :label="$t('sites.address')"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).postal_code"
            :label="$t('sites.postalCode')"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).city"
            :label="$t('sites.city')"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-autocomplete
            v-model="(editedItem as OrganizationFormData).country"
            v-model:search-input="searchCountry"
            :items="countries"
            item-title="title"
            item-value="value"
            :label="$t('sites.country')"
            variant="outlined"
            prepend-inner-icon="mdi-earth"
            :filter="customFilter"
            :error-messages="formErrors.country"
            :no-data-text="$t('dashboard.aucun_pays_trouv')"
          ></v-autocomplete>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as OrganizationFormData).siret"
            :label="$t('dashboard.numro_siret')"
            :rules="[
              v => !v || v.length <= 14 || $t('organizations.siretFormat')
            ]"
          ></v-text-field>
        </v-col>
        <v-col cols="12">
          <v-textarea
            v-model="(editedItem as OrganizationFormData).notes"
            :label="$t('organizations.notes')"
            rows="3"
          ></v-textarea>
        </v-col>
        <v-col cols="12" sm="6">
          <v-switch
            v-model="(editedItem as OrganizationFormData).is_active"
            :label="$t('dashboard.organisation_active')"
          ></v-switch>
        </v-col>
      </DashboardForm>
    </template>
  </DashboardView>
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ref, onMounted } from 'vue'
import { organizationsApi } from '@/services/api'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useRouter } from 'vue-router'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'

// Interface pour les données envoyées à l'API
interface OrganizationApiData {
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
  users?: number[];
}

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
  users?: number[];
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
  users?: number[];
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
const users = ref<any[]>([])
const selectedUsers = ref<number[]>([])

// Filtres
const filters = ref({
  search: ''
})

// Données
const organizations = ref<Organization[]>([])

// Import i18n
const { t } = useI18n()

// En-têtes du tableau
const organizationHeaders = [
  { title: t('common.id'), key: 'org_id' },
  { title: t('common.name'), key: 'name' },
  { title: t('common.phone'), key: 'phone' },
  { title: t('common.email'), key: 'contact_email' },
  { title: t('sites.address'), key: 'address', component: AddressWithMap },
  { title: t('sites.city'), key: 'city' },
  { title: t('common.actions'), key: 'actions', sortable: false }
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
const { dialogState } = useConfirmDialog()

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
    console.error('[AccessManagement][LoadOrganizations] Error loading organizations:', error)
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    const response = await organizationsApi.getUnassignedEmployees(editedItem.value?.id || 0)
    const unassignedUsers = response.data.results || []

    // Combiner avec les utilisateurs existants
    const allUsers = [...users.value, ...unassignedUsers]

    // Formater les noms complets
    users.value = allUsers.map(user => ({
      ...user,
      full_name: `${user.last_name} ${user.first_name} (${user.email})`
    }))
  } catch (error) {
    console.error('[AccessManagement][LoadUsers] Error loading users:', error)
  }
}

const loadOrganizationUsers = async (organizationId: number) => {
  try {
    const response = await organizationsApi.getOrganizationUsers(organizationId)
    const organizationUsers = response.data.results || []
    selectedUsers.value = organizationUsers.map((user: any) => user.id)
    if (editedItem.value) {
      editedItem.value.users = selectedUsers.value
    }

    // Ajouter les utilisateurs actuels à la liste des utilisateurs disponibles
    users.value = organizationUsers.map((user: any) => ({
      ...user,
      full_name: `${user.last_name} ${user.first_name} (${user.email})`
    }))
  } catch (error) {
    console.error('[AccessManagement][LoadOrganizationUsers] Error loading organization users:', error)
  }
}

const resetFilters = () => {
  filters.value = {
    search: ''
  }
  loadOrganizations()
}

const openDialog = async (item?: Organization) => {
  // Réinitialiser les utilisateurs
  users.value = []
  selectedUsers.value = []

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
    is_active: item.is_active,
    users: []
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
    is_active: true,
    users: []
  }

  // Charger d'abord les utilisateurs de l'organisation si on est en mode édition
  if (item?.id) {
    await loadOrganizationUsers(item.id)
  }

  // Ensuite charger les utilisateurs non assignés
  await loadUsers()
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
        await organizationsApi.updateOrganization(orgData.id, {
          ...orgData,
          users: orgData.users || []
        } as OrganizationApiData)
      } else {
        await organizationsApi.createOrganization({
          ...orgData,
          users: orgData.users || []
        } as OrganizationApiData)
      }
      await loadOrganizations()
      dashboardView.value.showForm = false
    }
  } catch (error: any) {
    console.error('[AccessManagement][SaveOrganization] Error saving organization:', error)
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
  state.title = t('common.deleteConfirmation')
  state.message = t('organizations.deleteConfirmation')
  state.confirmText = t('common.delete')
  state.cancelText = t('common.cancel')
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
    console.error('[AccessManagement][DeleteOrganization] Error deleting organization:', error)
  }
}

const toggleStatus = async (item: Organization) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = t('common.statusChangeConfirmation')
  state.message = item.is_active ? t('organizations.deactivateConfirmation') : t('organizations.activateConfirmation')
  state.confirmText = item.is_active ? t('common.deactivate') : t('common.activate')
  state.cancelText = t('common.cancel')
  state.confirmColor = 'warning'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      const newStatus = !item.is_active;
      await organizationsApi.toggleOrganizationStatus(item.id, newStatus);
      await loadOrganizations();
    } catch (error) {
      console.error('[AccessManagement][ToggleStatus] Error changing status:', error);
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
      console.error('[AccessManagement][LoadData] Error loading data:', error)
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