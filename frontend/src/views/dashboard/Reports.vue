<template>
  <div>
    <h1 class="text-h4 mb-4">Rapports</h1>
    
    <v-row>
      <v-col cols="12" lg="4">
        <v-card class="mb-4">
          <v-card-title>Générer un rapport</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="generateReport" ref="form">
              <v-text-field
                v-model="reportForm.name"
                label="Nom du rapport"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
              ></v-text-field>
              
              <v-select
                v-model="reportForm.type"
                label="Type de rapport"
                :items="reportTypeOptions"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
              ></v-select>
              
              <v-select
                v-model="reportForm.format"
                label="Format de rapport"
                :items="reportFormatOptions"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
              ></v-select>
              
              <v-select
                v-model="reportForm.site"
                label="Site"
                :items="siteOptions"
                variant="outlined"
                clearable
                class="mb-4"
              ></v-select>
              
              <v-text-field
                v-model="reportForm.startDate"
                label="Date de début"
                type="date"
                variant="outlined"
                :rules="[rules.required]"
                class="mb-4"
              ></v-text-field>
              
              <v-text-field
                v-model="reportForm.endDate"
                label="Date de fin"
                type="date"
                variant="outlined"
                :rules="[rules.required, dateRangeRule]"
                class="mb-4"
              ></v-text-field>
              
              <v-btn
                type="submit"
                color="primary"
                block
                :loading="generating"
              >
                Générer le rapport
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" lg="8">
        <v-card>
          <v-card-title>Rapports générés</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="reports"
              :loading="loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <template #actions="{ item }">
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="primary"
                  @click="downloadReport(item.raw.id)"
                >
                  <v-icon>mdi-download</v-icon>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  color="error"
                  @click="deleteReport(item.raw.id)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
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
import { ref } from 'vue'

export default {
  name: 'ReportsView',
  setup() {
    const form = ref(null)
    const loading = ref(true)
    const generating = ref(false)
    
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Type', align: 'start', key: 'type' },
      { title: 'Format', align: 'center', key: 'format' },
      { title: 'Période', align: 'start', key: 'period' },
      { title: 'Site', align: 'start', key: 'site' },
      { title: 'Créé le', align: 'start', key: 'createdAt' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const reportTypeOptions = ref(['Journalier', 'Hebdomadaire', 'Mensuel', 'Personnalisé'])
    const reportFormatOptions = ref(['PDF', 'CSV', 'Excel'])
    const siteOptions = ref(['Tous les sites', 'Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    
    const reports = ref([])
    
    const reportForm = ref({
      name: '',
      type: 'Mensuel',
      format: 'PDF',
      site: '',
      startDate: '',
      endDate: ''
    })
    
    const snackbar = ref({
      show: false,
      text: '',
      color: 'success'
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis'
    }
    
    const dateRangeRule = v => {
      if (!v || !reportForm.value.startDate) return true
      return new Date(v) >= new Date(reportForm.value.startDate) || 'La date de fin doit être postérieure à la date de début'
    }
    
    const generateReport = async () => {
      const isValid = await form.value.validate()
      
      if (isValid.valid) {
        generating.value = true
        
        try {
          // Simulation d'API call
          await new Promise(resolve => setTimeout(resolve, 2000))
          
          // Simulons l'ajout d'un nouveau rapport
          const newReport = {
            id: Math.floor(Math.random() * 1000),
            name: reportForm.value.name,
            type: reportForm.value.type,
            format: reportForm.value.format,
            period: `${reportForm.value.startDate} - ${reportForm.value.endDate}`,
            site: reportForm.value.site || 'Tous les sites',
            createdAt: new Date().toLocaleDateString()
          }
          
          reports.value.unshift(newReport)
          
          // Réinitialiser le formulaire
          reportForm.value = {
            name: '',
            type: 'Mensuel',
            format: 'PDF',
            site: '',
            startDate: '',
            endDate: ''
          }
          
          showSuccess('Rapport généré avec succès')
        } catch (error) {
          showError('Erreur lors de la génération du rapport')
        } finally {
          generating.value = false
        }
      }
    }
    
    const downloadReport = (id) => {
      // Simulation de téléchargement
      console.log(`Téléchargement du rapport ${id}`)
      showSuccess('Téléchargement démarré')
    }
    
    const deleteReport = (id) => {
      // Simulation de suppression
      console.log(`Suppression du rapport ${id}`)
      
      // Pour la démo, on supprime localement
      reports.value = reports.value.filter(r => r.id !== id)
      
      showSuccess('Rapport supprimé avec succès')
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
    
    // Charger les rapports initiaux
    setTimeout(() => {
      reports.value = [
        { 
          id: 1, 
          name: 'Rapport mensuel Mars 2025', 
          type: 'Mensuel',
          format: 'PDF',
          period: '01/03/2025 - 31/03/2025',
          site: 'Tous les sites',
          createdAt: '31/03/2025'
        },
        { 
          id: 2, 
          name: 'Rapport hebdomadaire S10', 
          type: 'Hebdomadaire',
          format: 'Excel',
          period: '04/03/2025 - 10/03/2025',
          site: 'Centre Commercial',
          createdAt: '11/03/2025'
        },
        { 
          id: 3, 
          name: 'Rapport mensuel Février 2025', 
          type: 'Mensuel',
          format: 'PDF',
          period: '01/02/2025 - 29/02/2025',
          site: 'Tous les sites',
          createdAt: '29/02/2025'
        }
      ]
      loading.value = false
    }, 1000)
    
    return {
      form,
      loading,
      generating,
      headers,
      reportTypeOptions,
      reportFormatOptions,
      siteOptions,
      reports,
      reportForm,
      snackbar,
      rules,
      dateRangeRule,
      generateReport,
      downloadReport,
      deleteReport
    }
  }
}
</script>

