<template>
  <v-card class="auth-card">
    <v-card-title class="text-center">
      <h2 class="text-h5 mb-2">Réinitialisation du mot de passe</h2>
      <p class="text-subtitle-1">Définir un nouveau mot de passe</p>
    </v-card-title>
    
    <v-card-text>
      <v-form @submit.prevent="resetPassword" ref="form">
        <v-text-field
          v-model="password"
          label="Nouveau mot de passe"
          :type="showPassword ? 'text' : 'password'"
          :rules="[rules.required, rules.minLength]"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          variant="outlined"
          class="mb-4"
        ></v-text-field>
        
        <v-text-field
          v-model="confirmPassword"
          label="Confirmer le mot de passe"
          :type="showConfirmPassword ? 'text' : 'password'"
          :rules="[rules.required, rules.match]"
          prepend-inner-icon="mdi-lock-check"
          :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showConfirmPassword = !showConfirmPassword"
          variant="outlined"
          class="mb-6"
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
          Réinitialiser le mot de passe
        </v-btn>
        
        <div class="text-center mt-4">
          <v-btn
            variant="text"
            color="primary"
            to="/login"
            size="small"
          >
            Retour à la connexion
          </v-btn>
        </div>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'ResetPasswordView',
  setup() {
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
      required: v => !!v || 'Ce champ est requis',
      minLength: v => v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères',
      match: v => v === password.value || 'Les mots de passe ne correspondent pas'
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
          success.value = 'Votre mot de passe a été réinitialisé avec succès.'
          setTimeout(() => {
            router.push('/login')
          }, 2000)
        } catch (err) {
          error.value = 'Une erreur est survenue lors de la réinitialisation du mot de passe'
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

