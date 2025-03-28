<template>
  <v-container fluid>
    <!-- En-tête avec titre et actions -->
    <div class="d-flex align-center mb-4">
      <v-btn
        v-if="showBackButton"
        icon="mdi-arrow-left"
        variant="text"
        :to="backRoute"
        class="mr-4"
      ></v-btn>
      <Title :level="1" class="font-weight-bold">{{ title }}</Title>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-pencil"
        @click="editItem"
        class="mr-2"
      >
        Modifier
      </v-btn>
      <v-btn
        v-if="allowDelete"
        color="error"
        prepend-icon="mdi-delete"
        @click="confirmDelete"
        :disabled="deleteButtonDisabled"
      >
        Supprimer
        <v-tooltip activator="parent" v-if="deleteButtonDisabled">
          Vous ne pouvez pas supprimer votre propre compte
        </v-tooltip>
      </v-btn>
    </div>

    <!-- Loader -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-col>
    </v-row>

    <template v-else>
      <v-row>
        <!-- Informations principales -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title>Informations générales</v-card-title>
            <v-card-text>
              <v-list>
                <template v-for="(field, index) in displayFields" :key="index">
                  <v-list-item>
                    <template #prepend>
                      <v-icon>{{ field.icon }}</v-icon>
                    </template>
                    <v-list-item-title>{{ field.label }}</v-list-item-title>
                    <v-list-item-subtitle>
                      <!-- Adresse avec carte -->
                      <template v-if="field.type === 'address' && isAddressField(field)">
                        <AddressWithMap
                          :address="item[field.address]"
                          :postal-code="item[field.postalCode]"
                          :city="item[field.city]"
                          :country="item[field.country]"
                        />
                      </template>
                      
                      <!-- Statut avec puce -->
                      <template v-else-if="field.type === 'status'">
                        <v-chip
                          :color="item[field.key] ? 'success' : 'error'"
                          size="small"
                        >
                          {{ item[field.key] ? field.activeLabel : field.inactiveLabel }}
                        </v-chip>
                      </template>

                      <!-- Rôle avec puce -->
                      <template v-else-if="field.type === 'role'">
                        <v-chip
                          :color="item[field.key] === 'MANAGER' ? 'primary' : 'success'"
                          size="small"
                        >
                          {{ item[field.key] === 'MANAGER' ? 'Manager' : 'Employé' }}
                        </v-chip>
                      </template>

                      <!-- Valeur par défaut -->
                      <template v-else>
                        {{ formatFieldValue(field, item[field.key]) }}
                      </template>
                    </v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Statistiques et informations complémentaires -->
        <v-col cols="12" md="6">
          <!-- Statistiques -->
          <v-card class="mb-4">
            <v-card-title>Statistiques</v-card-title>
            <v-card-text>
              <v-row>
                <template v-for="(stat, index) in statistics" :key="index">
                  <v-col :cols="12 / statistics.length" class="text-center">
                    <div class="text-h4">{{ stat.value }}</div>
                    <div class="text-subtitle-1">{{ stat.label }}</div>
                  </v-col>
                </template>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Logo (pour les organisations) -->
          <v-card v-if="item.logo" class="mb-4">
            <v-card-title>Logo</v-card-title>
            <v-card-text class="text-center">
              <v-img
                :src="item.logo"
                :alt="item.name"
                max-width="200"
                class="mx-auto"
              ></v-img>
            </v-card-text>
          </v-card>

          <!-- QR Code (pour les sites) -->
          <v-card v-if="item.qr_code" class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon icon="mdi-qrcode" class="mr-2"></v-icon>
              QR Code du site
            </v-card-title>
            <v-card-text class="text-center">
              <div class="qr-code-container">
                <v-img
                  :src="item.qr_code"
                  width="400"
                  height="400"
                  class="mx-auto mb-4"
                ></v-img>
                <div class="d-flex gap-2">
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-download"
                    @click="downloadQRCode"
                  >
                    Télécharger
                  </v-btn>
                  <v-btn
                    v-if="type === 'site'"
                    color="error"
                    prepend-icon="mdi-refresh"
                    @click="generateQRCode"
                  >
                    Régénérer
                  </v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tableaux de données associées -->
      <template v-if="relatedTables.length > 0">
        <v-card v-for="table in relatedTables" :key="table.key" class="mt-4">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>{{ table.title }} ({{ table.items.length }})</span>
            <v-btn
              v-if="table.addRoute"
              color="primary"
              size="small"
              prepend-icon="mdi-plus-circle"
              :to="table.addRoute"
            >
              {{ table.addLabel }}
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-data-table
              :headers="table.headers"
              :items="table.items"
              :items-per-page="5"
              :no-data-text="table.noDataText || 'Aucune donnée'"
              @click:row="(item: TableItem) => handleRowClick(table.key, item)"
            >
              <!-- Slot pour les actions -->
              <template v-slot:item.actions="{ item: rowItem }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :to="formatDetailRoute(table.key, rowItem)"
                >
                  <v-icon>mdi-eye</v-icon>
                  <v-tooltip activator="parent">Voir les détails</v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  @click="editRelatedItem(table.key, rowItem)"
                >
                  <v-icon>mdi-pencil</v-icon>
                  <v-tooltip activator="parent">Modifier</v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click="deleteRelatedItem(table.key, rowItem)"
                >
                  <v-icon>mdi-delete</v-icon>
                  <v-tooltip activator="parent">Supprimer</v-tooltip>
                </v-btn>
              </template>

              <!-- Slots pour les colonnes spéciales -->
              <template v-for="slot in table.slots" :key="slot.key" v-slot:[`item.${slot.key}`]="{ item: rowItem }">
                <component :is="slot.component" v-bind="slot.props(rowItem)" />
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </template>

      <!-- Dialog de confirmation de suppression -->
      <v-dialog v-model="showDeleteDialog" max-width="400">
        <v-card>
          <v-card-title>Confirmer la suppression</v-card-title>
          <v-card-text>
            Êtes-vous sûr de vouloir supprimer {{ itemTypeLabel }} "{{ item.name }}" ?
            Cette action est irréversible.
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" variant="text" @click="showDeleteDialog = false">
              Annuler
            </v-btn>
            <v-btn
              color="error"
              variant="text"
              @click="deleteItem"
              :loading="deleting"
            >
              Supprimer
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import { formatPhoneNumber, formatAddressForMaps } from '@/utils/formatters'
import { generateStyledQRCode } from '@/utils/qrcode'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'
import { 
  sitesApi, 
  usersApi, 
  organizationsApi,
  type Site,
  type Organization,
  type Employee,
  type Schedule
} from '@/services/api'

// Types
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'address' | 'status' | 'role' | 'default' | 'date';
  activeLabel?: string;
  inactiveLabel?: string;
  format?: 'phone' | 'date' | 'role' | 'scan_preference';
  dateFormat?: string;
  suffix?: string;
}

interface User {
  id: number;
  role: string;
  first_name: string;
  last_name: string;
  organization?: any;
  [key: string]: any;
}

interface AddressField extends Field {
  type: 'address';
  address: string;
  postalCode: string;
  city: string;
  country: string;
}

interface StatusField extends Field {
  type: 'status';
  activeLabel: string;
  inactiveLabel: string;
}

interface RoleField extends Field {
  type: 'role';
}

type DisplayField = Field | AddressField | StatusField | RoleField;

interface TableHeader {
  title: string;
  key: string;
  align?: 'start' | 'center' | 'end';
  sortable?: boolean;
}

interface TableSlot {
  key: string;
  component: any;
  props: (item: any) => any;
}

interface RelatedTable {
  key: string;
  title: string;
  items: any[];
  headers: TableHeader[];
  addRoute?: string;
  addLabel?: string;
  noDataText?: string;
  slots?: TableSlot[];
}

interface TableItem {
  id: number;
  [key: string]: any;
}

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value: string) => ['user', 'site', 'organization'].includes(value)
  },
  showBackButton: {
    type: Boolean,
    default: true
  },
  allowDelete: {
    type: Boolean,
    default: true
  }
})

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const deleting = ref(false)
const showDeleteDialog = ref(false)
const item = ref<any>({})
const statistics = ref<Array<{ label: string; value: number }>>([])
const relatedTables = ref<RelatedTable[]>([])
const auth = useAuthStore()

// Computed properties
const itemId = computed(() => Number(route.params.id))
const itemTypeLabel = computed(() => {
  switch (props.type) {
    case 'user': return "l'utilisateur"
    case 'site': return 'le site'
    case 'organization': return "l'organisation"
    default: return "l'élément"
  }
})

const title = computed(() => {
  switch (props.type) {
    case 'user': return "Détails de l'utilisateur"
    case 'site': return item.value?.name || 'Détails du site'
    case 'organization': return item.value?.name || "Détails de l'organisation"
    default: return 'Détails'
  }
})

const backRoute = computed(() => {
  switch (props.type) {
    case 'user': return '/dashboard/admin/users'
    case 'site': return '/dashboard/sites'
    case 'organization': return '/dashboard/organizations'
    default: return '/'
  }
})

// Configuration des champs à afficher selon le type
const roleLabels: Record<string, string> = {
  'SUPER_ADMIN': 'Super Administrateur',
  'ADMIN': 'Administrateur',
  'MANAGER': 'Manager',
  'EMPLOYEE': 'Employé'
}

const scanPreferenceLabels: Record<string, string> = {
  'BOTH': 'QR Code et NFC',
  'QR_CODE': 'QR Code uniquement',
  'NFC': 'NFC uniquement'
}

const displayFields = computed((): DisplayField[] => {
  switch (props.type) {
    case 'user':
      const fields: DisplayField[] = [
        { key: 'first_name', label: 'Prénom', icon: 'mdi-account', type: 'default' },
        { key: 'last_name', label: 'Nom', icon: 'mdi-account-box', type: 'default' },
        { key: 'email', label: 'Email', icon: 'mdi-email', type: 'default' },
        { key: 'phone_number', label: 'Téléphone', icon: 'mdi-phone', type: 'default', format: 'phone' },
        { key: 'role', label: 'Rôle', icon: 'mdi-badge-account', type: 'default', format: 'role' }
      ]

      // Ajouter employee_id seulement s'il existe et n'est pas vide
      if (item.value?.employee_id) {
        fields.push({ key: 'employee_id', label: 'ID Employé', icon: 'mdi-card-account-details', type: 'default' })
      }

      return [
        ...fields,
        { key: 'scan_preference', label: 'Préférence de scan', icon: 'mdi-qrcode-scan', type: 'default', format: 'scan_preference' },
        { key: 'simplified_mobile_view', label: 'Vue mobile simplifiée', icon: 'mdi-cellphone',
          type: 'status',
          activeLabel: 'Activée',
          inactiveLabel: 'Désactivée'
        },
        { key: 'date_joined', label: 'Date d\'inscription', icon: 'mdi-calendar', type: 'default', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Actif',
          inactiveLabel: 'Inactif'
        }
      ]
    case 'site':
      return [
        { key: 'name', label: 'Nom', icon: 'mdi-domain' },
        { 
          type: 'address',
          label: 'Adresse',
          icon: 'mdi-map-marker',
          address: 'address',
          postalCode: 'postal_code',
          city: 'city',
          country: 'country',
          key: 'address'
        },
        { key: 'nfc_id', label: 'ID NFC', icon: 'mdi-nfc' },
        { key: 'organization_name', label: 'Organisation', icon: 'mdi-domain' },
        { key: 'manager_name', label: 'Manager', icon: 'mdi-account-tie' },
        { key: 'late_margin', label: 'Marge de retard', icon: 'mdi-clock-alert', suffix: ' minutes' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Actif',
          inactiveLabel: 'Inactif'
        }
      ]
    case 'organization':
      return [
        { key: 'name', label: 'Nom', icon: 'mdi-domain' },
        { key: 'org_id', label: 'ID Organisation', icon: 'mdi-identifier' },
        {
          type: 'address',
          label: 'Adresse',
          icon: 'mdi-map-marker',
          address: 'address',
          postalCode: 'postal_code',
          city: 'city',
          country: 'country',
          key: 'address'
        },
        { key: 'phone', label: 'Téléphone', icon: 'mdi-phone', format: 'phone' },
        { key: 'contact_email', label: 'Email de contact', icon: 'mdi-email-outline' },
        { key: 'siret', label: 'SIRET', icon: 'mdi-card-account-details' },
        { key: 'notes', label: 'Notes', icon: 'mdi-note-text' },
        { key: 'created_at', label: 'Date de création', icon: 'mdi-calendar-plus', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { key: 'updated_at', label: 'Dernière modification', icon: 'mdi-calendar-clock', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Active',
          inactiveLabel: 'Inactive'
        }
      ]
    default:
      return []
  }
})

// Type guard pour vérifier si un champ est de type adresse
const isAddressField = (field: DisplayField): field is AddressField => {
  return field.type === 'address'
}

// Mise à jour des paramètres de getAllSites
interface GetAllSitesParams {
  page?: number;
  perPage?: number;
  organization?: number;
}

// Mise à jour du type des routes
type RouteKey = 'user' | 'site' | 'organization'

// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    switch (props.type) {
      case 'user':
        const userResponse = await usersApi.getUser(itemId.value)
        item.value = userResponse.data
        const userStats = await usersApi.getUserStatistics(itemId.value)
        statistics.value = [
          { label: 'Heures totales', value: userStats.data.total_hours || 0 },
          { label: 'Anomalies', value: userStats.data.anomalies || 0 }
        ]
        break

      case 'site':
        const siteResponse = await sitesApi.getSite(itemId.value)
        item.value = siteResponse.data
        // Charger les employés et les plannings pour les tableaux associés
        const [employeesResponse, schedulesResponse] = await Promise.all([
          sitesApi.getSiteEmployees(itemId.value),
          sitesApi.getSchedulesBySite(itemId.value)
        ])
        relatedTables.value = [
          {
            key: 'employees',
            title: 'Employés',
            items: employeesResponse.data.results,
            headers: [
              { title: 'Nom', key: 'employee_name' },
              { title: 'Email', key: 'email' },
              { title: 'Rôle', key: 'role' },
              { title: 'Actions', key: 'actions' }
            ],
            addRoute: '/dashboard/employees/new',
            addLabel: 'Ajouter un employé'
          },
          {
            key: 'schedules',
            title: 'Plannings',
            items: schedulesResponse.data.results,
            headers: [
              { title: 'Nom', key: 'name' },
              { title: 'Type', key: 'schedule_type' },
              { title: 'Actions', key: 'actions' }
            ],
            addRoute: `/dashboard/sites/${itemId.value}/schedules/new`,
            addLabel: 'Ajouter un planning'
          }
        ]
        break

      case 'organization':
        const orgResponse = await organizationsApi.getOrganization(itemId.value)
        item.value = orgResponse.data
        const orgStats = await organizationsApi.getOrganizationStatistics(itemId.value)
        statistics.value = [
          { label: 'Sites', value: orgStats.data.sites || 0 },
          { label: 'Employés', value: orgStats.data.employees || 0 },
          { label: 'Managers', value: orgStats.data.managers || 0 }
        ]
        // Charger les sites et les employés pour les tableaux associés
        const [sitesResponse, orgEmployeesResponse] = await Promise.all([
          sitesApi.getAllSites(1, 10),
          organizationsApi.getOrganizationUsers(itemId.value)
        ])
        relatedTables.value = [
          {
            key: 'sites',
            title: 'Sites',
            items: sitesResponse.data.results,
            headers: [
              { title: 'Nom', key: 'name' },
              { title: 'Adresse', key: 'address' },
              { title: 'Statut', key: 'status' },
              { title: 'Actions', key: 'actions' }
            ],
            addRoute: '/dashboard/sites/new',
            addLabel: 'Ajouter un site'
          },
          {
            key: 'employees',
            title: 'Employés',
            items: orgEmployeesResponse.data.results,
            headers: [
              { title: 'Nom', key: 'employee_name' },
              { title: 'Email', key: 'email' },
              { title: 'Rôle', key: 'role' },
              { title: 'Site', key: 'site_name' },
              { title: 'Actions', key: 'actions' }
            ],
            addRoute: '/dashboard/employees/new',
            addLabel: 'Ajouter un employé'
          }
        ]
        break
    }
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.format === 'phone') return formatPhoneNumber(value)
  if (field.format === 'date') {
    try {
      const date = new Date(value)
      return format(date, field.dateFormat || 'dd/MM/yyyy', { locale: fr })
    } catch (error) {
      console.error('Erreur lors du formatage de la date:', error)
      return value
    }
  }
  if (field.format === 'role') return roleLabels[value] || value
  if (field.format === 'scan_preference') return scanPreferenceLabels[value] || value
  if (field.suffix) return `${value}${field.suffix}`
  return value
}

const editItem = () => {
  const editRoutes: Record<RouteKey, string> = {
    user: `/dashboard/admin/users/${itemId.value}/edit`,
    site: `/dashboard/sites/${itemId.value}/edit`,
    organization: `/dashboard/organizations/${itemId.value}/edit`
  }
  
  const editRoute = editRoutes[props.type as RouteKey]
  if (editRoute) {
    router.push(editRoute)
  }
}

const confirmDelete = () => {
  showDeleteDialog.value = true
}

const deleteItem = async () => {
  deleting.value = true
  try {
    switch (props.type) {
      case 'user':
        await usersApi.deleteUser(itemId.value)
        router.push('/dashboard/admin/users')
        break
      case 'site':
        await sitesApi.deleteSite(itemId.value)
        router.push('/dashboard/sites')
        break
      case 'organization':
        await organizationsApi.deleteOrganization(itemId.value)
        router.push('/dashboard/organizations')
        break
    }
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
  }
}

const handleRowClick = (tableKey: string, rowItem: TableItem) => {
  const routes: Record<string, string> = {
    employees: `/dashboard/admin/users/${rowItem.id}`,
    sites: `/dashboard/sites/${rowItem.id}`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${rowItem.id}`
  }
  const targetRoute = routes[tableKey]
  if (targetRoute) {
    router.push(targetRoute)
  }
}

const formatDetailRoute = (tableKey: string, rowItem: TableItem): string => {
  const routes: Record<string, string> = {
    employees: `/dashboard/admin/users/${rowItem.id}`,
    sites: `/dashboard/sites/${rowItem.id}`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${rowItem.id}`
  }
  return routes[tableKey] || ''
}

const downloadQRCode = async () => {
  if (!item.value?.qr_code) return
  
  const link = document.createElement('a')
  link.href = item.value.download_qr_code || item.value.qr_code
  link.download = `qr-code-${item.value.name.toLowerCase().replace(/\s+/g, '-')}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const generateQRCode = async () => {
  if (!item.value || props.type !== 'site') return
  
  try {
    const previewQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 500,
      qrSize: 500,
      showFrame: false
    })
    
    const downloadQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 700,
      qrSize: 400,
      showFrame: true,
      radius: 20
    })
    
    item.value.qr_code = previewQRCode
    item.value.download_qr_code = downloadQRCode
  } catch (error) {
    console.error('Erreur lors de la génération du QR code:', error)
  }
}

const editRelatedItem = (tableKey: string, item: any) => {
  const routes = {
    employees: `/dashboard/admin/users/${item.id}/edit`,
    sites: `/dashboard/sites/${item.id}/edit`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${item.id}/edit`
  }
  const editRoute = routes[tableKey as keyof typeof routes]
  if (editRoute) {
    router.push(editRoute)
  }
}

const deleteRelatedItem = async (tableKey: string, item: any) => {
  try {
    switch (tableKey) {
      case 'employees':
        await usersApi.deleteUser(item.id)
        break
      case 'sites':
        await sitesApi.deleteSite(item.id)
        break
      case 'schedules':
        await sitesApi.deleteSchedule(Number(route.params.id), item.id)
        break
    }
    // Recharger les données après la suppression
    await loadData()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

// Computed pour vérifier si c'est le profil de l'utilisateur connecté
const isOwnProfile = computed(() => {
  return props.type === 'user' && (auth.user as User)?.id === itemId.value
})

// Computed pour déterminer si le bouton de suppression doit être désactivé
const deleteButtonDisabled = computed(() => {
  return isOwnProfile.value
})

onMounted(loadData)
</script>

<style scoped>
.white-space-pre-wrap {
  white-space: pre-wrap;
}

.qr-code-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

:deep(.v-img.mx-auto) {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 8px;
  background-color: white;
}

.gap-2 {
  gap: 8px;
}

:deep(.v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-btn--icon .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}

:deep(.v-list-item .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}

:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}
</style> 