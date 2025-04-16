<template>
  <div class="report-anomaly-container">
    <Title level="1" class="text-h5 mb-4">Signaler une anomalie</Title>
    
    <v-card>
      <v-card-title>{{ $t('mobile.dtails_de_lanomalie') }}</v-card-title>
      <v-card-text>
        <v-form ref="form" @submit.prevent="submitAnomaly">
          <v-select
            v-model="anomaly.site"
            :label="$t('timesheets.site')"
            :items="siteOptions"
            variant="outlined"
            :rules="[rules.required]"
            class="mb-4"
          ></v-select>
          
          <v-select
            v-model="anomaly.type"
            :label="$t('anomalies.type')"
            :items="anomalyTypeOptions"
            variant="outlined"
            :rules="[rules.required]"
            class="mb-4"
          ></v-select>
          
          <v-text-field
            v-model="anomaly.date"
            :label="$t('timesheets.date')"
            type="date"
            variant="outlined"
            :rules="[rules.required]"
            class="mb-4"
          ></v-text-field>
          
          <v-textarea
            v-model="anomaly.description"
            :label="$t('anomalies.description')"
            variant="outlined"
            :rules="[rules.required]"
            class="mb-4"
            rows="4"
            counter
            maxlength="500"
          ></v-textarea>
          
          <v-file-input
            v-model="anomaly.files"
            :label="$t('mobile.joindre_des_photos_optionnel')"
            variant="outlined"
            prepend-icon="mdi-camera"
            accept="image/*"
            multiple
            chips
            class="mb-4"
          ></v-file-input>
          
          <v-btn
            type="submit"
            color="primary"
            block
            size="large"
            :loading="submitting"
          >
            {{ $t('mobile.soumettre_lanomalie') }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="5000"
    >
      {{ snackbar.text }}
      
      <template #actions>
        <v-btn
          v-if="snackbar.color === 'success'"
          color="white"
          variant="text"
          @click="goToHistory"
        >
          {{ $t('mobile.voir_lhistorique') }}
        </v-btn>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          {{ $t('common.close') }}
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Title } from '@/components/typography'

export default {
  name: 'ReportAnomalyView',
  components: {
    Title
  },
  setup() {
    const { t } = useI18n()
    const router = useRouter()
    const form = ref(null)
    const submitting = ref(false)
    
    const siteOptions = ref(['Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    const anomalyTypeOptions = ref([
      'Retard',
      'Départ anticipé',
      'Arrivée manquante',
      'Départ manquant',
      'Heures insuffisantes',
      'Autre'
    ])
    
    const anomaly = ref({
      site: '',
      type: '',
      date: '',
      description: '',
      files: []
    })
    
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis'
    }
    
    const submitAnomaly = async () => {
      const isValid = await form.value.validate()
      
      if (isValid.valid) {
        submitting.value = true
        
        try {
          // Simulation d'API call
          await new Promise(resolve => setTimeout(resolve, 2000))
          
          // Réinitialiser le formulaire
          anomaly.value = {
            site: '',
            type: '',
            date: '',
            description: '',
            files: []
          }
          
          form.value.reset()
          
          showSuccess('Anomalie signalée avec succès. Un manager va traiter votre demande.')
        } catch (error) {
          showError('Erreur lors du signalement de l\'anomalie. Veuillez réessayer.')
        } finally {
          submitting.value = false
        }
      }
    }
    
    const goToHistory = () => {
      router.push('/mobile/history')
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
    
    return {
      form,
      submitting,
      siteOptions,
      anomalyTypeOptions,
      anomaly,
      snackbar,
      rules,
      submitAnomaly,
      goToHistory
    }
  }
}
</script>

<style scoped>
.report-anomaly-container {
  padding: 16px;
}
</style>

