<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Détails du planning</h1>
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
            <v-card-title>Informations générales</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-calendar"></v-icon>
                  </template>
                  <v-list-item-title>Nom</v-list-item-title>
                  <v-list-item-subtitle>{{ schedule.name }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-map-marker"></v-icon>
                  </template>
                  <v-list-item-title>Site</v-list-item-title>
                  <v-list-item-subtitle>{{ schedule.site }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item>
                  <template v-slot:prepend>
                    <v-icon icon="mdi-format-list-bulleted-type"></v-icon>
                  </template>
                  <v-list-item-title>Type de planning</v-list-item-title>
                  <v-list-item-subtitle>{{ schedule.type }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="schedule.type === 'Fréquence (nettoyage)'">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-clock-time-four"></v-icon>
                  </template>
                  <v-list-item-title>Heures minimales par jour</v-list-item-title>
                  <v-list-item-subtitle>{{ schedule.minDailyHours }}</v-list-item-subtitle>
                </v-list-item>
                
                <v-list-item v-if="schedule.type === 'Fréquence (nettoyage)'">
                  <template v-slot:prepend>
                    <v-icon icon="mdi-calendar-clock"></v-icon>
                  </template>
                  <v-list-item-title>Heures minimales par semaine</v-list-item-title>
                  <v-list-item-subtitle>{{ schedule.minWeeklyHours }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="6">
          <v-card class="mb-4">
            <v-card-title>Statut</v-card-title>
            <v-card-text class="text-center">
              <v-chip
                :color="schedule.isActive ? 'success' : 'error'"
                size="large"
                class="ma-2"
              >
                {{ schedule.isActive ? 'Actif' : 'Inactif' }}
              </v-chip>
              
              <div class="mt-4">
                <p>Créé le: {{ schedule.createdAt }}</p>
                <p>Dernière modification: {{ schedule.updatedAt }}</p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <v-card v-if="schedule.type === 'Fixe (gardien)'" class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Horaires par jour</span>
          <v-btn color="primary" size="small" prepend-icon="mdi-plus-circle">
            Ajouter un horaire
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-simple-table>
            <thead>
              <tr>
                <th>Jour</th>
                <th>Horaire matin</th>
                <th>Horaire après-midi</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(detail, index) in scheduleDetails" :key="index">
                <td>{{ detail.day }}</td>
                <td>{{ detail.morningTime }}</td>
                <td>{{ detail.afternoonTime }}</td>
                <td>
                  <v-btn icon variant="text" size="small" color="primary">
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn icon variant="text" size="small" color="error">
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-simple-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés assignés ({{ employees.length }})</span>
          <v-btn color="primary" size="small" prepend-icon="mdi-plus-circle">
            Assigner un employé
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
  name: 'ScheduleDetailView',
  setup() {
    const route = useRoute()
    const scheduleId = route.params.id
    
    const loading = ref(true)
    const schedule = ref({})
    
    const employeesHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const scheduleDetails = ref([])
    const employees = ref([])
    
    const fetchScheduleData = async () => {
      loading.value = true
      
      try {
        // Simulation de chargement des données
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        schedule.value = {
          id: scheduleId,
          name: 'Gardiennage jour',
          site: 'Centre Commercial',
          type: 'Fixe (gardien)',
          minDailyHours: '-',
          minWeeklyHours: '-',
          isActive: true,
          createdAt: '01/03/2023',
          updatedAt: '15/02/2025'
        }
        
        scheduleDetails.value = [
          { day: 'Lundi', morningTime: '08:00 - 12:00', afternoonTime: '14:00 - 18:00' },
          { day: 'Mardi', morningTime: '08:00 - 12:00', afternoonTime: '14:00 - 18:00' },
          { day: 'Mercredi', morningTime: '08:00 - 12:00', afternoonTime: '14:00 - 18:00' },
          { day: 'Jeudi', morningTime: '08:00 - 12:00', afternoonTime: '14:00 - 18:00' },
          { day: 'Vendredi', morningTime: '08:00 - 12:00', afternoonTime: '14:00 - 18:00' },
          { day: 'Samedi', morningTime: '08:00 - 12:00', afternoonTime: '-' },
          { day: 'Dimanche', morningTime: '-', afternoonTime: '-' }
        ]
        
        employees.value = [
          { id: 1, name: 'Jean Dupont', email: 'jean.dupont@example.com', phone: '06 12 34 56 78' },
          { id: 3, name: 'Pierre Lambert', email: 'pierre.lambert@example.com', phone: '06 34 56 78 90' },
          { id: 5, name: 'Sophie Petit', email: 'sophie.petit@example.com', phone: '06 45 67 89 01' },
          { id: 7, name: 'Luc Bernard', email: 'luc.bernard@example.com', phone: '06 56 78 90 12' }
        ]
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error)
      } finally {
        loading.value = false
      }
    }
    
    onMounted(fetchScheduleData)
    
    return {
      loading,
      schedule,
      employeesHeaders,
      scheduleDetails,
      employees
    }
  }
}
</script>

