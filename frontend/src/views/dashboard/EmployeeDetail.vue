<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Détails de l'employé</h1>
      <div>
        <v-btn color="primary" class="mr-2" prepend-icon="mdi-pencil">
          Modifier
        </v-btn>
        <v-btn color="error" prepend-icon="mdi-delete">
          Supprimer
        </v-btn>
      </div>
    </div>
    
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      </v-col>
    </v-row>
    
    <template v-else>
      <v-row>
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Informations personnelles</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-account"></v-icon>
                  </template>
                  <v-list-item-title>Nom complet</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-email"></v-icon>
                  </template>
                  <v-list-item-title>Email</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.email }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-phone"></v-icon>
                  </template>
                  <v-list-item-title>Téléphone</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.phone }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-badge-account"></v-icon>
                  </template>
                  <v-list-item-title>ID Employé</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.employeeId }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Informations professionnelles</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-account-tie"></v-icon>
                  </template>
                  <v-list-item-title>Rôle</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.role }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Organisation</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.organization }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-calendar-clock"></v-icon>
                  </template>
                  <v-list-item-title>Date d'embauche</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.hireDate }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template #prepend>
                    <v-icon icon="mdi-check-circle"></v-icon>
                  </template>
                  <v-list-item-title>Statut</v-list-item-title>
                  <v-list-item-subtitle>{{ employee.status }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card class="mb-4">
        <v-card-title>Sites assignés ({{ sites.length }})</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="sitesHeaders"
            :items="sites"
            :items-per-page="5"
          >
            <template #item.actions="{ item }">
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
        <v-card-title>Derniers pointages</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="timesheetsHeaders"
            :items="timesheets"
            :items-per-page="5"
          >
            <template #item.type="{ item }">
              <v-chip
                :color="item.raw.type === 'Arrivée' ? 'success' : 'info'"
                size="small"
              >
                {{ item.raw.type }}
              </v-chip>
            </template>
            <template #item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.raw.status)"
                size="small"
              >
                {{ item.raw.status }}
              </v-chip>
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
  name: 'EmployeeDetailView',
  setup() {
    const route = useRoute()
    const employeeId = route.params.id
    
    const loading = ref(true)
    const employee = ref({})
    
    const sitesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Planning', align: 'center', key: 'schedule' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const timesheetsHeaders = ref([
      { title: 'Date', align: 'start', key: 'date' },
      { title: 'Heure', align: 'start', key: 'time' },
      { title: 'Site', align: 'start', key: 'site' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Statut', align: 'center', key: 'status' }
    ])
    
    const sites = ref([])
    const timesheets = ref([])
    
    const getStatusColor = (status) => {
      if (status === 'Normal') return 'success'
      if (status === 'Retard') return 'warning'
      if (status === 'Départ anticipé') return 'error'
      return 'grey'
    }
    
    const fetchEmployeeData = async () => {
      loading.value = true
      
      try {
        // Simulation de chargement des données
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        employee.value = {
          id: employeeId,
          name: 'Jean Dupont',
          email: 'jean.dupont@example.com'
        }
        
        employee.value = {
          id: employeeId,
          name: 'Jean Dupont',
          email: 'jean.dupont@example.com',
          phone: '06 12 34 56 78',
          employeeId: 'EMP001',
          role: 'Manager',
          organization: 'Planète Gardiens Paris',
          hireDate: '01/03/2022',
          status: 'Actif'
        }
        
        sites.value = [
          { id: 1, name: 'Centre Commercial', address: '1 Place du Commerce, Paris', schedule: 'Gardiennage jour' },
          { id: 2, name: 'Hôpital Nord', address: '2 rue de la Santé, Paris', schedule: 'Gardiennage nuit' }
        ]
        
        timesheets.value = [
          { date: '10/03/2025', time: '08:02', site: 'Centre Commercial', type: 'Arrivée', status: 'Normal' },
          { date: '10/03/2025', time: '16:00', site: 'Centre Commercial', type: 'Départ', status: 'Normal' },
          { date: '11/03/2025', time: '08:17', site: 'Centre Commercial', type: 'Arrivée', status: 'Retard' },
          { date: '11/03/2025', time: '15:45', site: 'Centre Commercial', type: 'Départ', status: 'Départ anticipé' },
          { date: '12/03/2025', time: '08:00', site: 'Centre Commercial', type: 'Arrivée', status: 'Normal' }
        ]
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(fetchEmployeeData)
    
    return {
      loading,
      employee,
      sitesHeaders,
      timesheetsHeaders,
      sites,
      timesheets,
      getStatusColor
    }
  }
}
</script>

