<template>
  <v-card class="auth-card">
    <v-card-title class="text-center">
      <Title level="2" class="mb-2">{{ $t('auth.resetPassword') }}</Title>
      <Text>{{ $t('auth.setNewPassword', 'Définir un nouveau mot de passe') }}</Text>
    </v-card-title>

    <v-card-text>
      <v-form ref="form" @submit.prevent="resetPassword">
        <v-text-field
          v-model="password"
          :label="$t('auth.newPassword')"
          :type="showPassword ? 'text' : 'password'"
          :rules="[rules.required, rules.minLength]"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          variant="outlined"
          class="mb-4"
          @click:append-inner="showPassword = !showPassword"
        ></v-text-field>

        <v-text-field
          v-model="confirmPassword"
          :label="$t('auth.confirmPassword')"
          :type="showConfirmPassword ? 'text' : 'password'"
          :rules="[rules.required, rules.match]"
          prepend-inner-icon="mdi-lock-check"
          :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
          variant="outlined"
          class="mb-6"
          @click:append-inner="showConfirmPassword = !showConfirmPassword"
        ></v-text-field>

        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ error }}
        </v-alert>

        <v-alert
          v-if="success"
          type="success"
          variant="tonal"
          class="mb-4"
        >
          {{ success }}
        </v-alert>

        <v-btn
          type="submit"
          color="primary"
          block
          size="large"
          :loading="loading"
        >
          {{ $t('auth.resetPassword') }}
        </v-btn>

        <div class="text-center mt-4">
          <v-btn
            variant="text"
            color="primary"
            to="/login"
            size="small"
          >
            {{ $t('auth.retour_la_connexion') }}
          </v-btn>
        </div>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title, Text } from '@/components/typography'

export default {
  name: 'ResetPasswordView',
  components: {
    Title,
    Text
  },
  setup() {
    const { t } = useI18n()
    const route = useRoute()
    const router = useRouter()
    const form = ref(null)
    const password = ref('')
    const confirmPassword = ref('')
    const showPassword = ref(false)
    const showConfirmPassword = ref(false)
    const loading = ref(false)
    const error = ref(null)
    const success = ref(null)

    const token = computed(() => route.params.token)

    const rules = {
      required: v => !!v || t('auth.fieldRequired'),
      minLength: v => v.length >= 8 || t('auth.passwordMinLength', 'Le mot de passe doit contenir au moins 8 caractères'),
      match: v => v === password.value || t('auth.passwordMismatch')
    }

    const resetPassword = async () => {
      const isValid = await form.value.validate()

      if (isValid.valid) {
        loading.value = true
        error.value = null
        success.value = null

        try {
          // Simulation d'API call
          await new Promise(resolve => setTimeout(resolve, 1000))
          success.value = t('auth.passwordChanged')
          setTimeout(() => {
            router.push('/login')
          }, 2000)
        } catch (err) {
          error.value = t('auth.passwordResetError', 'Une erreur est survenue lors de la réinitialisation du mot de passe')
        } finally {
          loading.value = false
        }
      }
    }

    return {
      form,
      password,
      confirmPassword,
      showPassword,
      showConfirmPassword,
      loading,
      error,
      success,
      rules,
      resetPassword,
      token
    }
  }
}
</script>

<style scoped>
.auth-card {
  width: 100%;
  padding: 16px;
}
</style>

