<template>
  <div>
    <Title level="1" class="text-h4">Nouvelle organisation</Title>

    <div class="d-flex align-center mb-4">
      <v-btn icon class="mr-4" to="/dashboard/organizations">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
    </div>

    <v-card>
      <v-form ref="form" @submit.prevent="saveOrganization">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.name"
                label="Nom de l'organisation"
                required
                :rules="[v => !!v || 'Le nom est requis']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.contact_email"
                label="Email de contact"
                type="email"
                required
                :rules="[
                  v => !!v || 'L\'email est requis',
                  v => /.+@.+\..+/.test(v) || 'L\'email doit être valide'
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.phone"
                label="Téléphone"
                required
                :rules="[v => !!v || 'Le téléphone est requis']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.siret"
                label="SIRET"
                required
                :rules="[
                  v => !!v || 'Le SIRET est requis',
                  v => /^\d{14}$/.test(v) || 'Le SIRET doit contenir 14 chiffres'
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="organizationForm.address"
                label="Adresse"
                required
                :rules="[v => !!v || 'L\'adresse est requise']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.postal_code"
                label="Code postal"
                required
                :rules="[
                  v => !!v || 'Le code postal est requis',
                  v => /^\d{5}$/.test(v) || 'Le code postal doit contenir 5 chiffres'
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.city"
                label="Ville"
                required
                :rules="[v => !!v || 'La ville est requise']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.country"
                label="Pays"
                required
                :rules="[v => !!v || 'Le pays est requis']"
              ></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-model="organizationForm.notes"
                label="Notes"
                rows="3"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-title>Responsable de l'organisation</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.first_name"
                label="Prénom"
                required
                :rules="[v => !!v || 'Le prénom est requis']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.last_name"
                label="Nom"
                required
                :rules="[v => !!v || 'Le nom est requis']"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.email"
                label="Email"
                type="email"
                required
                :rules="[
                  v => !!v || 'L\'email est requis',
                  v => /.+@.+\..+/.test(v) || 'L\'email doit être valide'
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.phone"
                label="Téléphone"
                required
                :rules="[v => !!v || 'Le téléphone est requis']"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="text"
            :to="{ name: 'Organizations' }"
          >
            Annuler
          </v-btn>
          <v-btn
            color="primary"
            type="submit"
            :loading="saving"
          >
            Créer l'organisation
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { Title } from '@/components/typography'

export default {
  name: 'NewOrganizationView',
  components: {
    Title
  },
  setup() {
    const router = useRouter()
    const form = ref(null)
    const saving = ref(false)

    const organizationForm = ref({
      name: '',
      contact_email: '',
      phone: '',
      siret: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      notes: ''
    })

    const managerForm = ref({
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      role: 'MANAGER'
    })

    const saveOrganization = async () => {
      const { valid } = await form.value.validate()
      
      if (!valid) {
        console.log('Formulaire invalide, validation échouée')
        return
      }

      saving.value = true
      try {
        console.log('Données de l\'organisation à créer:', organizationForm.value)
        // Créer l'organisation
        const orgResponse = await api.post('/organizations/', organizationForm.value)
        console.log('Organisation créée avec succès:', orgResponse.data)
        const organizationId = orgResponse.data.id

        // Préparer les données du manager
        const managerData = {
          ...managerForm.value,
          organization: organizationId,
          username: managerForm.value.email.split('@')[0] // Générer un username à partir de l'email
        }
        console.log('Données du manager à créer:', managerData)

        // Créer le manager
        const userResponse = await api.post('/users/', managerData)
        console.log('Manager créé avec succès:', userResponse.data)

        // Rediriger vers la liste des organisations
        router.push('/dashboard/organizations')
      } catch (error) {
        console.error('Erreur lors de la création:', error)
        console.error('Détails de l\'erreur:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data
        })
        // Afficher un message d'erreur plus détaillé
        let errorMessage = 'Une erreur est survenue lors de la création'
        if (error.response?.data) {
          const errors = Object.entries(error.response.data)
            .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
            .join('\n')
          errorMessage = `Erreurs de validation:\n${errors}`
        }
        alert(errorMessage)
      } finally {
        saving.value = false
      }
    }

    return {
      form,
      saving,
      organizationForm,
      managerForm,
      saveOrganization
    }
  }
}
</script> 