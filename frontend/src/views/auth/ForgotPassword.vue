<template>
  <v-card class="auth-card">
    <v-card-title class="text-center">
      <AppTitle level="2" class="mb-2">{{ $t('auth.forgotPassword') }}</AppTitle>
      <Text>{{ $t('auth.resetPassword') }}</Text>
    </v-card-title>

    <v-card-text>
      <v-form ref="form" @submit.prevent="requestReset">
        <v-text-field
          v-model="email"
          :label="$t('auth.email')"
          type="email"
          :rules="[rules.required, rules.email]"
          prepend-inner-icon="mdi-email"
          variant="outlined"
          class="mb-4"
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
          {{ $t('auth.envoyer_le_lien_de_rinitialisation') }}
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
import { ref } from 'vue'
import { Text } from '@/components/typography'

export default {
  name: 'ForgotPasswordView',
  setup() {
    const { t } = useI18n()
    const form = ref(null)
    const email = ref('')
    const loading = ref(false)
    const error = ref(null)
    const success = ref(null)

    const rules = {
      required: v => !!v || t('auth.fieldRequired'),
      email: v => /.+@.+\..+/.test(v) || t('auth.invalidEmail')
    }

    const requestReset = async () => {
      const isValid = await form.value.validate()

      if (isValid.valid) {
        loading.value = true
        error.value = null
        success.value = null

        try {
          // Simulation d'API call
          await new Promise(resolve => setTimeout(resolve, 1000))
          success.value = t('auth.passwordResetLinkSent', 'Si votre adresse est correcte, vous recevrez un email avec les instructions pour réinitialiser votre mot de passe.')
          email.value = ''
        } catch (err) {
          error.value = t('auth.passwordResetError', 'Une erreur est survenue lors de la demande de réinitialisation')
        } finally {
          loading.value = false
        }
      }
    }

    return {
      form,
      email,
      loading,
      error,
      success,
      rules,
      requestReset
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

