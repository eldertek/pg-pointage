<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-nav-icon 
        :icon="rail ? 'mdi-menu' : 'mdi-menu-open'"
        @click="$vuetify.display.lgAndUp ? (rail = !rail) : (drawer = !drawer)"
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
        <v-tooltip location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-view-dashboard</v-icon>
              </template>
              <v-list-item-title>Tableau de bord</v-list-item-title>
            </v-list-item>
          </template>
          <span>Tableau de bord</span>
        </v-tooltip>

        <!-- Utilisateurs - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item 
              to="/dashboard/admin/users" 
              :active="$route.meta.section === 'users' || $route.path === '/dashboard/admin/users'" 
              active-class="primary--text" 
              v-bind="props"
            >
              <template #prepend>
                <v-icon>mdi-account-group</v-icon>
              </template>
              <v-list-item-title>Utilisateurs</v-list-item-title>
            </v-list-item>
          </template>
          <span>Utilisateurs</span>
        </v-tooltip>

        <!-- Sites - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item 
              to="/dashboard/sites" 
              :active="$route.meta.section === 'sites' || $route.path === '/dashboard/sites'"
              active-class="primary--text" 
              v-bind="props"
            >
              <template #prepend>
                <v-icon>mdi-domain</v-icon>
              </template>
              <v-list-item-title>Sites</v-list-item-title>
            </v-list-item>
          </template>
          <span>Sites</span>
        </v-tooltip>

        <!-- Plannings - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard/plannings" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-calendar</v-icon>
              </template>
              <v-list-item-title>Plannings</v-list-item-title>
            </v-list-item>
          </template>
          <span>Plannings</span>
        </v-tooltip>

        <!-- Pointages - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard/timesheets" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-clock-time-four</v-icon>
              </template>
              <v-list-item-title>Pointages</v-list-item-title>
            </v-list-item>
          </template>
          <span>Pointages</span>
        </v-tooltip>

        <!-- Anomalies - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard/anomalies" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-alert</v-icon>
              </template>
              <v-list-item-title>Anomalies</v-list-item-title>
            </v-list-item>
          </template>
          <span>Anomalies</span>
        </v-tooltip>

        <!-- Rapports - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard/reports" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-file-chart</v-icon>
              </template>
              <v-list-item-title>Rapports</v-list-item-title>
            </v-list-item>
          </template>
          <span>Rapports</span>
        </v-tooltip>

        <!-- Gestion des accès - Super Admin uniquement -->
        <v-tooltip v-if="isSuperAdmin" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item 
              to="/dashboard/admin/access" 
              :active="$route.path.includes('/dashboard/admin/access')"
              active-class="primary--text" 
              v-bind="props"
            >
              <template #prepend>
                <v-icon>mdi-domain</v-icon>
              </template>
              <v-list-item-title>Gestion des accès</v-list-item-title>
            </v-list-item>
          </template>
          <span>Gestion des accès</span>
        </v-tooltip>

        <!-- Paramètres - Super Admin, Admin et Manager -->
        <v-tooltip v-if="isSuperAdmin || isAdmin || isManager" location="right" :disabled="!rail">
          <template #activator="{ props }">
            <v-list-item to="/dashboard/settings" active-class="primary--text" v-bind="props">
              <template #prepend>
                <v-icon>mdi-cog</v-icon>
              </template>
              <v-list-item-title>Paramètres</v-list-item-title>
            </v-list-item>
          </template>
          <span>Paramètres</span>
        </v-tooltip>
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
    const isSuperAdminMode = ref(false)
    
    const isSuperAdmin = computed(() => isSuperAdminMode.value || authStore.isSuperAdmin)
    const isAdmin = computed(() => authStore.isAdmin)
    const isManager = computed(() => authStore.isManager)
    const isEmployee = computed(() => authStore.isEmployee)
    
    const toggleSuperAdmin = () => {
      isSuperAdminMode.value = !isSuperAdminMode.value
      console.log('[Auth][Debug] Mode Super Admin:', isSuperAdminMode.value ? 'Activé' : 'Désactivé')
    }
    
    const logout = () => {
      isSuperAdminMode.value = false
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
      isAdmin,
      isManager,
      isEmployee,
      isSuperAdminMode,
      toggleSuperAdmin,
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
  background-color: rgb(0, 32, 96) !important;
}

:deep(.v-list) {
  background-color: transparent !important;
}

:deep(.v-list-item) {
  margin: 4px 8px;
  border-radius: 8px;
  min-height: 44px !important;
  padding: 0 12px;
}

:deep(.v-list-item--active) {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: white !important;
}

/* Style spécifique pour le tableau de bord */
:deep(.v-list-item[href="/dashboard"].v-list-item--active) {
  background-color: rgba(247, 140, 72, 0.2) !important;
  border-left: 3px solid rgb(247, 140, 72) !important;
}

:deep(.v-list-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

:deep(.v-list-subheader) {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background-color: transparent !important;
  padding: 0 20px;
  min-height: 36px;
}

:deep(.v-divider) {
  border-color: rgba(255, 255, 255, 0.1);
  margin: 8px 16px;
}

:deep(.v-icon) {
  color: white !important;
}

/* Mode rail */
:deep(.v-navigation-drawer--rail) {
  .v-list {
    padding: 8px 0;
  }

  .v-list-item {
    margin: 4px auto;
    padding: 0;
    width: 40px;
    height: 40px;
    min-height: 40px !important;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
  }

  .v-list-item--active {
    background-color: rgba(255, 255, 255, 0.15) !important;
  }

  /* Style spécifique pour le tableau de bord en mode rail */
  .v-list-item[href="/dashboard"].v-list-item--active {
    background-color: rgba(247, 140, 72, 0.2) !important;
    border: 2px solid rgb(247, 140, 72) !important;
  }

  .v-list-item__prepend {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    justify-content: center !important;
  }

  .v-list-item__content,
  .v-list-item__append,
  .v-list-subheader {
    display: none !important;
  }

  .v-divider {
    margin: 8px auto;
    width: 24px;
  }

  .v-icon {
    color: white !important;
    font-size: 24px;
    margin: 0 !important;
    padding: 0 !important;
  }
}

/* Style des tooltips */
:deep(.v-tooltip) {
  background-color: rgba(0, 0, 0, 0.8) !important;
  border-radius: 4px;
  font-size: 0.875rem;
  padding: 4px 8px;
  color: white !important;
}
</style>


