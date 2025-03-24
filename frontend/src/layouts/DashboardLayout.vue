<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-app-bar-title>Planète Gardiens - Administration</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="showLogoutDialog = true">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" temporary>
      <v-list>
        <v-list-item to="/dashboard" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-view-dashboard</v-icon>
          </template>
          <v-list-item-title>Tableau de bord</v-list-item-title>
        </v-list-item>
        
        <v-list-item v-if="isSuperAdmin" to="/dashboard/organizations" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-domain</v-icon>
          </template>
          <v-list-item-title>Organisations</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/sites" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-map-marker</v-icon>
          </template>
          <v-list-item-title>Sites</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/employees" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-account-group</v-icon>
          </template>
          <v-list-item-title>Employés</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/schedules" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-calendar</v-icon>
          </template>
          <v-list-item-title>Plannings</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/timesheets" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-clock-time-four</v-icon>
          </template>
          <v-list-item-title>Pointages</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/anomalies" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-alert</v-icon>
          </template>
          <v-list-item-title>Anomalies</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/reports" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-file-chart</v-icon>
          </template>
          <v-list-item-title>Rapports</v-list-item-title>
        </v-list-item>
        
        <v-list-item to="/dashboard/settings" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-cog</v-icon>
          </template>
          <v-list-item-title>Paramètres</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>

    <v-dialog v-model="showLogoutDialog" max-width="300">
      <v-card>
        <v-card-title>Déconnexion</v-card-title>
        <v-card-text>Êtes-vous sûr de vouloir vous déconnecter ?</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="showLogoutDialog = false">Annuler</v-btn>
          <v-btn color="error" variant="text" @click="logout">Déconnecter</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'DashboardLayout',
  setup() {
    const authStore = useAuthStore()
    const drawer = ref(false)
    const showLogoutDialog = ref(false)
    
    const isSuperAdmin = computed(() => authStore.isSuperAdmin)
    
    const logout = () => {
      authStore.logout()
    }
    
    return {
      drawer,
      showLogoutDialog,
      isSuperAdmin,
      logout
    }
  }
}
</script>

