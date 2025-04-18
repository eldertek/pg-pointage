<template>
  <DashboardView title="settings.title">
    <v-tabs v-model="activeTab" grow>
      <v-tab value="profile">{{ $t('settings.profile') }}</v-tab>
      <v-tab value="security">{{ $t('settings.security') }}</v-tab>
      <v-tab value="language">{{ $t('settings.language') }}</v-tab>
    </v-tabs>

    <v-window v-model="activeTab" class="mt-4">
      <v-window-item value="profile">
        <v-card>
          <v-card-title>{{ $t('dashboard.informations_du_profil') }}</v-card-title>
          <v-card-text>
            <v-form ref="profileForm" @submit.prevent="saveProfile">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.firstName"
                    :label="$t('profile.firstName')"
                    variant="outlined"
                    :rules="[rules.required]"
                  ></v-text-field>
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.lastName"
                    :label="$t('profile.lastName')"
                    variant="outlined"
                    :rules="[rules.required]"
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.email"
                    :label="$t('auth.email')"
                    type="email"
                    variant="outlined"
                    :rules="[rules.required, rules.email]"
                  ></v-text-field>
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="profile.phone"
                    :label="$t('profile.phone')"
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
                {{ $t('common.save') }}
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="security">
        <v-card>
          <v-card-title>{{ $t('settings.security') }}</v-card-title>
          <v-card-text>
            <v-form ref="passwordForm" @submit.prevent="changePassword">
              <input type="text"
                :value="profile.username"
                autocomplete="username"
                style="display: none;"
                aria-hidden="true"
              />
              <v-text-field
                v-model="security.currentPassword"
                :label="$t('auth.currentPassword')"
                type="password"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
                autocomplete="current-password"
              ></v-text-field>

              <v-text-field
                v-model="security.newPassword"
                :label="$t('auth.newPassword')"
                type="password"
                variant="outlined"
                :rules="[rules.required, rules.minLength]"
                class="mb-4"
                autocomplete="new-password"
              ></v-text-field>

              <v-text-field
                v-model="security.confirmPassword"
                :label="$t('auth.confirmPassword')"
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
                {{ $t('dashboard.changer_le_mot_de_passe') }}
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- Onglet Langue -->
      <v-window-item value="language">
        <v-card>
          <v-card-title>{{ $t('settings.language') }}</v-card-title>
          <v-card-text>
            <v-form ref="languageForm" @submit.prevent="saveLanguage">
              <v-select
                v-model="language.selected"
                :items="languageOptions"
                item-title="text"
                item-value="value"
                :label="$t('profile.language')"
                variant="outlined"
                class="mb-4"
              ></v-select>

              <v-btn
                type="submit"
                color="primary"
                :loading="saving.language"
              >
                {{ $t('common.save') }}
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
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const activeTab = ref('profile')
const profileForm = ref(null)
const passwordForm = ref(null)
const languageForm = ref(null)

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

const language = ref({
  selected: localStorage.getItem('language') || 'fr'
})

const languageOptions = ref([
  { text: t('profile.languages.fr'), value: 'fr' },
  { text: t('profile.languages.en'), value: 'en' }
])

const saving = ref({
  profile: false,
  security: false,
  language: false
})

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const rules = {
  required: v => !!v || t('common.fieldRequired'),
  email: v => /.+@.+\..+/.test(v) || t('auth.invalidEmail'),
  minLength: v => v.length >= 8 || t('auth.passwordMinLength'),
  phone: v => !v || /^[0-9]{10}$/.test(v.replace(/\D/g, '')) || t('profile.phoneFormat')
}

const passwordMatchRule = computed(() => {
  return v => v === security.value.newPassword || t('auth.passwordMismatch')
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

    // Mettre à jour la langue avec la valeur du profil
    if (response.data.language) {
      language.value.selected = response.data.language
      locale.value = response.data.language
      localStorage.setItem('language', response.data.language)
    }
  } catch (error) {
    console.error('Erreur lors du chargement du profil:', error)
    showError(t('common.error') + ': ' + t('profile.title'))
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
      showSuccess(t('profile.profileUpdated'))
    } catch (error) {
      console.error('Erreur lors de la mise à jour du profil:', error)
      showError(t('common.error'))
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

      showSuccess(t('auth.passwordChanged'))
    } catch (error) {
      console.error('Erreur lors du changement de mot de passe:', error)
      const errorMessage = error.response?.data?.error || t('common.error')
      showError(errorMessage)
    } finally {
      saving.value.security = false
    }
  }
}

const saveLanguage = async () => {
  saving.value.language = true
  try {
    await usersApi.updatePreferences({ language: language.value.selected })

    // Mettre à jour la langue de l'application
    locale.value = language.value.selected

    showSuccess(t('profile.profileUpdated'))
  } catch (error) {
    console.error('Erreur lors de la mise à jour de la langue:', error)
    showError(t('common.error'))
  } finally {
    saving.value.language = false
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

