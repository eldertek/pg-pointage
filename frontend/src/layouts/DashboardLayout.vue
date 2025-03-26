<template>
  <v-app>
    <v-app-bar color="primary">
      <v-app-bar-nav-icon 
        @click="$vuetify.display.lgAndUp ? (rail = !rail) : (drawer = !drawer)"
        :icon="rail ? 'mdi-menu' : 'mdi-menu-open'"
      ></v-app-bar-nav-icon>
      <v-app-bar-title>Planète Gardiens - Administration</v-app-bar-title>
      <v-spacer></v-spacer>
      
      <!-- Sélecteur de site -->
      <v-autocomplete
        v-if="isManager || isSuperAdmin"
        v-model="selectedSite"
        :loading="loadingSites"
        :items="siteOptions"
        label="Sélectionner un site"
        item-title="text"
        item-value="value"
        variant="outlined"
        density="compact"
        hide-details
        class="site-selector mx-4"
        clearable
        @update:modelValue="handleSiteChange"
      ></v-autocomplete>

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
          <template v-slot:activator="{ props }">
            <v-list-item to="/dashboard" active-class="primary--text" v-bind="props">
              <template v-slot:prepend>
                <v-icon>mdi-view-dashboard</v-icon>
              </template>
              <v-list-item-title>Tableau de bord</v-list-item-title>
            </v-list-item>
          </template>
          <span>Tableau de bord</span>
        </v-tooltip>

        <!-- Section Super Admin -->
        <template v-if="isSuperAdmin">
          <v-divider class="my-2"></v-divider>
          <v-list-subheader>Administration globale</v-list-subheader>
          
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/admin/users" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-account-cog</v-icon>
                </template>
                <v-list-item-title>Gestion des accès</v-list-item-title>
              </v-list-item>
            </template>
            <span>Gestion des accès</span>
          </v-tooltip>
        </template>

        <!-- Section Manager -->
        <template v-if="isManager">
          <v-divider class="my-2"></v-divider>
          <v-list-subheader>Gestion des employés</v-list-subheader>
          
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/admin/users" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-account-group</v-icon>
                </template>
                <v-list-item-title>Gestion des employés</v-list-item-title>
              </v-list-item>
            </template>
            <span>Gestion des employés</span>
          </v-tooltip>
        </template>

        <!-- Section Gestion -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Gestion opérationnelle</v-list-subheader>
        
        <template v-if="isManager || isSuperAdmin">
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/sites" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-domain</v-icon>
                </template>
                <v-list-item-title>Sites & Plannings</v-list-item-title>
              </v-list-item>
            </template>
            <span>Sites & Plannings</span>
          </v-tooltip>
        </template>

        <!-- Section Suivi -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Suivi & rapports</v-list-subheader>
        
        <template v-if="isManager || isSuperAdmin">
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/timesheets" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-clock-time-four</v-icon>
                </template>
                <v-list-item-title>Pointages</v-list-item-title>
              </v-list-item>
            </template>
            <span>Pointages</span>
          </v-tooltip>
          
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/anomalies" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-alert</v-icon>
                </template>
                <v-list-item-title>Anomalies</v-list-item-title>
              </v-list-item>
            </template>
            <span>Anomalies</span>
          </v-tooltip>
          
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/reports" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-file-chart</v-icon>
                </template>
                <v-list-item-title>Rapports</v-list-item-title>
              </v-list-item>
            </template>
            <span>Rapports</span>
          </v-tooltip>
        </template>

        <!-- Section Configuration -->
        <v-divider class="my-2"></v-divider>
        <v-list-subheader>Configuration</v-list-subheader>
        
        <template v-if="isManager || isSuperAdmin">
          <v-tooltip location="right" :disabled="!rail">
            <template v-slot:activator="{ props }">
              <v-list-item to="/dashboard/settings" active-class="primary--text" v-bind="props">
                <template v-slot:prepend>
                  <v-icon>mdi-cog</v-icon>
                </template>
                <v-list-item-title>Paramètres</v-list-item-title>
              </v-list-item>
            </template>
            <span>Paramètres</span>
          </v-tooltip>
        </template>
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSitesStore } from '@/stores/sites'
import { sitesApi } from '@/services/api'
import { useDisplay } from 'vuetify'

export default {
  name: 'DashboardLayout',
  setup() {
    const authStore = useAuthStore()
    const sitesStore = useSitesStore()
    const display = useDisplay()
    const drawer = ref(true)
    const rail = ref(false)
    const showLogoutDialog = ref(false)
    const selectedSite = ref(null)
    const siteOptions = ref([])
    const loadingSites = ref(false)
    
    const isSuperAdmin = computed(() => authStore.isSuperAdmin)
    const isManager = computed(() => authStore.isManager)
    
    const loadSites = async () => {
      try {
        loadingSites.value = true
        const response = await sitesApi.getAllSites()
        siteOptions.value = response.data.results.map(site => ({
          text: site.name,
          value: site.id
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des sites:', error)
      } finally {
        loadingSites.value = false
      }
    }

    const handleSiteChange = async (siteId) => {
      if (siteId) {
        await sitesStore.setCurrentSite(siteId)
      } else {
        sitesStore.clearCurrentSite()
      }
    }

    onMounted(() => {
      if (isManager.value || isSuperAdmin.value) {
        loadSites()
      }
    })
    
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
      selectedSite,
      siteOptions,
      loadingSites,
      logout,
      handleDrawerOutsideClick,
      handleListItemClick,
      handleSiteChange
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

  .v-list-item:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
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

/* Style du sélecteur de site */
.site-selector {
  max-width: 300px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

:deep(.site-selector .v-field__input) {
  color: white !important;
}

:deep(.site-selector .v-field__outline) {
  --v-field-border-opacity: 0.2;
}

:deep(.site-selector .v-field__append-inner) {
  color: white !important;
}

:deep(.site-selector .v-label) {
  color: rgba(255, 255, 255, 0.7) !important;
}
</style>


