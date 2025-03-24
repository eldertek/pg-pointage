<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Détails du site</h1>
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
                  <template v-slot:prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Nom</v-list-item-title>
                  <v-list-item-subtitle>{{ site.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-map-marker"></v-icon>
                  </template>
                  <v-list-item-title>Adresse</v-list-item-title>
                  <v-list-item-subtitle>{{ site.address }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-domain"></v-icon>
                  </template>
                  <v-list-item-title>Franchise</v-list-item-title>
                  <v-list-item-subtitle>{{ site.organization }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-nfc"></v-icon>
                  </template>
                  <v-list-item-title>ID NFC</v-list-item-title>
                  <v-list-item-subtitle>{{ site.nfcId }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Paramètres d'alertes</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <v-list-item-title>Marge de retard</v-list-item-title>
                  <v-list-item-subtitle>{{ site.lateMargin }} minutes</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <v-list-item-title>Marge de départ anticipé</v-list-item-title>
                  <v-list-item-subtitle>{{ site.earlyDepartureMargin }} minutes</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <v-list-item-title>Emails pour alertes</v-list-item-title>
                  <v-list-item-subtitle>{{ site.alertEmails }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Plannings ({{ schedules.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle">
            Ajouter un planning
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="schedulesHeaders"
            :items="schedules"
            :items-per-page="5"
            :no-data-text="'Aucun planning trouvé'"
            :loading-text="'Chargement des plannings...'"
            :items-per-page-text="'Lignes par page'"
            :page-text="'{0}-{1} sur {2}'"
            :items-per-page-options="[
              { title: '5', value: 5 },
              { title: '10', value: 10 },
              { title: '15', value: 15 },
              { title: 'Tout', value: -1 }
            ]"
          >
            <template #actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                :to="`/dashboard/schedules/${item.raw.id}`"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés assignés ({{ employees.length }})</span>
          <v-btn color="#00346E" size="small" prepend-icon="mdi-plus-circle">
            Assigner un employé
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
  name: 'SiteDetailView',
  setup() {
    const route = useRoute()
    const siteId = route.params.id
    
    const loading = ref(true)
    const site = ref({})
    
    const schedulesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Heures min. quotidiennes', align: 'center', key: 'minDailyHours' },
      { title: 'Heures min. hebdomadaires', align: 'center', key: 'minWeeklyHours' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const employeesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Planning', align: 'center', key: 'schedule' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const schedules = ref([])
    const employees = ref([])
    
    const fetchSiteData = async () => {
      loading.value = true
      
      try {
        // Simulation de chargement des données
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        site.value = {
          id: siteId,
          name: 'Centre Commercial',
          address: '1 Place du Commerce, Paris',
          organization: 'Planète Gardiens Paris',
          nfcId: 'NFC12345',
          lateMargin: 15,
          earlyDepartureMargin: 15,
          alertEmails: 'manager@planetegardiens.com, alerte@planetegardiens.com'
        }
        
        schedules.value = [
          { id: 1, name: 'Gardiennage jour', type: 'Fixe (gardien)', minDailyHours: '-', minWeeklyHours: '-', status: 'Actif' },
          { id: 2, name: 'Gardiennage nuit', type: 'Fixe (gardien)', minDailyHours: '-', minWeeklyHours: '-', status: 'Actif' },
          { id: 3, name: 'Nettoyage', type: 'Fréquence (nettoyage)', minDailyHours: '6h', minWeeklyHours: '30h', status: 'Actif' }
        ]
        
        employees.value = [
          { id: 1, name: 'Jean Dupont', email: 'jean.dupont@example.com', phone: '06 12 34 56 78', schedule: 'Gardiennage jour' },
          { id: 2, name: 'Marie Martin', email: 'marie.martin@example.com', phone: '06 23 45 67 89', schedule: 'Gardiennage nuit' },
          { id: 3, name: 'Pierre Lambert', email: 'pierre.lambert@example.com', phone: '06 34 56 78 90', schedule: 'Nettoyage' }
        ]
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(fetchSiteData)
    
    return {
      loading,
      site,
      schedulesHeaders,
      employeesHeaders,
      schedules,
      employees
    }
  }
}
</script>

