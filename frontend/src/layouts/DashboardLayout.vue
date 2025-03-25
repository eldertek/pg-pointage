<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-nav-icon 
        @click="$vuetify.display.lgAndUp ? (rail = !rail) : (drawer = !drawer)"
        :icon="rail ? 'mdi-menu' : 'mdi-menu-open'"
      ></v-app-bar-nav-icon>
      <v-app-bar-title>Planète Gardiens - Administration</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="showLogoutDialog = true">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer 
      v-model="drawer" 
      :permanent="$vuetify.display.lgAndUp"
      :temporary="$vuetify.display.mdAndDown"
      :rail="rail"
      :rail-width="56"
      width="256"
      color="primary"
      class="text-white"
      touchless
      @click:outside="handleDrawerOutsideClick"
    >
      <v-list @click="handleListItemClick">
        <!-- Tableau de bord -->
        <v-list-item to="/dashboard" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-view-dashboard</v-icon>
          </template>
          <v-list-item-title>Tableau de bord</v-list-item-title>
        </v-list-item>

        <!-- Section Super Admin -->
        <template v-if="isSuperAdmin">
          <v-divider class="my-2"></v-divider>
          <v-list-subheader>Administration globale</v-list-subheader>
          
          <v-list-item to="/dashboard/admin/users" active-class="primary--text">
            <template v-slot:prepend>
              <v-icon>mdi-account-cog</v-icon>
            </template>
            <v-list-item-title>Gestion des accès</v-list-item-title>
          </v-list-item>
        </template>

        <!-- Section Gestion -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Gestion opérationnelle</v-list-subheader>
        
        <v-list-item to="/dashboard/sites" active-class="primary--text">
          <template v-slot:prepend>
            <v-icon>mdi-domain</v-icon>
          </template>
          <v-list-item-title>Sites & Plannings</v-list-item-title>
        </v-list-item>

        <!-- Section Suivi -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Suivi & rapports</v-list-subheader>
        
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

        <!-- Section Configuration -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Configuration</v-list-subheader>
        
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
import { useDisplay } from 'vuetify'

export default {
  name: 'DashboardLayout',
  setup() {
    const authStore = useAuthStore()
    const display = useDisplay()
    const drawer = ref(true)
    const rail = ref(false)
    const showLogoutDialog = ref(false)
    
    const isSuperAdmin = computed(() => authStore.isSuperAdmin)
    const isManager = computed(() => authStore.isManager)
    
    const logout = () => {
      authStore.logout()
    }

    const handleDrawerOutsideClick = () => {
      if (display.mdAndDown.value) {
        drawer.value = false
      }
    }

    const handleListItemClick = () => {
      if (display.mdAndDown.value) {
        drawer.value = false
      }
    }
    
    return {
      drawer,
      rail,
      showLogoutDialog,
      isSuperAdmin,
      isManager,
      logout,
      handleDrawerOutsideClick,
      handleListItemClick
    }
  }
}
</script>

<style scoped>
.v-navigation-drawer {
  transition: width 0.3s ease;
}

.v-list-item {
  margin: 4px 8px;
  border-radius: 8px;
}

.v-list-item--active {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.v-list-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.v-list-subheader {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.v-divider {
  border-color: rgba(255, 255, 255, 0.1);
  margin: 8px 0;
}

.v-icon {
  color: inherit;
}
</style>

