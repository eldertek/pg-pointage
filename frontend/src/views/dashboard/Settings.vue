<template>
  <DashboardView title="Paramètres">
    <v-tabs v-model="activeTab" grow>
      <v-tab value="profile">Profil</v-tab>
      <v-tab value="security">Sécurité</v-tab>
    </v-tabs>
    
    <v-window v-model="activeTab" class="mt-4">
      <v-window-item value="profile">
        <v-card>
          <v-card-title>Informations du profil</v-card-title>
          <v-card-text>
            <v-form ref="profileForm" @submit.prevent="saveProfile">
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
                    :value="profile.phone ? formatPhoneNumber(profile.phone) : ''"
                    :rules="[rules.phone]"
                    @input="e => profile.phone = e.target.value.replace(/\D/g, '')"
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
      
      <v-window-item value="security">
        <v-card>
          <v-card-title>Sécurité</v-card-title>
          <v-card-text>
            <v-form ref="passwordForm" @submit.prevent="changePassword">
              <v-text-field
                v-model="security.currentPassword"
                label="Mot de passe actuel"
                type="password"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
                autocomplete="current-password"
              ></v-text-field>
              
              <v-text-field
                v-model="security.newPassword"
                label="Nouveau mot de passe"
                type="password"
                variant="outlined"
                :rules="[rules.required, rules.minLength]"
                class="mb-4"
                autocomplete="new-password"
              ></v-text-field>
              
              <v-text-field
                v-model="security.confirmPassword"
                label="Confirmer le mot de passe"
                type="password"
                variant="outlined"
                :rules="[rules.required, passwordMatchRule]"
                class="mb-4"
                autocomplete="new-password"
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
    </v-window>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </DashboardView>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usersApi } from '@/services/api'
import { formatPhoneNumber } from '@/utils/formatters'
import DashboardView from '@/components/dashboard/DashboardView.vue'

const activeTab = ref('profile')
const profileForm = ref(null)
const passwordForm = ref(null)

const profile = ref({
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  username: ''
})

const security = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const saving = ref({
  profile: false,
  security: false
})

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const rules = {
  required: v => !!v || 'Ce champ est requis',
  email: v => /.+@.+\..+/.test(v) || 'Veuillez entrer un email valide',
  minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères',
  phone: v => !v || /^[0-9]{10}$/.test(v.replace(/\D/g, '')) || 'Le numéro de téléphone doit contenir 10 chiffres'
}

const passwordMatchRule = computed(() => {
  return v => v === security.value.newPassword || 'Les mots de passe ne correspondent pas'
})

const loadProfileData = async () => {
  try {
    const response = await usersApi.getProfile()
    profile.value = {
      firstName: response.data.first_name,
      lastName: response.data.last_name,
      email: response.data.email,
      phone: response.data.phone_number || '',
      username: response.data.username
    }
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
      await usersApi.updateProfile({
        firstName: profile.value.firstName,
        lastName: profile.value.lastName,
        email: profile.value.email,
        phone: profile.value.phone,
        username: profile.value.username
      })
      showSuccess('Profil mis à jour avec succès')
    } catch (error) {
      console.error('Erreur lors de la mise à jour du profil:', error)
      showError('Erreur lors de la mise à jour du profil')
    } finally {
      saving.value.profile = false
    }
  }
}

const changePassword = async () => {
  const isValid = await passwordForm.value.validate()
  
  if (isValid.valid) {
    saving.value.security = true
    try {
      await usersApi.changePassword({
        currentPassword: security.value.currentPassword,
        newPassword: security.value.newPassword
      })
      
      security.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      
      showSuccess('Mot de passe changé avec succès')
    } catch (error) {
      console.error('Erreur lors du changement de mot de passe:', error)
      const errorMessage = error.response?.data?.error || 'Une erreur est survenue lors du changement de mot de passe'
      showError(errorMessage)
    } finally {
      saving.value.security = false
    }
  }
}

const showSuccess = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'success'
  }
}

const showError = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'error'
  }
}
</script>

<style scoped>
/* Style des boutons */
:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}

/* Style des boutons icônes */
:deep(.v-btn--icon) {
  background-color: transparent !important;
  opacity: 1 !important;
}

:deep(.v-btn--icon .v-icon) {
  color: inherit !important;
  opacity: 1 !important;
}

/* Correction des overlays et underlays */
:deep(.v-btn__overlay),
:deep(.v-btn__underlay) {
  opacity: 0 !important;
}
</style>

