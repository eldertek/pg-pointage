<template>
  <div class="profile-container">
    <v-card class="mb-4">
      <v-card-title>Mon profil</v-card-title>
      <v-card-text>
        <div class="text-center mb-4">
          <v-avatar color="primary" size="100">
            <span class="text-h4 text-white">{{ userInitials }}</span>
          </v-avatar>
          <h2 class="text-h5 mt-2">{{ user.first_name }} {{ user.last_name }}</h2>
          <p class="text-subtitle-1">{{ roleLabels[user.role] || user.role }}</p>
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
            <v-list-item-subtitle>{{ user.phone_number || 'Non renseigné' }}</v-list-item-subtitle>
          </v-list-item>
          
          <v-list-item v-if="user.organization_name">
            <template v-slot:prepend>
              <v-icon icon="mdi-domain"></v-icon>
            </template>
            <v-list-item-title>Organisation</v-list-item-title>
            <v-list-item-subtitle>{{ user.organization_name }}</v-list-item-subtitle>
          </v-list-item>
          
          <v-list-item v-if="user.employee_id">
            <template v-slot:prepend>
              <v-icon icon="mdi-badge-account"></v-icon>
            </template>
            <v-list-item-title>ID Employé</v-list-item-title>
            <v-list-item-subtitle>{{ user.employee_id }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.role === 'EMPLOYEE'">
            <template v-slot:prepend>
              <v-icon icon="mdi-qrcode-scan"></v-icon>
            </template>
            <v-list-item-title>Méthode de scan</v-list-item-title>
            <v-list-item-subtitle>{{ scanPreferenceLabels[user.scan_preference] }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.role === 'EMPLOYEE'">
            <template v-slot:prepend>
              <v-icon icon="mdi-cellphone-cog"></v-icon>
            </template>
            <v-list-item-title>Vue simplifiée</v-list-item-title>
            <v-list-item-subtitle>
              <v-switch
                v-model="simplifiedView"
                color="primary"
                hide-details
                density="compact"
                @update:model-value="updateSimplifiedView"
              ></v-switch>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
    
    <!-- Sites assignés - uniquement pour les employés -->
    <v-card v-if="user.role === 'EMPLOYEE'" class="mb-4">
      <v-card-title>
        <div class="d-flex justify-space-between align-center">
          <span>Sites assignés ({{ assignedSites.length }})</span>
        </div>
      </v-card-title>
      <v-card-text>
        <v-list v-if="assignedSites.length > 0">
          <v-list-item v-for="site in assignedSites" :key="site.id">
            <template v-slot:prepend>
              <v-icon icon="mdi-map-marker"></v-icon>
            </template>
            <v-list-item-title>{{ site.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ site.address }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <div v-else class="text-center pa-4">
          <v-icon icon="mdi-alert" color="warning" class="mb-2"></v-icon>
          <p class="text-body-1">Aucun site assigné</p>
        </div>
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
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api, { usersApi } from '@/services/api'

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
    
    const user = ref({})
    const assignedSites = ref([])
    
    const roleLabels = {
      'SUPER_ADMIN': 'Super Administrateur',
      'MANAGER': 'Gestionnaire',
      'EMPLOYEE': 'Employé'
    }

    const scanPreferenceLabels = {
      'BOTH': 'NFC et QR Code',
      'NFC_ONLY': 'NFC uniquement',
      'QR_ONLY': 'QR Code uniquement'
    }
    
    const userInitials = computed(() => {
      if (!user.value.first_name || !user.value.last_name) return ''
      return `${user.value.first_name.charAt(0)}${user.value.last_name.charAt(0)}`
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis',
      minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
    }
    
    const passwordMatchRule = computed(() => {
      return v => v === passwordForm.value.newPassword || 'Les mots de passe ne correspondent pas'
    })
    
    const simplifiedView = ref(false)
    
    const fetchAssignedSites = async () => {
      try {
        // Si l'utilisateur n'est pas un employé, on ne charge pas les sites
        if (user.value.role !== 'EMPLOYEE') {
          assignedSites.value = []
          return
        }
        
        const response = await api.get('/sites/', {
          params: {
            assigned_to: user.value.id,
            is_active: true
          }
        })
        assignedSites.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des sites assignés:', error)
        assignedSites.value = []
      }
    }
    
    const fetchUserProfile = async () => {
      try {
        const response = await usersApi.getProfile()
        user.value = response.data
        // Mettre à jour simplifiedView avec la valeur du profil
        simplifiedView.value = response.data.simplified_mobile_view || false
        // Charger les sites assignés après avoir récupéré le profil
        await fetchAssignedSites()
      } catch (error) {
        showError('Erreur lors du chargement du profil')
        console.error('Erreur lors du chargement du profil:', error)
      }
    }
    
    const changePassword = async () => {
      if (!passwordForm.value) return
      
      saving.value = true
      try {
        await usersApi.changePassword({
          currentPassword: passwordForm.value.currentPassword,
          newPassword: passwordForm.value.newPassword
        })
        
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
        console.error('Erreur lors du changement de mot de passe:', error)
      } finally {
        saving.value = false
      }
    }
    
    const logout = () => {
      authStore.logout()
      showLogoutDialog.value = false
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
    
    const updateSimplifiedView = async (value) => {
      try {
        saving.value = true
        await usersApi.updatePreferences({ simplifiedMobileView: value })
        
        // Mettre à jour le store et le user local
        authStore.updateUser({ simplified_mobile_view: value })
        user.value.simplified_mobile_view = value
        
        snackbar.value = {
          show: true,
          text: 'Préférences mises à jour',
          color: 'success'
        }
      } catch (error) {
        console.error('Erreur lors de la mise à jour des préférences:', error)
        snackbar.value = {
          show: true,
          text: 'Erreur lors de la mise à jour des préférences',
          color: 'error'
        }
        // Restaurer l'ancienne valeur dans tous les endroits
        simplifiedView.value = !value
        if (user.value) {
          user.value.simplified_mobile_view = !value
        }
        authStore.updateUser({ simplified_mobile_view: !value })
      } finally {
        saving.value = false
      }
    }
    
    onMounted(() => {
      fetchUserProfile()
    })
    
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
      logout,
      roleLabels,
      scanPreferenceLabels,
      simplifiedView,
      updateSimplifiedView,
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 16px;
}
</style>

