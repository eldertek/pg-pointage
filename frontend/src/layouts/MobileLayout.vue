<template>
  <div class="mobile-layout">
    <v-app-bar color="primary" density="compact">
      <v-app-bar-title>Planète Gardiens</v-app-bar-title>
      <template #append>
        <v-btn icon @click="showLogoutDialog = true">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </template>
    </v-app-bar>
    
    <v-main>
      <router-view />
    </v-main>
    
    <v-bottom-navigation v-if="!isSimplifiedView" v-model="activeTab" grow>
      <v-btn value="home" to="/mobile" variant="flat">
        <v-icon>mdi-view-dashboard</v-icon>
        Accueil
      </v-btn>
      
      <v-btn value="scan" to="/mobile/scan" variant="flat">
        <v-icon>mdi-qrcode-scan</v-icon>
        Scanner
      </v-btn>
      
      <v-btn value="history" to="/mobile/history" variant="flat">
        <v-icon>mdi-history</v-icon>
        Historique
      </v-btn>
      
      <v-btn value="profile" to="/mobile/profile" variant="flat">
        <v-icon>mdi-account</v-icon>
        Profil
      </v-btn>
    </v-bottom-navigation>

    <!-- Navigation simplifiée -->
    <v-bottom-navigation v-else v-model="activeTab" grow>
      <v-btn value="scan" to="/mobile/scan" variant="flat">
        <v-icon>mdi-qrcode-scan</v-icon>
        Scanner
      </v-btn>
      
      <v-btn value="profile" to="/mobile/profile" variant="flat">
        <v-icon>mdi-account</v-icon>
        Profil
      </v-btn>
    </v-bottom-navigation>
    
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
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

export default {
  name: 'MobileLayout',
  setup() {
    const authStore = useAuthStore()
    const router = useRouter()
    const showLogoutDialog = ref(false)
    const activeTab = ref('home')
    
    const isSimplifiedView = computed(() => authStore.user?.simplified_mobile_view)

    // Mettre à jour l'onglet actif en fonction de la route
    watch(() => router.currentRoute.value.path, (newPath) => {
      if (newPath === '/mobile') activeTab.value = 'home'
      else if (newPath === '/mobile/scan') activeTab.value = 'scan'
      else if (newPath === '/mobile/history') activeTab.value = 'history'
      else if (newPath === '/mobile/profile') activeTab.value = 'profile'
    }, { immediate: true })
    
    // Rediriger vers /mobile/scan si vue simplifiée et sur une route non autorisée
    if (isSimplifiedView.value) {
      const allowedRoutes = ['/mobile/scan', '/mobile/profile']
      if (!allowedRoutes.includes(router.currentRoute.value.path)) {
        router.push('/mobile/scan')
      }
    }
    
    const logout = () => {
      authStore.logout()
    }
    
    return {
      showLogoutDialog,
      logout,
      isSimplifiedView,
      activeTab
    }
  }
}
</script>

<style scoped>
.mobile-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.v-main {
  flex: 1;
  background-color: #f5f5f5;
}
</style>

