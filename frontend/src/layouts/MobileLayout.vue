<template>
  <div class="mobile-layout">
    <v-app-bar color="primary" density="compact">
      <v-app-bar-title>Planète Gardiens</v-app-bar-title>
      <template v-slot:append>
        <v-btn icon @click="showLogoutDialog = true">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </template>
    </v-app-bar>
    
    <v-main>
      <router-view />
    </v-main>
    
    <v-bottom-navigation grow color="primary">
      <v-btn to="/mobile">
        <v-icon>mdi-view-dashboard</v-icon>
        Accueil
      </v-btn>
      
      <v-btn to="/mobile/scan">
        <v-icon>mdi-qrcode-scan</v-icon>
        Scanner
      </v-btn>
      
      <v-btn to="/mobile/history">
        <v-icon>mdi-history</v-icon>
        Historique
      </v-btn>
      
      <v-btn to="/mobile/profile">
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
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'MobileLayout',
  setup() {
    const authStore = useAuthStore()
    const showLogoutDialog = ref(false)
    
    const logout = () => {
      authStore.logout()
    }
    
    return {
      showLogoutDialog,
      logout
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

