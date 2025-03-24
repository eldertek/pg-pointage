<template>
  <div class="profile-container">
    <v-card class="mb-4">
      <v-card-title>Mon profil</v-card-title>
      <v-card-text>
        <div class="text-center mb-4">
          <v-avatar color="primary" size="100">
            <span class="text-h4 text-white">{{ userInitials }}</span>
          </v-avatar>
          <h2 class="text-h5 mt-2">{{ user.firstName }} {{ user.lastName }}</h2>
          <p class="text-subtitle-1">{{ user.role }}</p>
        </div>
        
        <v-list>
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-email"></v-icon>
            </template>
            <v-list-item-title>Email</v-list-item-title>
            <v-list-item-subtitle>{{ user.email }}</v-list-item-subtitle>
          </v-list-item>
          
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-phone"></v-icon>
            </template>
            <v-list-item-title>Téléphone</v-list-item-title>
            <v-list-item-subtitle>{{ user.phone }}</v-list-item-subtitle>
          </v-list-item>
          
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-domain"></v-icon>
            </template>
            <v-list-item-title>Organisation</v-list-item-title>
            <v-list-item-subtitle>{{ user.organization }}</v-list-item-subtitle>
          </v-list-item>
          
          <v-list-item>
            <template v-slot:prepend>
              <v-icon icon="mdi-badge-account"></v-icon>
            </template>
            <v-list-item-title>ID Employé</v-list-item-title>
            <v-list-item-subtitle>{{ user.employeeId }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <v-card class="mb-4">
      <v-card-title>
        <div class="d-flex justify-space-between align-center">
          <span>Sites assignés ({{ assignedSites.length }})</span>
          <v-chip color="primary" size="small">{{ user.mainSite }}</v-chip>
        </div>
      </v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item v-for="(site, index) in assignedSites" :key="index">
            <template v-slot:prepend>
              <v-icon icon="mdi-map-marker"></v-icon>
            </template>
            <v-list-item-title>{{ site.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ site.schedule }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <v-card>
      <v-card-title>Actions</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item @click="showPasswordDialog = true">
            <template v-slot:prepend>
              <v-icon icon="mdi-lock"></v-icon>
            </template>
            <v-list-item-title>Changer mon mot de passe</v-list-item-title>
          </v-list-item>
          
          <v-list-item to="/mobile/report-anomaly">
            <template v-slot:prepend>
              <v-icon icon="mdi-alert-circle"></v-icon>
            </template>
            <v-list-item-title>Signaler une anomalie</v-list-item-title>
          </v-list-item>
          
          <v-list-item @click="showLogoutDialog = true">
            <template v-slot:prepend>
              <v-icon icon="mdi-logout" color="error"></v-icon>
            </template>
            <v-list-item-title class="text-error">Se déconnecter</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <!-- Dialogue de changement de mot de passe -->
    <v-dialog v-model="showPasswordDialog" max-width="500">
      <v-card>
        <v-card-title>Changer mon mot de passe</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="changePassword" ref="passwordForm">
            <v-text-field
              v-model="passwordForm.currentPassword"
              label="Mot de passe actuel"
              type="password"
              variant="outlined"
              :rules="[rules.required]"
              class="mb-4"
            ></v-text-field>
            
            <v-text-field
              v-model="passwordForm.newPassword"
              label="Nouveau mot de passe"
              type="password"
              variant="outlined"
              :rules="[rules.required, rules.minLength]"
              class="mb-4"
            ></v-text-field>
            
            <v-text-field
              v-model="passwordForm.confirmPassword"
              label="Confirmer le mot de passe"
              type="password"
              variant="outlined"
              :rules="[rules.required, passwordMatchRule]"
              class="mb-4"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showPasswordDialog = false">Annuler</v-btn>
          <v-btn color="primary" @click="changePassword" :loading="saving">Changer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Dialogue de déconnexion -->
    <v-dialog v-model="showLogoutDialog" max-width="300">
      <v-card>
        <v-card-title>Déconnexion</v-card-title>
        <v-card-text>Êtes-vous sûr de vouloir vous déconnecter ?</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showLogoutDialog = false">Annuler</v-btn>
          <v-btn color="error" variant="text" @click="logout">Déconnecter</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'ProfileView',
  setup() {
    const authStore = useAuthStore()
    
    const showPasswordDialog = ref(false)
    const showLogoutDialog = ref(false)
    const saving = ref(false)
    
    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
    
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    
    // Utilisateur simulé pour la démo
    const user = ref({
      firstName: 'Pierre',
      lastName: 'Lambert',
      role: 'Employé',
      email: 'pierre.lambert@example.com',
      phone: '06 34 56 78 90',
      organization: 'Planète Gardiens Paris',
      employeeId: 'EMP003',
      mainSite: 'Centre Commercial'
    })
    
    const assignedSites = ref([
      { name: 'Centre Commercial', schedule: 'Gardiennage jour' },
      { name: 'Hôpital Nord', schedule: 'Gardiennage nuit' }
    ])
    
    const userInitials = computed(() => {
      return `${user.value.firstName.charAt(0)}${user.value.lastName.charAt(0)}`
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis',
      minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
    }
    
    const passwordMatchRule = computed(() => {
      return v => v === passwordForm.value.newPassword || 'Les mots de passe ne correspondent pas'
    })
    
    const changePassword = async () => {
      if (!passwordForm.value) return
      
      const isValid = await passwordForm.value.validate()
      
      if (isValid.valid) {
        saving.value = true
        
        try {
          // Simulation d'API call
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          // Réinitialiser les champs
          passwordForm.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
          
          showPasswordDialog.value = false
          showSuccess('Mot de passe changé avec succès')
        } catch (error) {
          showError('Erreur lors du changement de mot de passe')
        } finally {
          saving.value = false
        }
      }
    }
    
    const logout = () => {
      authStore.logout()
    }
    
    const showSuccess = (text) => {
      snackbar.value = {
        show: true,
        text,
        color: 'success'
      }
    }
    
    const showError = (text) => {
      snackbar.value = {
        show: true,
        text,
        color: 'error'
      }
    }
    
    return {
      user,
      assignedSites,
      userInitials,
      passwordForm,
      showPasswordDialog,
      showLogoutDialog,
      saving,
      snackbar,
      rules,
      passwordMatchRule,
      changePassword,
      logout
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 16px;
}
</style>

