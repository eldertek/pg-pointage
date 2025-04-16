<template>
  <div>
    <Title level="1" class="text-h4">{{ $t('dashboard.nouvelle_organisation') }}</Title>

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
                :label="$t('dashboard.nom_de_lorganisation')"
                required
                :rules="[v => !!v || t('organizations.nameRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.contact_email"
                :label="$t('organizations.contactEmail')"
                type="email"
                required
                :rules="[
                  v => !!v || t('common.fieldRequired'),
                  v => /.+@.+\..+/.test(v) || t('auth.invalidEmail')
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.phone"
                :label="$t('profile.phone')"
                required
                :rules="[v => !!v || t('organizations.phoneRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="organizationForm.siret"
                :label="$t('organizations.siret')"
                required
                :rules="[
                  v => !!v || t('organizations.siretRequired'),
                  v => /^\d{14}$/.test(v) || t('organizations.siretFormat', 'Le SIRET doit contenir 14 chiffres')
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="organizationForm.address"
                :label="$t('sites.address')"
                required
                :rules="[v => !!v || t('sites.addressRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.postal_code"
                :label="$t('sites.postalCode')"
                required
                :rules="[
                  v => !!v || t('organizations.postalCodeRequired'),
                  v => /^\d{5}$/.test(v) || t('sites.postalCodeFormat')
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.city"
                :label="$t('sites.city')"
                required
                :rules="[v => !!v || t('organizations.cityRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model="organizationForm.country"
                :label="$t('sites.country')"
                required
                :rules="[v => !!v || t('organizations.countryRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-model="organizationForm.notes"
                :label="$t('organizations.notes')"
                rows="3"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-title>{{ $t('dashboard.responsable_de_lorganisation') }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.first_name"
                :label="$t('profile.firstName')"
                required
                :rules="[v => !!v || t('common.firstNameRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.last_name"
                :label="$t('profile.lastName')"
                required
                :rules="[v => !!v || t('common.lastNameRequired')]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.email"
                :label="$t('auth.email')"
                type="email"
                required
                :rules="[
                  v => !!v || t('common.fieldRequired'),
                  v => /.+@.+\..+/.test(v) || t('auth.invalidEmail')
                ]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="managerForm.phone"
                :label="$t('profile.phone')"
                required
                :rules="[v => !!v || t('common.phoneRequired')]"
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
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            type="submit"
            :loading="saving"
          >
            {{ $t('dashboard.crer_lorganisation') }}
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
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
    const { t } = useI18n()
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