<template>
  <div class="profile-container">
    <v-card class="mb-4">
      <v-card-title>{{ $t('profile.title') }}</v-card-title>
      <v-card-text>
        <div class="text-center mb-4">
          <v-avatar color="primary" size="100">
            <span class="text-h4 text-white">{{ userInitials }}</span>
          </v-avatar>
          <Title :level="2" class="mt-2">{{ user.first_name }} {{ user.last_name }}</Title>
          <Text>{{ roleLabels[user.role] || user.role }}</Text>
        </div>

        <v-list>
          <v-list-item>
            <template #prepend>
              <v-icon icon="mdi-email"></v-icon>
            </template>
            <v-list-item-title>{{ $t('auth.email') }}</v-list-item-title>
            <v-list-item-subtitle>{{ user.email }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item>
            <template #prepend>
              <v-icon icon="mdi-phone"></v-icon>
            </template>
            <v-list-item-title>{{ $t('profile.phone') }}</v-list-item-title>
            <v-list-item-subtitle>{{ user.phone_number ? formatPhoneNumber(user.phone_number) : 'Non renseigné' }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.organization_name">
            <template #prepend>
              <v-icon icon="mdi-domain"></v-icon>
            </template>
            <v-list-item-title>{{ $t('profile.organization') }}</v-list-item-title>
            <v-list-item-subtitle>{{ user.organization_name }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.employee_id">
            <template #prepend>
              <v-icon icon="mdi-badge-account"></v-icon>
            </template>
            <v-list-item-title>{{ $t('mobile.id_employ') }}</v-list-item-title>
            <v-list-item-subtitle>{{ user.employee_id }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.role === 'EMPLOYEE'">
            <template #prepend>
              <v-icon icon="mdi-qrcode-scan"></v-icon>
            </template>
            <v-list-item-title>{{ $t('mobile.mthode_de_scan') }}</v-list-item-title>
            <v-list-item-subtitle>{{ scanPreferenceLabels[user.scan_preference] }}</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="user.role === 'EMPLOYEE'">
            <template #prepend>
              <v-icon icon="mdi-cellphone-cog"></v-icon>
            </template>
            <v-list-item-title>{{ $t('profile.simplifiedView') }}</v-list-item-title>
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

          <!-- Sélection de la langue -->
          <v-list-item>
            <template #prepend>
              <v-icon icon="mdi-translate"></v-icon>
            </template>
            <v-list-item-title>{{ $t('profile.language') }}</v-list-item-title>
            <v-list-item-subtitle>
              <v-select
                v-model="selectedLanguage"
                :items="languageOptions"
                item-title="text"
                item-value="value"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="updateLanguage"
              ></v-select>
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
            <template #prepend>
              <v-icon icon="mdi-map-marker"></v-icon>
            </template>
            <v-list-item-title>{{ site.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ site.address }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <div v-else class="text-center pa-4">
          <v-icon icon="mdi-alert" color="warning" class="mb-2"></v-icon>
          <p class="text-body-1">{{ $t('mobile.aucun_site_assign') }}</p>
        </div>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title>{{ $t('common.actions') }}</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item @click="showPasswordDialog = true">
            <template #prepend>
              <v-icon icon="mdi-lock"></v-icon>
            </template>
            <v-list-item-title>{{ $t('auth.changePassword') }}</v-list-item-title>
          </v-list-item>

          <v-list-item to="/mobile/report-anomaly">
            <template #prepend>
              <v-icon icon="mdi-alert-circle"></v-icon>
            </template>
            <v-list-item-title>{{ $t('profile.reportAnomaly') }}</v-list-item-title>
          </v-list-item>

          <v-list-item @click="showLogoutDialog = true">
            <template #prepend>
              <v-icon icon="mdi-logout" color="error"></v-icon>
            </template>
            <v-list-item-title class="text-error">{{ $t('mobile.se_dconnecter') }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

    <!-- Dialogue de changement de mot de passe -->
    <v-dialog v-model="showPasswordDialog" max-width="500" persistent>
      <v-card>
        <v-card-title>{{ $t('auth.changePassword') }}</v-card-title>
        <v-card-text>
          <v-form ref="passwordForm" @submit.prevent="changePassword">
            <v-text-field
              v-model="passwordForm.currentPassword"
              :label="$t('auth.currentPassword')"
              type="password"
              variant="outlined"
              :rules="[rules.required]"
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.newPassword"
              :label="$t('auth.newPassword')"
              type="password"
              variant="outlined"
              :rules="[rules.required, rules.minLength]"
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.confirmPassword"
              :label="$t('auth.confirmPassword')"
              type="password"
              variant="outlined"
              :rules="[rules.required, passwordMatchRule]"
              class="mb-4"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showPasswordDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" :loading="saving" @click="changePassword">{{ $t('mobile.changer') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialogue de déconnexion -->
    <v-dialog v-model="showLogoutDialog" max-width="300">
      <v-card>
        <v-card-title>{{ $t('auth.logout') }}</v-card-title>
        <v-card-text>{{ $t('mobile.tesvous_sr_de_vouloir_vous_dconnecter') }}</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showLogoutDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" variant="text" @click="logout">{{ $t('mobile.dconnecter') }}</v-btn>
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
import { formatPhoneNumber } from '@/utils/formatters'
import { Title, Text } from '@/components/typography'
import { useI18n } from 'vue-i18n'

export default {
  name: 'ProfileView',
  components: {
    Title,
    Text
  },
  setup() {
    const authStore = useAuthStore()
    const { t, locale } = useI18n()

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
      'ADMIN': 'Administrateur',
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

    const userOrganizations = computed(() => {
      if (!user.value.organizations) return []
      return user.value.organizations.map(org => org.name).join(', ')
    })

    const rules = {
      required: v => !!v || 'Ce champ est requis',
      minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
    }

    const passwordMatchRule = computed(() => {
      return v => v === passwordForm.value.newPassword || 'Les mots de passe ne correspondent pas'
    })

    const simplifiedView = ref(false)

    // Options de langue
    const selectedLanguage = ref(localStorage.getItem('language') || 'fr')
    const languageOptions = [
      { text: t('profile.languages.fr'), value: 'fr' },
      { text: t('profile.languages.en'), value: 'en' }
    ]

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
        // Mettre à jour la langue avec la valeur du profil
        if (response.data.language) {
          selectedLanguage.value = response.data.language
          locale.value = response.data.language
          localStorage.setItem('language', response.data.language)
        }
        // Charger les sites assignés après avoir récupéré le profil
        await fetchAssignedSites()
      } catch (error) {
        showError(t('common.error') + ': ' + t('profile.title'))
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
          text: t('profile.profileUpdated'),
          color: 'success'
        }
      } catch (error) {
        console.error('Erreur lors de la mise à jour des préférences:', error)
        snackbar.value = {
          show: true,
          text: t('common.error'),
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

    // Mettre à jour la langue
    const updateLanguage = async (value) => {
      try {
        saving.value = true
        await usersApi.updatePreferences({ language: value })

        // Mettre à jour le store et le user local
        authStore.updateUser({ language: value })
        user.value.language = value

        // Mettre à jour la langue de l'application
        locale.value = value

        snackbar.value = {
          show: true,
          text: t('profile.profileUpdated'),
          color: 'success'
        }
      } catch (error) {
        console.error('Erreur lors de la mise à jour de la langue:', error)
        snackbar.value = {
          show: true,
          text: t('common.error'),
          color: 'error'
        }
        // Restaurer l'ancienne valeur
        selectedLanguage.value = locale.value
        if (user.value) {
          user.value.language = locale.value
        }
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
      formatPhoneNumber,
      userOrganizations,
      selectedLanguage,
      languageOptions,
      updateLanguage
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 16px;
}
</style>

