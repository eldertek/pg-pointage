<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Employés</h1>
      <v-btn color="primary" prepend-icon="mdi-plus">
        Ajouter un employé
      </v-btn>
    </div>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="employees"
        :loading="loading"
        :items-per-page="10"
        class="elevation-1"
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
  name: 'EmployeesView',
  setup() {
    const loading = ref(true)
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Rôle', align: 'center', key: 'role' },
      { title: 'Organisation', align: 'start', key: 'organization' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const employees = ref([])
    
    // Simulation de chargement des données
    setTimeout(() => {
      employees.value = [
        { 
          id: 1, 
          name: 'Jean Dupont', 
          email: 'jean.dupont@example.com',
          phone: '06 12 34 56 78',
          role: 'Manager',
          organization: 'Planète Gardiens Paris',
          status: 'Actif'
        },
        { 
          id: 2, 
          name: 'Marie Martin', 
          email: 'marie.martin@example.com',
          phone: '06 23 45 67 89',
          role: 'Manager',
          organization: 'Planète Gardiens Lyon',
          status: 'Actif'
        },
        { 
          id: 3, 
          name: 'Pierre Lambert', 
          email: 'pierre.lambert@example.com',
          phone: '06 34 56 78 90',
          role: 'Employé',
          organization: 'Planète Gardiens Paris',
          status: 'Actif'
        }
      ]
      loading.value = false
    }, 1000)
    
    return {
      loading,
      headers,
      employees
    }
  }
}
</script>

