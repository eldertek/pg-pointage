<template>
  <DashboardView
    ref="dashboardView"
    title="Utilisateurs"
    :form-title="view === 'users' ? (editedItem as UserFormData)?.username ? 'Modifier utilisateur' : 'Nouvel utilisateur' : (editedItem as OrganizationFormData)?.name ? 'Modifier' : 'Nouvelle' + ' organisation'"
    :saving="saving"
    @save="saveUser"
  >
    <!-- Sous-titre -->
    <template #subtitle>
      <v-btn-toggle
        v-if="isSuperAdmin"
        v-model="view"
        mandatory
        class="mb-4"
      >
        <v-btn value="users">Utilisateurs</v-btn>
        <v-btn value="organizations">Organisations</v-btn>
      </v-btn-toggle>
    </template>

    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="openDialog()"
      >
        {{ view === 'users' ? 'Nouvel utilisateur' : 'Nouvelle organisation' }}
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
            @update:model-value="loadUsers"
          ></v-text-field>
        </v-col>
        <v-col v-if="view === 'users'" cols="12" md="4">
          <v-select
            v-model="filters.role"
            :items="roles"
            item-title="label"
            item-value="value"
            label="Rôle"
            variant="outlined"
            prepend-inner-icon="mdi-account-key"
            clearable
            @update:model-value="loadUsers"
          ></v-select>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Tableau des utilisateurs -->
    <template v-if="view === 'users'">
      <v-data-table
        v-model:page="page"
        :headers="headers"
        :items="users"
        :loading="loading"
        :items-per-page="itemsPerPage"
        :items-length="totalItems"
        :no-data-text="'Aucun utilisateur trouvé'"
        :loading-text="'Chargement des utilisateurs...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        :sort-by="[{ key: 'last_name' }, { key: 'first_name' }, { key: 'role' }]"
        class="elevation-1"
        @click:row="handleRowClick"
      >
        <!-- Rôle -->
        <template v-slot:item.role="{ item }">
          <v-chip
            :color="getRoleColor(item.role)"
            size="small"
          >
            {{ getRoleLabel(item.role) }}
          </v-chip>
        </template>

        <!-- Sites -->
        <template v-slot:item.sites="{ item }">
          <v-chip
            v-for="site in item.sites"
            :key="site.id"
            color="primary"
            size="small"
            class="mr-1"
          >
            {{ site.name }}
          </v-chip>
        </template>

        <!-- Actions -->
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            :to="`/dashboard/admin/users/${item.id}`"
            @click.stop
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click.stop="openDialog(item)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click.stop="confirmDelete(item)"
            :disabled="(item as ExtendedUser).id === (authStore.user as any)?.id"
            :class="{ 'disabled-button': (item as ExtendedUser).id === (authStore.user as any)?.id }"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>

    <!-- Tableau des organisations -->
    <template v-else>
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
            :to="`/dashboard/organizations/${item.id}`"
            @click.stop
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click.stop="openDialog(item)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click.stop="confirmDelete(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </template>

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" :errors="formErrors" @submit="saveUser">
        <!-- Formulaire utilisateur -->
        <template v-if="view === 'users' && editedItem">
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="(editedItem as UserFormData).last_name"
              label="Nom"
              required
              :error-messages="formErrors.last_name"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="(editedItem as UserFormData).first_name"
              label="Prénom"
              required
              :error-messages="formErrors.first_name"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="(editedItem as UserFormData).phone_number"
              label="Téléphone"
              required
              :error-messages="formErrors.phone_number"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="(editedItem as UserFormData).email"
              label="Email"
              type="email"
              required
              :error-messages="formErrors.email"
              @update:model-value="handleEmailChange"
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="6">
            <v-select
              v-model="(editedItem as UserFormData).role"
              :items="roles"
              item-title="label"
              item-value="value"
              label="Rôle"
              required
              :error-messages="formErrors.role"
            ></v-select>
          </v-col>
          <v-col v-if="(editedItem as UserFormData).role !== RoleEnum.SUPER_ADMIN" cols="12" sm="6">
            <v-select
              v-model="(editedItem as UserFormData).sites"
              :items="sites"
              item-title="name"
              item-value="id"
              label="Sites"
              multiple
              chips
              required
              :error-messages="formErrors.sites"
              no-data-text="Aucun site disponible"
            ></v-select>
          </v-col>
          <!-- Champ mot de passe uniquement à la création -->
          <v-col v-if="view === 'users' && !(editedItem as UserFormData).id" cols="12" sm="6">
            <v-text-field
              v-model="(editedItem as UserFormData).password"
              label="Mot de passe"
              type="password"
              required
              :error-messages="formErrors.password"
              :rules="[
                v => !!v || 'Le mot de passe est obligatoire',
                v => (v && v.length >= 8) || 'Le mot de passe doit contenir au moins 8 caractères'
              ]"
            ></v-text-field>
          </v-col>
          <v-col v-if="(editedItem as UserFormData).role === RoleEnum.EMPLOYEE" cols="12" sm="6">
            <v-select
              v-model="(editedItem as UserFormData).scan_preference"
              :items="[
                { title: 'NFC et QR Code', value: ScanPreferenceEnum.BOTH },
                { title: 'QR Code uniquement', value: ScanPreferenceEnum.QR_ONLY },
                { title: 'NFC uniquement', value: ScanPreferenceEnum.NFC_ONLY }
              ]"
              label="Préférence de scan"
              required
              :error-messages="formErrors.scan_preference"
            ></v-select>
          </v-col>
          <v-col v-if="(editedItem as UserFormData).role === RoleEnum.EMPLOYEE" cols="12" sm="6">
            <v-switch
              v-model="(editedItem as UserFormData).simplified_mobile_view"
              label="Vue mobile simplifiée"
              :error-messages="formErrors.simplified_mobile_view"
            ></v-switch>
          </v-col>
        </template>

        <!-- Formulaire organisation -->
        <template v-else-if="view === 'organizations' && editedItem">
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
        </template>
      </DashboardForm>
    </template>
  </DashboardView>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { usersApi, sitesApi, organizationsApi } from '@/services/api'
import type { User, UserRequest } from '@/types/api'
import type { Site } from '@/services/api'
import { RoleEnum, ScanPreferenceEnum } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import { useRouter, useRoute } from 'vue-router'

// Interface étendue pour les utilisateurs avec les propriétés supplémentaires
interface ExtendedUser extends User {
  sites?: Site[];
}

// Interface étendue pour les organisations
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
  is_active?: boolean;
}

// Interface pour le formulaire utilisateur
interface UserFormData extends UserRequest {
  id?: number;
  phone_number?: string;
  sites?: number[];
  password?: string;
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

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.user?.role === RoleEnum.SUPER_ADMIN)

const props = defineProps({
  editId: {
    type: [String, Number],
    default: null
  },
  defaultView: {
    type: String,
    default: 'users'
  }
})

// État
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const view = ref(props.defaultView)
const editedItem = ref<UserFormData | OrganizationFormData | null>(null)
const form = ref()
const dashboardView = ref()
const formErrors = ref<Record<string, string[]>>({})

// Filtres
const filters = ref({
  search: '',
  role: ''
})

// Données
const users = ref<ExtendedUser[]>([])
const organizations = ref<Organization[]>([])
const sites = ref<Site[]>([])

// En-têtes des tableaux
const headers = [
  { title: 'ID', key: 'id' },
  { title: 'Nom', key: 'last_name' },
  { title: 'Prénom', key: 'first_name' },
  { title: 'Téléphone', key: 'phone_number' },
  { title: 'Email', key: 'email' },
  { title: 'Rôle', key: 'role' },
  { title: 'Sites', key: 'sites' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const organizationHeaders = [
  { title: 'ID', key: 'org_id' },
  { title: 'Nom', key: 'name' },
  { title: 'Téléphone', key: 'phone' },
  { title: 'Email', key: 'contact_email' },
  { title: 'Adresse', key: 'address', component: AddressWithMap },
  { title: 'Ville', key: 'city' },
  { title: 'Actions', key: 'actions', sortable: false }
] as const

// Rôles disponibles
const roles = [
  { label: 'Administrateur', value: RoleEnum.SUPER_ADMIN },
  { label: 'Manager', value: RoleEnum.MANAGER },
  { label: 'Employé', value: RoleEnum.EMPLOYEE }
]

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
const route = useRoute()

const handleRowClick = (event: any, { item }: any) => {
  if (view.value === 'users') {
    if (item?.id) {
      router.push(`/dashboard/admin/users/${item.id}`)
    }
  } else {
    if (item?.id) {
      router.push(`/dashboard/organizations/${item.id}`)
    }
  }
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await usersApi.getAllUsers({
      page: page.value,
      page_size: itemsPerPage.value,
      search: filters.value.search,
      role: filters.value.role
    })
    users.value = response.data.results || []
    totalItems.value = response.data.count
  } catch (error) {
    console.error('Erreur lors du chargement des utilisateurs:', error)
  } finally {
    loading.value = false
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

const loadSites = async () => {
  try {
    const response = await sitesApi.getAllSites()
    sites.value = response.data.results || []
  } catch (error) {
    console.error('Erreur lors du chargement des sites:', error)
  }
}

const resetFilters = () => {
  filters.value = {
    search: '',
    role: ''
  }
  loadUsers()
}

const openDialog = (item?: ExtendedUser | Organization) => {
  if (view.value === 'users') {
    editedItem.value = item ? {
      id: (item as ExtendedUser).id,
      username: (item as ExtendedUser).username,
      email: (item as ExtendedUser).email,
      first_name: (item as ExtendedUser).first_name,
      last_name: (item as ExtendedUser).last_name,
      role: (item as ExtendedUser).role,
      organization: (item as ExtendedUser).organization,
      phone_number: (item as ExtendedUser).phone_number,
      is_active: (item as ExtendedUser).is_active,
      scan_preference: (item as ExtendedUser).scan_preference,
      simplified_mobile_view: (item as ExtendedUser).simplified_mobile_view,
      sites: (item as ExtendedUser).role === RoleEnum.SUPER_ADMIN ? undefined : (item as ExtendedUser).sites?.map(site => site.id)
    } : {
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: RoleEnum.EMPLOYEE,
      organization: null,
      is_active: true,
      scan_preference: 'BOTH',
      simplified_mobile_view: false,
      password: ''
    }
  } else {
    editedItem.value = item ? {
      id: (item as Organization).id,
      name: (item as Organization).name,
      phone: (item as Organization).phone,
      contact_email: (item as Organization).contact_email,
      address: (item as Organization).address,
      postal_code: (item as Organization).postal_code,
      city: (item as Organization).city,
      country: (item as Organization).country,
      siret: (item as Organization).siret,
      notes: (item as Organization).notes,
      is_active: (item as Organization).is_active
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
  }
  dashboardView.value.showForm = true
}

const generateUsername = (email: string): string => {
  // Prend la partie avant @ de l'email
  let baseUsername = email.split('@')[0]
  
  // Supprime les caractères spéciaux et les espaces
  baseUsername = baseUsername.replace(/[^a-zA-Z0-9]/g, '')
  
  // Ajoute un timestamp pour garantir l'unicité
  const timestamp = new Date().getTime().toString().slice(-4)
  return `${baseUsername}${timestamp}`
}

const handleEmailChange = (email: string) => {
  if (!editedItem.value || view.value !== 'users') return
  const userFormData = editedItem.value as UserFormData
  if (!userFormData.id) {
    userFormData.username = generateUsername(email)
  }
}

const saveUser = async () => {
  if (!form.value?.validate()) return

  saving.value = true
  formErrors.value = {}
  
  try {
    if (view.value === 'users' && editedItem.value) {
      const userData = editedItem.value as UserFormData
      if (userData.id) {
        await usersApi.updateUser(userData.id, userData)
      } else {
        // Génère le nom d'utilisateur final avant la création
        userData.username = generateUsername(userData.email)
        await usersApi.createUser(userData)
      }
    } else if (view.value === 'organizations' && editedItem.value) {
      const orgData = editedItem.value as OrganizationFormData
      if (orgData.id) {
        await organizationsApi.updateOrganization(orgData.id, orgData)
      } else {
        await organizationsApi.createOrganization(orgData)
      }
      await loadOrganizations()
    }
    await loadUsers()
    dashboardView.value.showForm = false
  } catch (error: any) {
    console.error('Erreur lors de la sauvegarde:', error)
    if (error.response?.data) {
      const processedErrors: Record<string, string[]> = {}
      Object.entries(error.response.data).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          processedErrors[field] = messages.map(message => {
            switch (message) {
              case "Ce champ ne peut être vide.":
              case "Ce champ est obligatoire.":
                return "Ce champ est obligatoire."
              case "Un utilisateur avec ce nom d'utilisateur existe déjà.":
                return "Ce nom d'utilisateur est déjà utilisé. Veuillez réessayer."
              default:
                return message
            }
          })
        } else {
          processedErrors[field] = [messages as string]
        }
      })
      formErrors.value = processedErrors
    }
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: ExtendedUser | Organization) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
    deleteUser(item)
  }
}

const deleteUser = async (item: ExtendedUser | Organization) => {
  try {
    if (view.value === 'users') {
      await usersApi.deleteUser((item as ExtendedUser).id)
    } else {
      await organizationsApi.deleteOrganization((item as Organization).id)
    }
    if (view.value === 'users') {
      await loadUsers()
    } else {
      await loadOrganizations()
    }
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const getRoleColor = (role: RoleEnum | undefined) => {
  if (!role) return 'grey'
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

const getRoleLabel = (role: RoleEnum | undefined) => {
  if (!role) return ''
  const found = roles.find(r => r.value === role)
  return found ? found.label : role
}

// Initialisation
onMounted(async () => {
  // Initialiser la vue
  view.value = props.defaultView

  // Charger les données initiales
  await Promise.all([
    loadUsers(),
    loadSites()
  ])

  // Si on a un ID d'édition, ouvrir le dialogue
  if (props.editId) {
    try {
      let response
      if (view.value === 'organizations') {
        response = await organizationsApi.getOrganization(Number(props.editId))
      } else {
        response = await usersApi.getUser(Number(props.editId))
      }
      openDialog(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error)
    }
  }
})

// Observateurs
watch(view, (newValue) => {
  if (newValue === 'users') {
    loadUsers()
  } else {
    loadOrganizations()
  }
})

watch(page, () => {
  if (view.value === 'users') {
    loadUsers()
  } else {
    loadOrganizations()
  }
})

watch(itemsPerPage, () => {
  if (view.value === 'users') {
    loadUsers()
  } else {
    loadOrganizations()
  }
})

const searchCountry = ref('')

const customFilter = (item: any, queryText: string) => {
  const text = item.title.toLowerCase()
  const query = queryText.toLowerCase()
  return text.indexOf(query) > -1
}

watch(() => route.query.view, (newView) => {
  if (newView === 'organizations') {
    view.value = 'organizations'
  }
}, { immediate: true })
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

/* Style pour le bouton désactivé */
:deep(.disabled-button) {
  opacity: 0.5 !important;
  color: #999 !important;
  cursor: not-allowed !important;
}

:deep(.disabled-button .v-icon) {
  color: #999 !important;
}
</style> 