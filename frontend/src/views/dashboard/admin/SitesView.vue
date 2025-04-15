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
        v-if="canCreateDelete"
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
      :items="filteredSites"
      :loading="loading"
      :no-data-text="'Aucun site trouvé'"
      :loading-text="'Chargement des sites...'"
      :sort-by="[{ key: 'name' }]"
      :items-per-page="itemsPerPage"
      :items-length="filteredSites.length"
      class="elevation-1"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: 'Tout', value: -1 }
      ]"
      :page-text="'{0}-{1} sur {2}'"
      :items-per-page-text="'Lignes par page'"
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
          :to="`/dashboard/sites/${item.id}`"
          @click.stop
        >
          <v-icon>mdi-eye</v-icon>
          <v-tooltip activator="parent">Voir les détails</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canEdit"
          icon
          variant="text"
          size="small"
          color="primary"
          @click.stop="openDialog(item)"
        >
          <v-icon>mdi-pencil</v-icon>
          <v-tooltip activator="parent">Modifier</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canCreateDelete"
          icon
          variant="text"
          size="small"
          color="warning"
          @click.stop="toggleSiteStatus(item)"
        >
          <v-icon>{{ item.is_active ? 'mdi-domain-off' : 'mdi-domain' }}</v-icon>
          <v-tooltip activator="parent">{{ item.is_active ? 'Désactiver' : 'Activer' }}</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canCreateDelete"
          icon
          variant="text"
          size="small"
          color="error"
          @click.stop="confirmDelete(item)"
        >
          <v-icon>mdi-delete</v-icon>
          <v-tooltip activator="parent">Supprimer</v-tooltip>
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
              :rules="[
                v => !!v || 'Le code postal est requis',
                v => /^\d{5}$/.test(v) || 'Le code postal doit contenir 5 chiffres'
              ]"
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
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { sitesApi, organizationsApi, usersApi } from '@/services/api'
import type { Site, Organization } from '@/services/api'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'
import { useAuthStore } from '@/stores/auth'
import { RoleEnum } from '@/types/api'

const props = defineProps({
  editId: {
    type: [String, Number],
    default: null
  }
})

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
  late_margin: number
  early_departure_margin: number
  ambiguous_margin: number
  is_active: boolean
  alert_emails: string
}

interface ApiError {
  response?: {
    data: Record<string, string[]>
  }
}

// État
const router = useRouter()
const loading = ref(false)
const saving = ref(false)

const defaultSiteValues = {
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
  late_margin: 15,
  early_departure_margin: 15,
  ambiguous_margin: 20,
  is_active: true,
  alert_emails: ''
} as EditedSite

const editedItem = ref<EditedSite>({ ...defaultSiteValues })
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
    // Récupérer tous les sites en une seule fois avec le filtre de recherche
    const params = {
      search: filters.value.search || ''
    }
    console.log('[Sites][LoadSites] Paramètres de recherche:', params)

    const response = await sitesApi.getAllSites(1, 1000, params) // Valeur arbitrairement grande
    sites.value = response.data.results || []
    console.log('[Sites] Nombre de sites chargés:', sites.value.length)
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

const openDialog = async (item?: Site) => {
  try {
    // S'assurer que les organisations sont chargées
    if (organizations.value.length === 0) {
      await loadOrganizations()
    }

    if (item) {
      // Charger d'abord les managers si on a une organisation
      if (item.organization) {
        editedItem.value = {
          ...defaultSiteValues,
          ...item,
          organization: item.organization,
          manager: undefined // On met temporairement le manager à undefined pendant le chargement
        }
        await loadManagers()
      }

      // Une fois les managers chargés, on peut définir la valeur finale
      editedItem.value = {
        ...defaultSiteValues,
        ...item,
        organization: item.organization || undefined,
        manager: item.manager || undefined
      }
    } else {
      editedItem.value = { ...defaultSiteValues }
    }

    // Ouvrir le formulaire uniquement une fois que tout est chargé
    dashboardView.value.showForm = true
  } catch (error) {
    console.error('[Sites][Error] Erreur lors de l\'ouverture du formulaire:', error)
  }
}

const saveSite = async () => {
  if (!form.value?.validate()) {
    console.log('[Sites][Save] Formulaire invalide')
    return
  }

  saving.value = true
  try {
    console.log('[Sites][Save] editedItem avant traitement:', editedItem.value)

    // S'assurer que tous les champs requis sont présents et correctement formatés
    const siteData = {
      name: editedItem.value.name,
      address: editedItem.value.address,
      postal_code: editedItem.value.postal_code,
      city: editedItem.value.city,
      country: editedItem.value.country || 'France',
      organization: editedItem.value.organization,
      manager: editedItem.value.manager || null,
      require_geolocation: editedItem.value.require_geolocation ?? true,
      geolocation_radius: editedItem.value.geolocation_radius ?? 100,
      allow_offline_mode: editedItem.value.allow_offline_mode ?? true,
      max_offline_duration: editedItem.value.max_offline_duration ?? 24,
      late_margin: editedItem.value.late_margin ?? 15,
      early_departure_margin: editedItem.value.early_departure_margin ?? 15,
      ambiguous_margin: editedItem.value.ambiguous_margin ?? 20,
      is_active: editedItem.value.is_active ?? true,
      alert_emails: editedItem.value.alert_emails ?? ''
    }

    console.log('[Sites][Save] Données à envoyer:', siteData)

    if (editedItem.value.id) {
      await sitesApi.updateSite(editedItem.value.id, siteData)
    } else {
      await sitesApi.createSite(siteData)
    }
    await loadSites()
    dashboardView.value.showForm = false
  } catch (error) {
    const apiError = error as ApiError
    console.error('[Sites][Error] Erreur lors de la sauvegarde:', apiError)
    console.error('[Sites][Error] Détails de la réponse:', apiError.response?.data)

    // Afficher les erreurs de validation si présentes
    if (apiError.response?.data) {
      const errors = apiError.response.data
      Object.keys(errors).forEach(field => {
        const messages = errors[field]
        if (Array.isArray(messages)) {
          messages.forEach(message => {
            console.error(`[Sites][Validation] ${field}: ${message}`)
          })
        }
      })
    }
  } finally {
    saving.value = false
  }
}

const { dialogState } = useConfirmDialog()

const confirmDelete = (item: Site) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de suppression'
  state.message = `Êtes-vous sûr de vouloir supprimer le site "${item.name}" ?`
  state.confirmText = 'Supprimer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    await deleteSite(item)
    state.show = false
    state.loading = false
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
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de changement de statut'
  state.message = `Êtes-vous sûr de vouloir ${item.is_active ? 'désactiver' : 'activer'} le site "${item.name}" ?`
  state.confirmText = item.is_active ? 'Désactiver' : 'Activer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'warning'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      console.log('[Sites][ToggleStatus] État actuel:', item.is_active)
      console.log('[Sites][ToggleStatus] Nouvel état:', !item.is_active)

      // N'envoyer que l'ID et le nouveau statut
      await sitesApi.updateSite(item.id, {
        is_active: !item.is_active
      })
      await loadSites()

      console.log('[Sites][ToggleStatus] Mise à jour réussie')
    } catch (error) {
      console.error('[Sites][Error] Erreur lors de la mise à jour du statut:', error)
    } finally {
      state.show = false
      state.loading = false
    }
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

  // Si on a un ID d'édition, charger et ouvrir le formulaire
  if (props.editId) {
    try {
      const response = await sitesApi.getSite(Number(props.editId))
      openDialog(response.data)
    } catch (error) {
      console.error('[Sites][Error] Erreur lors du chargement du site:', error)
    }
  }
})

// Pagination désactivée, pas besoin d'observateurs

watch(() => editedItem.value.organization, async (newOrgId, oldOrgId) => {
  if (newOrgId) {
    // Ne réinitialiser le manager que si l'organisation change
    if (newOrgId !== oldOrgId) {
      editedItem.value.manager = undefined
    }
    await loadManagers()
  } else {
    managers.value = []
  }
})

const authStore = useAuthStore()

// Computed properties pour les permissions
const canCreateDelete = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN
})

const canEdit = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN || role === RoleEnum.MANAGER
})

// Filtrer les sites selon les permissions
const filteredSites = computed(() => {
  const user = authStore.user
  if (!user) return []

  console.log('[Sites][Filter] User:', {
    id: user.id,
    role: user.role,
    organizations: user.organizations
  })

  console.log('[Sites][Filter] Sites avant filtrage:', sites.value)
  console.log('[Sites][Filter] Nombre de sites avant filtrage:', sites.value.length)

  const filtered = sites.value.filter(site => {
    // Super Admin voit tout
    if (user.role === RoleEnum.SUPER_ADMIN) return true

    // Admin et Manager voient les sites de leurs organisations
    if (user.role === RoleEnum.ADMIN || user.role === RoleEnum.MANAGER) {
      // Convertir les IDs en nombres pour la comparaison
      const userOrgIds = user.organizations?.map(org => Number(org)) ?? []
      const siteOrgId = Number(site.organization)

      const hasAccess = userOrgIds.includes(siteOrgId)

      console.log('[Sites][Filter] Vérification accès pour le site:', {
        siteId: site.id,
        siteName: site.name,
        siteOrg: siteOrgId,
        userOrgs: userOrgIds,
        hasAccess
      })
      return hasAccess
    }

    // Employé voit les sites auxquels il est rattaché
    if (user.role === RoleEnum.EMPLOYEE) {
      return user.sites?.some(s => s.id === site.id) ?? false
    }

    return false
  })

  console.log('[Sites][Filter] Sites après filtrage:', filtered)
  console.log('[Sites][Filter] Nombre de sites après filtrage:', filtered.length)
  return filtered
})

const page = ref(1)
const itemsPerPage = ref(10)
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