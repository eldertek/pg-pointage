<template>
  <div class="login-container">
    <v-card class="login-card">
      <v-card-title class="text-center">
        <AppTitle :level="1" class="text-h4 mb-2">{{ $t('auth.appName') }}</AppTitle>
        <p class="text-subtitle-1">{{ $t('auth.login') }}</p>
      </v-card-title>

      <v-card-text>
        <v-form ref="form" @submit.prevent="login">
          <v-text-field
            v-model="email"
            :label="$t('auth.email')"
            type="email"
            :rules="[rules.required, rules.email]"
            prepend-inner-icon="mdi-email"
            variant="outlined"
            class="mb-4"
            autocomplete="username email"
          ></v-text-field>

          <v-text-field
            v-model="password"
            :label="$t('auth.password')"
            :type="showPassword ? 'text' : 'password'"
            :rules="[rules.required]"
            prepend-inner-icon="mdi-lock"
            :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
            variant="outlined"
            class="mb-6"
            autocomplete="current-password"
            @click:append-inner="showPassword = !showPassword"
          ></v-text-field>

          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mb-4"
          >
            {{ error }}
          </v-alert>

          <v-btn
            type="submit"
            color="primary"
            block
            size="large"
            :loading="loading"
          >
            {{ $t('auth.login') }}
          </v-btn>

          <div class="text-center mt-4">
            <v-btn
              variant="text"
              color="primary"
              to="/forgot-password"
              size="small"
            >
              {{ $t('auth.forgotPassword') }}
            </v-btn>
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { AppTitle } from '@/components/typography'

export default {
  name: 'LoginView',
  components: {
    AppTitle
  },
  setup() {
    const { t } = useI18n()
    const authStore = useAuthStore()
    const form = ref(null)
    const email = ref('')
    const password = ref('')
    const showPassword = ref(false)
    const loading = ref(false)
    const error = ref(null)

    const rules = {
      required: v => !!v || t('auth.fieldRequired'),
      email: v => /.+@.+\..+/.test(v) || t('auth.invalidEmail')
    }

    const login = async () => {
      const isValid = await form.value.validate()

      if (isValid.valid) {
        loading.value = true
        error.value = null

        try {
          const success = await authStore.login({
            email: email.value,
            password: password.value
          })

          if (!success) {
            error.value = authStore.error
          }
        } catch (err) {
          error.value = t('auth.loginError')
        } finally {
          loading.value = false
        }
      }
    }

    return {
      form,
      email,
      password,
      showPassword,
      loading,
      error,
      rules,
      login
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
  background-color: #f5f5f5;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 16px;
}
</style>

