<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Sites</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Ajouter un site
      </v-btn>
    </div>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="sites"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
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
  name: 'SitesView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Franchise', align: 'start', key: 'organization' },
      { title: 'Employés', align: 'center', key: 'employeesCount' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const sites = ref([])
    
    // Simulation de chargement des données
    setTimeout(() => {
      sites.value = [
        { 
          id: 1, 
          name: 'Centre Commercial', 
          address: '1 Place du Commerce, Paris', 
          organization: 'Planète Gardiens Paris',
          employeesCount: 8,
          status: 'Actif'
        },
        { 
          id: 2, 
          name: 'Hôpital Nord', 
          address: '2 rue de la Santé, Paris', 
          organization: 'Planète Gardiens Paris',
          employeesCount: 6,
          status: 'Actif'
        },
        { 
          id: 3, 
          name: 'Centre Commercial Confluence', 
          address: '3 rue du Confluent, Lyon', 
          organization: 'Planète Gardiens Lyon',
          employeesCount: 7,
          status: 'Actif'
        },
        { 
          id: 4, 
          name: 'Résidence Les Pins', 
          address: '4 avenue des Pins, Marseille', 
          organization: 'Planète Gardiens Marseille',
          employeesCount: 4,
          status: 'Actif'
        }
      ]
      loading.value = false
    }, 1000)
    
    return {
      loading,
      headers,
      sites
    }
  }
}
</script>

