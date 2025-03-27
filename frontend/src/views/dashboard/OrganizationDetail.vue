<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <Title level="1">{{ organization.name }}</Title>
      <div>
        <v-btn color="#00346E" class="mr-2" prepend-icon="mdi-pencil" @click="editOrganization">
          Modifier
        </v-btn>
        <v-btn color="#F78C48" prepend-icon="mdi-delete" @click="confirmDelete">
          Supprimer
        </v-btn>
      </div>
    </div>
    
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="#00346E" size="64"></v-progress-circular>
      </v-col>
    </v-row>
    
    <template v-else>
      <v-row>
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Informations générales</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Nom</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-map-marker"></v-icon>
                  </template>
                  <v-list-item-title class="d-flex align-center">
                    Adresse
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      :href="formatAddressForMaps(organization.address, organization.postal_code, organization.city, organization.country)"
                      target="_blank"
                      color="primary"
                      class="ml-2"
                    >
                      <v-icon>mdi-map-marker</v-icon>
                      <v-tooltip activator="parent">Ouvrir dans Google Maps</v-tooltip>
                    </v-btn>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ organization.address }}<br>
                    {{ organization.postal_code }} {{ organization.city }}<br>
                    {{ organization.country }}
                  </v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-email"></v-icon>
                  </template>
                  <v-list-item-title>Email</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.email }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-email-outline"></v-icon>
                  </template>
                  <v-list-item-title>Email de contact</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.contact_email }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-phone"></v-icon>
                  </template>
                  <v-list-item-title>Téléphone</v-list-item-title>
                  <v-list-item-subtitle>{{ formatPhoneNumber(organization.phone) }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-card-account-details"></v-icon>
                  </template>
                  <v-list-item-title>SIRET</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.siret }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item v-if="organization.notes">
                  <template #prepend>
                    <v-icon icon="mdi-note-text"></v-icon>
                  </template>
                  <v-list-item-title>Notes</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.notes }}</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon :color="organization.is_active ? 'success' : 'error'">
                      {{ organization.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                    </v-icon>
                  </template>
                  <v-list-item-title>Statut</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ organization.is_active ? 'Active' : 'Inactive' }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Statistiques</v-card-title>
            <v-card-text>
              <div class="d-flex justify-space-around mb-4">
                <div class="text-center">
                  <div class="text-h4">{{ statistics.sites }}</div>
                  <div class="text-subtitle-1">Sites</div>
                </div>
                <div class="text-center">
                  <div class="text-h4">{{ statistics.employees }}</div>
                  <div class="text-subtitle-1">Employés</div>
                </div>
                <div class="text-center">
                  <div class="text-h4">{{ statistics.managers }}</div>
                  <div class="text-subtitle-1">Managers</div>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <v-card v-if="organization.logo" class="mb-4">
            <v-card-title>Logo</v-card-title>
            <v-card-text class="text-center">
              <v-img
                :src="organization.logo"
                :alt="organization.name"
                max-width="200"
                class="mx-auto"
              ></v-img>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Sites ({{ sites.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle" to="/dashboard/sites/new">
            Ajouter un site
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="sitesHeaders"
            :items="sites"
            :items-per-page="5"
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
          >
            <template #[`item.status`]="{ item }">
              <v-chip
                :color="item.is_active ? 'success' : 'error'"
                size="small"
              >
                {{ item.is_active ? 'Actif' : 'Inactif' }}
              </v-chip>
            </template>

            <template #[`item.address`]="{ item }">
              {{ item.address }}, {{ item.postal_code }} {{ item.city }}
              <v-btn
                icon
                variant="text"
                size="x-small"
                :href="formatAddressForMaps(item.address, item.postal_code, item.city, item.country)"
                target="_blank"
                color="primary"
              >
                <v-icon>mdi-map-marker</v-icon>
                <v-tooltip activator="parent">Ouvrir dans Google Maps</v-tooltip>
              </v-btn>
            </template>

            <template #[`item.actions`]="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/sites/${item.id}`"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent">Voir les détails</v-tooltip>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés ({{ employees.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle" to="/dashboard/employees/new">
            Ajouter un employé
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="employeesHeaders"
            :items="employees"
            :items-per-page="5"
            :no-data-text="'Aucun employé trouvé'"
            :loading-text="'Chargement des employés...'"
            :items-per-page-text="'Lignes par page'"
            :page-text="'{0}-{1} sur {2}'"
            :items-per-page-options="[
              { title: '5', value: 5 },
              { title: '10', value: 10 },
              { title: '15', value: 15 },
              { title: 'Tout', value: -1 }
            ]"
          >
            <template #[`item.role`]="{ item }">
              <v-chip
                :color="item.role === 'MANAGER' ? 'primary' : 'success'"
                size="small"
              >
                {{ item.role === 'MANAGER' ? 'Manager' : 'Employé' }}
              </v-chip>
            </template>

            <template #[`item.actions`]="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/admin/users/${item.id}`"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent">Voir les détails</v-tooltip>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- Dialog de confirmation de suppression -->
      <v-dialog v-model="showDeleteDialog" max-width="400">
        <v-card>
          <v-card-title>Confirmer la suppression</v-card-title>
          <v-card-text>
            Êtes-vous sûr de vouloir supprimer l'organisation "{{ organization.name }}" ?
            Cette action est irréversible.
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="grey" variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
            <v-btn 
              color="error" 
              variant="text" 
              @click="deleteOrganization"
              :loading="deleting"
            >
              Supprimer
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </template>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { formatPhoneNumber, formatAddressForMaps } from '@/utils/formatters'
import { Title } from '@/components/typography'

export default {
  name: 'OrganizationDetailView',
  components: {
    Title
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const organizationId = route.params.id
    
    const loading = ref(true)
    const deleting = ref(false)
    const showDeleteDialog = ref(false)
    const organization = ref({})
    const statistics = ref({
      sites: 0,
      employees: 0,
      managers: 0
    })
    
    const sitesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Employés', align: 'center', key: 'employeesCount' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const employeesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'employee_name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Rôle', align: 'center', key: 'role' },
      { title: 'Site', align: 'center', key: 'site_name' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const sites = ref([])
    const employees = ref([])
    
    const fetchOrganizationData = async () => {
      loading.value = true
      
      try {
        // Charger les données de l'organisation
        const orgResponse = await api.get(`/organizations/${organizationId}/`)
        organization.value = orgResponse.data

        // Charger les statistiques
        const statsResponse = await api.get(`/organizations/${organizationId}/statistics/`)
        statistics.value = statsResponse.data

        // Charger les sites
        const sitesResponse = await api.get(`/sites/?organization=${organizationId}`)
        sites.value = sitesResponse.data.results || []

        // Charger les employés
        const employeesResponse = await api.get(`/organizations/${organizationId}/users/`)
        employees.value = employeesResponse.data.results || []

      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }

    const editOrganization = () => {
      router.push(`/dashboard/organizations/${organizationId}/edit`)
    }

    const confirmDelete = () => {
      showDeleteDialog.value = true
    }

    const deleteOrganization = async () => {
      deleting.value = true
      try {
        await api.delete(`/organizations/${organizationId}/`)
        router.push('/dashboard/organizations')
      } catch (error) {
        console.error('Erreur lors de la suppression:', error)
      } finally {
        deleting.value = false
        showDeleteDialog.value = false
      }
    }
    
    onMounted(fetchOrganizationData)
    
    return {
      loading,
      deleting,
      showDeleteDialog,
      organization,
      statistics,
      sitesHeaders,
      employeesHeaders,
      sites,
      employees,
      editOrganization,
      confirmDelete,
      deleteOrganization,
      formatPhoneNumber,
      formatAddressForMaps
    }
  }
}
</script>

<style scoped>
.v-btn--icon.v-btn--density-default {
  color: rgb(0, 52, 110) !important;
}

:deep(.v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-btn--icon .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}

/* Style des icônes dans les informations générales */
:deep(.v-list-item .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}

/* Style des boutons dans les tables */
:deep(.v-data-table .v-btn--icon) {
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}

/* Style des boutons dans la liste d'informations */
:deep(.v-list-item .v-btn--icon) {
  opacity: 1 !important;
}

:deep(.v-list-item .v-btn--icon .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}
</style>

