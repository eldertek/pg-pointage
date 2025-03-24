<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Plannings</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Ajouter un planning
      </v-btn>
    </div>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="schedules"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
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
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'SchedulesView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Site', align: 'start', key: 'site' },
      { title: 'Type', align: 'start', key: 'type' },
      { title: 'Heures min. quotidiennes', align: 'center', key: 'minDailyHours' },
      { title: 'Heures min. hebdomadaires', align: 'center', key: 'minWeeklyHours' },
      { title: 'Employés assignés', align: 'center', key: 'employeesCount' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const schedules = ref([])
    
    // Simulation de chargement des données
    setTimeout(() => {
      schedules.value = [
        { 
          id: 1, 
          name: 'Gardiennage jour', 
          site: 'Centre Commercial',
          type: 'Fixe (gardien)',
          minDailyHours: '-',
          minWeeklyHours: '-',
          employeesCount: 4
        },
        { 
          id: 2, 
          name: 'Gardiennage nuit', 
          site: 'Centre Commercial',
          type: 'Fixe (gardien)',
          minDailyHours: '-',
          minWeeklyHours: '-',
          employeesCount: 3
        },
        { 
          id: 3, 
          name: 'Nettoyage', 
          site: 'Centre Commercial',
          type: 'Fréquence (nettoyage)',
          minDailyHours: '6h',
          minWeeklyHours: '30h',
          employeesCount: 2
        }
      ]
      loading.value = false
    }, 1000)
    
    return {
      loading,
      headers,
      schedules
    }
  }
}
</script>

