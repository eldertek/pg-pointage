<template>
  <v-navigation-drawer
    v-model="drawer"
    :rail="rail"
    permanent
    @mouseenter="rail = false"
    @mouseleave="rail = true"
  >
    <v-list-item
      prepend-avatar="https://randomuser.me/api/portraits/men/78.jpg"
      :title="userName"
      :subtitle="userRole"
    ></v-list-item>

    <v-divider></v-divider>

    <v-list density="compact" nav>
      <v-list-item
        v-for="item in menuItems"
        :key="item.title"
        :prepend-icon="item.icon"
        :title="item.title"
        :to="item.to"
        :value="item.to"
      >
        <template v-if="item.title === 'Anomalies' && pendingAnomaliesCount > 0" #append>
          <v-badge
            :content="pendingAnomaliesCount"
            color="error"
            dot
          ></v-badge>
        </template>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { timesheetsApi } from '@/services/api'

const drawer = ref(true)
const rail = ref(true)
const pendingAnomaliesCount = ref(0)

const authStore = useAuthStore()
const userName = computed(() => `${authStore.user?.first_name} ${authStore.user?.last_name}`)
const userRole = computed(() => authStore.user?.role)

const menuItems = [
  { title: 'Tableau de bord', icon: 'mdi-view-dashboard', to: '/dashboard' },
  { title: 'Sites', icon: 'mdi-domain', to: '/dashboard/sites' },
  { title: 'Employés', icon: 'mdi-account-group', to: '/dashboard/employees' },
  { title: 'Plannings', icon: 'mdi-calendar-clock', to: '/dashboard/schedules' },
  { title: 'Anomalies', icon: 'mdi-alert', to: '/dashboard/anomalies' },
  { title: 'Rapports', icon: 'mdi-file-document', to: '/dashboard/reports' },
]

// Charger le nombre d'anomalies en attente
const loadPendingAnomalies = async () => {
  try {
    const response = await timesheetsApi.getAnomalies({ status: 'PENDING' })
    pendingAnomaliesCount.value = response.data?.count || 0
  } catch (error) {
    console.error('Erreur lors du chargement des anomalies en attente:', error)
  }
}

// Charger les données initiales
loadPendingAnomalies()

// Recharger périodiquement (toutes les 5 minutes)
setInterval(loadPendingAnomalies, 5 * 60 * 1000)
</script>

<style scoped>
.v-badge {
  margin-left: 8px;
}
</style> 