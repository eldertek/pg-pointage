<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Détails de l'organisation</h1>
      <div>
        <v-btn color="#00346E" class="mr-2" prepend-icon="mdi-pencil">
          Modifier
        </v-btn>
        <v-btn color="#F78C48" prepend-icon="mdi-delete">
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
                  <v-list-item-title>Adresse</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.address }}</v-list-item-subtitle>
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
                    <v-icon icon="mdi-phone"></v-icon>
                  </template>
                  <v-list-item-title>Téléphone</v-list-item-title>
                  <v-list-item-subtitle>{{ organization.phone }}</v-list-item-subtitle>
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
        </v-col>
      </v-row>
      
      <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Sites ({{ sites.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle">
            Ajouter un site
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="sitesHeaders"
            :items="sites"
            :items-per-page="5"
          >
            <template #actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/sites/${item.raw.id}`"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés ({{ employees.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle">
            Ajouter un employé
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="employeesHeaders"
            :items="employees"
            :items-per-page="5"
          >
            <template #actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/employees/${item.raw.id}`"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'OrganizationDetailView',
  setup() {
    const route = useRoute()
    const organizationId = route.params.id
    
    const loading = ref(true)
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
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Rôle', align: 'center', key: 'role' },
      { title: 'Site', align: 'center', key: 'site' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const sites = ref([])
    const employees = ref([])
    
    const fetchOrganizationData = async () => {
      loading.value = true
      
      try {
        // Simulation de chargement des données
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        organization.value = {
          id: organizationId,
          name: 'Planète Gardiens Paris',
          address: '123 rue de Paris, 75001 Paris',
          email: 'paris@planetegardiens.com',
          phone: '01 23 45 67 89',
          status: 'Actif'
        }
        
        statistics.value = {
          sites: 5,
          employees: 25,
          managers: 3
        }
        
        sites.value = [
          { id: 1, name: 'Centre Commercial', address: '1 Place du Commerce, Paris', employeesCount: 8, status: 'Actif' },
          { id: 2, name: 'Hôpital Nord', address: '2 rue de la Santé, Paris', employeesCount: 6, status: 'Actif' },
          { id: 3, name: 'Résidence Les Pins', address: '3 avenue des Pins, Paris', employeesCount: 4, status: 'Actif' },
          { id: 4, name: 'Banque Centrale', address: '4 boulevard des Finances, Paris', employeesCount: 5, status: 'Actif' },
          { id: 5, name: 'École Primaire', address: '5 rue de l\'Éducation, Paris', employeesCount: 2, status: 'Actif' }
        ]
        
        employees.value = [
          { id: 1, name: 'Jean Dupont', email: 'jean.dupont@example.com', role: 'Manager', site: 'Multiple' },
          { id: 2, name: 'Marie Martin', email: 'marie.martin@example.com', role: 'Manager', site: 'Multiple' },
          { id: 3, name: 'Pierre Lambert', email: 'pierre.lambert@example.com', role: 'Employé', site: 'Centre Commercial' },
          { id: 4, name: 'Sophie Petit', email: 'sophie.petit@example.com', role: 'Employé', site: 'Hôpital Nord' },
          { id: 5, name: 'Luc Bernard', email: 'luc.bernard@example.com', role: 'Employé', site: 'Résidence Les Pins' }
        ]
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(fetchOrganizationData)
    
    return {
      loading,
      organization,
      statistics,
      sitesHeaders,
      employeesHeaders,
      sites,
      employees
    }
  }
}
</script>

