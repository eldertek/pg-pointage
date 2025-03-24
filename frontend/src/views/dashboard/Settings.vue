<template>
  <div>
    <h1 class="text-h4 mb-4">Paramètres</h1>
    
    <v-tabs v-model="activeTab" grow>
      <v-tab value="profile">Profil</v-tab>
      <v-tab value="notifications">Notifications</v-tab>
      <v-tab value="security">Sécurité</v-tab>
      <v-tab value="appearance">Apparence</v-tab>
    </v-tabs>
    
    <v-window v-model="activeTab" class="mt-4">
      <v-window-item value="profile">
        <v-card>
          <v-card-title>Informations du profil</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="saveProfile" ref="profileForm">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.firstName"
                    label="Prénom"
                    variant="outlined"
                    :rules="[rules.required]"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.lastName"
                    label="Nom"
                    variant="outlined"
                    :rules="[rules.required]"
                  ></v-text-field>
                </v-col>
              </v-row>
              
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.email"
                    label="Email"
                    type="email"
                    variant="outlined"
                    :rules="[rules.required, rules.email]"
                  ></v-text-field>
                </v-col>
                
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.phone"
                    label="Téléphone"
                    variant="outlined"
                  ></v-text-field>
                </v-col>
              </v-row>
              
              <v-btn
                type="submit"
                color="primary"
                :loading="saving.profile"
              >
                Enregistrer
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>
      
      <v-window-item value="notifications">
        <v-card>
          <v-card-title>Paramètres de notifications</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="saveNotifications" ref="notificationsForm">
              <v-switch
                v-model="notifications.email"
                label="Recevoir des notifications par email"
                color="primary"
              ></v-switch>
              
              <v-switch
                v-model="notifications.app"
                label="Recevoir des notifications dans l'application"
                color="primary"
              ></v-switch>
              
              <v-divider class="my-4"></v-divider>
              
              <h3 class="text-h6 mb-2">Types de notifications</h3>
              
              <v-checkbox
                v-model="notifications.types"
                label="Retards"
                value="lates"
                color="primary"
              ></v-checkbox>
              
              <v-checkbox
                v-model="notifications.types"
                label="Départs anticipés"
                value="earlyDepartures"
                color="primary"
              ></v-checkbox>
              
              <v-checkbox
                v-model="notifications.types"
                label="Anomalies"
                value="anomalies"
                color="primary"
              ></v-checkbox>
              
              <v-checkbox
                v-model="notifications.types"
                label="Rapports"
                value="reports"
                color="primary"
              ></v-checkbox>
              
              <v-btn
                type="submit"
                color="primary"
                :loading="saving.notifications"
              >
                Enregistrer
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>
      
      <v-window-item value="security">
        <v-card>
          <v-card-title>Sécurité</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="changePassword" ref="passwordForm">
              <v-text-field
                v-model="security.currentPassword"
                label="Mot de passe actuel"
                type="password"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
              ></v-text-field>
              
              <v-text-field
                v-model="security.newPassword"
                label="Nouveau mot de passe"
                type="password"
                variant="outlined"
                :rules="[rules.required, rules.minLength]"
                class="mb-4"
              ></v-text-field>
              
              <v-text-field
                v-model="security.confirmPassword"
                label="Confirmer le mot de passe"
                type="password"
                variant="outlined"
                :rules="[rules.required, passwordMatchRule]"
                class="mb-4"
              ></v-text-field>
              
              <v-btn
                type="submit"
                color="primary"
                :loading="saving.security"
              >
                Changer le mot de passe
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>
      
      <v-window-item value="appearance">
        <v-card>
          <v-card-title>Apparence</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="saveAppearance" ref="appearanceForm">
              <h3 class="text-h6 mb-2">Thème</h3>
              
              <v-radio-group v-model="appearance.theme" class="mb-4">
                <v-radio value="light" label="Clair"></v-radio>
                <v-radio value="dark" label="Sombre"></v-radio>
                <v-radio value="system" label="Suivre les préférences système"></v-radio>
              </v-radio-group>
              
              <h3 class="text-h6 mb-2">Taille du texte</h3>
              
              <v-slider
                v-model="appearance.fontSize"
                label="Taille du texte"
                min="80"
                max="120"
                step="5"
                thumb-label
                :thumb-size="24"
                class="mb-4"
              >
                <template v-slot:append>
                  <div class="text-caption">{{ appearance.fontSize }}%</div>
                </template>
              </v-slider>
              
              <v-btn
                type="submit"
                color="primary"
                :loading="saving.appearance"
              >
                Enregistrer
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
    
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
import api from '@/services/api'

export default {
  name: 'SettingsView',
  setup() {
    const activeTab = ref('profile')
    
    const profileForm = ref(null)
    const notificationsForm = ref(null)
    const passwordForm = ref(null)
    const appearanceForm = ref(null)
    
    const profile = ref({
      firstName: 'Jean',
      lastName: 'Dupont',
      email: 'jean.dupont@example.com',
      phone: '06 12 34 56 78'
    })
    
    const notifications = ref({
      email: true,
      sms: false,
      app: true,
      types: ['lates', 'anomalies', 'reports']
    })
    
    const security = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })
    
    const appearance = ref({
      theme: 'light',
      fontSize: 100
    })
    
    const saving = ref({
      profile: false,
      notifications: false,
      security: false,
      appearance: false
    })
    
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis',
      email: v => /.+@.+\..+/.test(v) || 'Veuillez entrer un email valide',
      minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
    }
    
    const passwordMatchRule = computed(() => {
      return v => v === security.value.newPassword || 'Les mots de passe ne correspondent pas'
    })
    
    const loadProfileData = async () => {
      try {
        console.log('Chargement des données du profil...')
        const response = await api.get('/users/profile')
        console.log('Données du profil reçues:', response.data)
        profile.value = response.data
      } catch (error) {
        console.error('Erreur lors du chargement du profil:', error)
        showError('Erreur lors du chargement des données du profil')
      }
    }

    onMounted(() => {
      loadProfileData()
    })
    
    const saveProfile = async () => {
      const isValid = await profileForm.value.validate()
      
      if (isValid.valid) {
        saving.value.profile = true
        
        try {
          console.log('Envoi des données du profil:', profile.value)
          const response = await api.put('/users/profile', profile.value)
          console.log('Réponse de mise à jour du profil:', response.data)
          showSuccess('Profil mis à jour avec succès')
        } catch (error) {
          console.error('Erreur lors de la mise à jour du profil:', error)
          showError('Erreur lors de la mise à jour du profil')
        } finally {
          saving.value.profile = false
        }
      }
    }
    
    const saveNotifications = async () => {
      saving.value.notifications = true
      
      try {
        console.log('Envoi des paramètres de notifications:', notifications.value)
        const response = await api.put('/users/notifications', notifications.value)
        console.log('Réponse de mise à jour des notifications:', response.data)
        showSuccess('Paramètres de notifications mis à jour avec succès')
      } catch (error) {
        console.error('Erreur lors de la mise à jour des notifications:', error)
        showError('Erreur lors de la mise à jour des paramètres de notifications')
      } finally {
        saving.value.notifications = false
      }
    }
    
    const changePassword = async () => {
      const isValid = await passwordForm.value.validate()
      
      if (isValid.valid) {
        saving.value.security = true
        
        try {
          console.log('Envoi de la demande de changement de mot de passe')
          const response = await api.put('/users/password', {
            currentPassword: security.value.currentPassword,
            newPassword: security.value.newPassword
          })
          console.log('Réponse du changement de mot de passe:', response.data)
          
          security.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
          
          showSuccess('Mot de passe changé avec succès')
        } catch (error) {
          console.error('Erreur lors du changement de mot de passe:', error)
          showError('Erreur lors du changement de mot de passe')
        } finally {
          saving.value.security = false
        }
      }
    }
    
    const saveAppearance = async () => {
      saving.value.appearance = true
      
      try {
        console.log('Envoi des paramètres d\'apparence:', appearance.value)
        const response = await api.put('/users/appearance', appearance.value)
        console.log('Réponse de mise à jour de l\'apparence:', response.data)
        showSuccess('Paramètres d\'apparence mis à jour avec succès')
      } catch (error) {
        console.error('Erreur lors de la mise à jour de l\'apparence:', error)
        showError('Erreur lors de la mise à jour des paramètres d\'apparence')
      } finally {
        saving.value.appearance = false
      }
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
      activeTab,
      profileForm,
      notificationsForm,
      passwordForm,
      appearanceForm,
      profile,
      notifications,
      security,
      appearance,
      saving,
      snackbar,
      rules,
      passwordMatchRule,
      loadProfileData,
      saveProfile,
      saveNotifications,
      changePassword,
      saveAppearance
    }
  }
}
</script>

