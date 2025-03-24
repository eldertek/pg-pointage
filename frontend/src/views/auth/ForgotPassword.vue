<template>
  <v-card class="auth-card">
    <v-card-title class="text-center">
      <h2 class="text-h5 mb-2">Mot de passe oublié</h2>
      <p class="text-subtitle-1">Réinitialiser votre mot de passe</p>
    </v-card-title>
    
    <v-card-text>
      <v-form @submit.prevent="requestReset" ref="form">
        <v-text-field
          v-model="email"
          label="Email"
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
          Envoyer le lien de réinitialisation
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
import { ref } from 'vue'

export default {
  name: 'ForgotPasswordView',
  setup() {
    const form = ref(null)
    const email = ref('')
    const loading = ref(false)
    const error = ref(null)
    const success = ref(null)
    
    const rules = {
      required: v => !!v || 'Ce champ est requis',
      email: v => /.+@.+\..+/.test(v) || 'Veuillez entrer un email valide'
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
          success.value = 'Si votre adresse est correcte, vous recevrez un email avec les instructions pour réinitialiser votre mot de passe.'
          email.value = ''
        } catch (err) {
          error.value = 'Une erreur est survenue lors de la demande de réinitialisation'
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

