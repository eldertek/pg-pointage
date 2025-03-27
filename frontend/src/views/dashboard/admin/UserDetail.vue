<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <h1 class="text-h4 font-weight-bold">Détails de l'utilisateur</h1>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-pencil"
            @click="editUser"
          >
            Modifier
          </v-btn>
        </div>

        <v-row v-if="loading">
          <v-col cols="12" class="text-center">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
          </v-col>
        </v-row>

        <v-row v-else>
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Informations personnelles</v-card-title>
              <v-card-text>
                <v-list>
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-account</v-icon>
                    </template>
                    <v-list-item-title>Nom complet</v-list-item-title>
                    <v-list-item-subtitle>{{ user.first_name }} {{ user.last_name }}</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-email</v-icon>
                    </template>
                    <v-list-item-title>Email</v-list-item-title>
                    <v-list-item-subtitle>{{ user.email }}</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-badge-account</v-icon>
                    </template>
                    <v-list-item-title>Rôle</v-list-item-title>
                    <v-list-item-subtitle>
                      <v-chip
                        :color="user.role === 'MANAGER' ? 'primary' : 'success'"
                        size="small"
                      >
                        {{ user.role === 'MANAGER' ? 'Manager' : 'Employé' }}
                      </v-chip>
                    </v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item v-if="user.site_name">
                    <template v-slot:prepend>
                      <v-icon>mdi-domain</v-icon>
                    </template>
                    <v-list-item-title>Site</v-list-item-title>
                    <v-list-item-subtitle>{{ user.site_name }}</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon>mdi-domain</v-icon>
                    </template>
                    <v-list-item-title>Organisation</v-list-item-title>
                    <v-list-item-subtitle>{{ user.organization_name }}</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <template v-slot:prepend>
                      <v-icon :color="user.is_active ? 'success' : 'error'">
                        {{ user.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                      </v-icon>
                    </template>
                    <v-list-item-title>Statut</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ user.is_active ? 'Actif' : 'Inactif' }}
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
                <v-row>
                  <v-col cols="6" class="text-center">
                    <div class="text-h4">{{ statistics.total_hours || 0 }}</div>
                    <div class="text-subtitle-1">Heures totales</div>
                  </v-col>
                  <v-col cols="6" class="text-center">
                    <div class="text-h4">{{ statistics.anomalies || 0 }}</div>
                    <div class="text-subtitle-1">Anomalies</div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usersApi } from '@/services/api'

const route = useRoute()
const router = useRouter()
const userId = route.params.id

const loading = ref(true)
const user = ref({})
const statistics = ref({
  total_hours: 0,
  anomalies: 0
})

const fetchUserData = async () => {
  loading.value = true
  try {
    const response = await usersApi.getUser(Number(userId))
    user.value = response.data

    // Charger les statistiques si disponible
    try {
      const statsResponse = await usersApi.getUserStatistics(Number(userId))
      statistics.value = statsResponse.data
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error)
    }
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

const editUser = () => {
  router.push(`/dashboard/admin/users/${userId}/edit`)
}

onMounted(() => {
  fetchUserData()
})
</script>

<style scoped>
.v-list-item .v-icon {
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