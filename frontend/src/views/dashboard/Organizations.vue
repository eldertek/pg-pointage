<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Organisations</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Ajouter une organisation
      </v-btn>
    </div>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="organizations"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
      >
        <template #actions="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            :to="`/dashboard/organizations/${item.raw.id}`"
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
  name: 'OrganizationsView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Statut', align: 'start', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const organizations = ref([])
    
    // Simulation de chargement des données
    setTimeout(() => {
      organizations.value = [
        { 
          id: 1, 
          name: 'Planète Gardiens Paris', 
          address: '123 rue de Paris, 75001 Paris', 
          email: 'paris@planetegardiens.com',
          phone: '01 23 45 67 89',
          status: 'Actif'
        },
        { 
          id: 2, 
          name: 'Planète Gardiens Lyon', 
          address: '456 avenue de Lyon, 69001 Lyon', 
          email: 'lyon@planetegardiens.com',
          phone: '04 56 78 90 12',
          status: 'Actif'
        },
        { 
          id: 3, 
          name: 'Planète Gardiens Marseille', 
          address: '789 boulevard de Marseille, 13001 Marseille', 
          email: 'marseille@planetegardiens.com',
          phone: '04 91 23 45 67',
          status: 'Actif'
        }
      ]
      loading.value = false
    }, 1000)
    
    return {
      loading,
      headers,
      organizations
    }
  }
}
</script>

