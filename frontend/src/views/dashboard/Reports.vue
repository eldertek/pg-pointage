<template>
  <DashboardView
    ref="dashboardView"
    title="Rapports"
    form-title="Générer un rapport"
    :saving="generating"
    @save="generateReport"
  >
    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-file-plus"
        @click="openDialog()"
      >
        Générer un rapport
      </v-btn>
    </template>

    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="filters.search"
            label="Rechercher"
            variant="outlined"
            prepend-inner-icon="mdi-magnify"
            clearable
            @update:model-value="applyFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.type"
            label="Type de rapport"
            :items="reportTypeOptions"
            variant="outlined"
            prepend-inner-icon="mdi-file-document"
            clearable
            @update:model-value="applyFilters"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.format"
            label="Format"
            :items="reportFormatOptions"
            variant="outlined"
            prepend-inner-icon="mdi-file-export"
            clearable
            @update:model-value="applyFilters"
          ></v-select>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Contenu principal -->
    <v-data-table
      :headers="headers"
      :items="reports"
      :loading="loading"
      :items-per-page="10"
      :no-data-text="'Aucun rapport trouvé'"
      :loading-text="'Chargement des rapports...'"
      :items-per-page-text="'Lignes par page'"
      :page-text="'{0}-{1} sur {2}'"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: 'Tout', value: -1 }
      ]"
      class="elevation-1"
    >
      <template #item.actions="{ item }">
        <v-btn
          v-tooltip="'Voir les détails'"
          icon
          variant="text"
          size="small"
          color="primary"
          :to="`/dashboard/reports/${item.id}`"
        >
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn
          v-tooltip="'Télécharger'"
          icon
          variant="text"
          size="small"
          color="primary"
          @click="downloadReport(item.id)"
        >
          <v-icon>mdi-download</v-icon>
        </v-btn>
        <v-btn
          v-tooltip="'Supprimer'"
          icon
          variant="text"
          size="small"
          color="error"
          @click="confirmDelete(item.id)"
        >
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Formulaire de génération de rapport -->
    <template #form>
      <DashboardForm ref="form" :errors="formErrors" @submit="generateReport">
        <v-row class="mb-6">
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="reportForm.name"
              label="Nom du rapport"
              density="comfortable"
              variant="outlined"
              :rules="[rules.required]"
            ></v-text-field>
          </v-col>
          
          <v-col cols="12" sm="6">
            <v-select
              v-model="reportForm.type"
              label="Type de rapport"
              :items="reportTypeOptions"
              density="comfortable"
              variant="outlined"
              :rules="[rules.required]"
            ></v-select>
          </v-col>

          <v-col cols="12" sm="6">
            <v-select
              v-model="reportForm.format"
              label="Format de rapport"
              :items="reportFormatOptions"
              density="comfortable"
              variant="outlined"
              :rules="[rules.required]"
            ></v-select>
          </v-col>
          
          <v-col cols="12" sm="6">
            <v-select
              v-if="!currentSiteId"
              v-model="reportForm.site"
              label="Site"
              :items="siteOptions"
              density="comfortable"
              variant="outlined"
              clearable
            ></v-select>
          </v-col>
        </v-row>

        <v-card variant="outlined" class="pa-4">
          <v-card-title class="text-subtitle-1 mb-4">Période du rapport</v-card-title>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="reportForm.startDate"
                label="Date de début"
                type="date"
                density="comfortable"
                variant="outlined"
                :rules="[rules.required]"
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="reportForm.endDate"
                label="Date de fin"
                type="date"
                density="comfortable"
                variant="outlined"
                :rules="[rules.required, dateRangeRule]"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card>
      </DashboardForm>
    </template>
  </DashboardView>

  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    timeout="3000"
  >
    {{ snackbar.text }}
  </v-snackbar>

  <!-- Dialog de confirmation -->
  <v-dialog v-model="showDeleteConfirmDialog" max-width="400" persistent>
    <v-card>
      <!-- Dialog content -->
    </v-card>
  </v-dialog>

  <ConfirmDialog />
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue'
import { reportsApi, sitesApi } from '@/services/api'
import { useSitesStore } from '@/stores/sites'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'ReportsView',
  components: {
    DashboardFilters,
    DashboardView,
    DashboardForm,
    ConfirmDialog
  },
  props: {
    siteId: {
      type: Number,
      default: null
    }
  },
  setup(props) {
    const sitesStore = useSitesStore()
    const form = ref(null)
    const loading = ref(true)
    const generating = ref(false)
    const dashboardView = ref(null)
    const formErrors = ref({})
    
    // Computed pour le site courant - priorité au siteId passé en prop
    const currentSiteId = computed(() => props.siteId || sitesStore.getCurrentSiteId)
    
    const headers = ref([
      { title: 'Site', align: 'start', key: 'site_name' },
      { title: 'Type', align: 'start', key: 'report_type_display' },
      { title: 'Format', align: 'center', key: 'report_format_display' },
      { title: 'Période', align: 'start', key: 'period' },
      { title: 'Créé par', align: 'start', key: 'created_by_name' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    const reportTypeOptions = ref([
      { title: 'Journalier', value: 'DAILY' },
      { title: 'Hebdomadaire', value: 'WEEKLY' },
      { title: 'Mensuel', value: 'MONTHLY' },
    ])
    
    const reportFormatOptions = ref([
      { title: 'PDF', value: 'PDF' },
      { title: 'CSV', value: 'CSV' },
      { title: 'Excel', value: 'EXCEL' }
    ])
    
    const siteOptions = ref(['Tous les sites', 'Centre Commercial', 'Hôpital Nord', 'Résidence Les Pins'])
    const reports = ref([])
    const showDeleteConfirmDialog = ref(false)
    
    const reportForm = ref({
      name: '',
      type: 'MONTHLY',
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
    
    const filters = ref({
      search: '',
      type: '',
      format: ''
    })
    
    const rules = {
      required: v => !!v || 'Ce champ est requis'
    }
    
    const dateRangeRule = v => {
      if (!v || !reportForm.value.startDate) return true
      return new Date(v) >= new Date(reportForm.value.startDate) || 'La date de fin doit être postérieure à la date de début'
    }
    
    const openDialog = () => {
      reportForm.value = {
        name: '',
        type: 'MONTHLY',
        format: 'PDF',
        site: currentSiteId.value || '',
        startDate: '',
        endDate: ''
      }
      if (dashboardView.value) {
        dashboardView.value.showForm = true
      }
    }
    
    const formatReportData = (data) => {
      return data.map(report => ({
        ...report, // On garde toutes les données originales
        created_at: new Date(report.created_at).toLocaleDateString()
      }))
    }
    
    const loadReports = async () => {
      try {
        loading.value = true
        console.log('[Reports][Load] Chargement des rapports...')
        
        const params = {
          search: filters.value.search,
          type: filters.value.type,
          format: filters.value.format,
          site: currentSiteId.value
        }
        
        const response = await reportsApi.getAllReports(params)
        console.log('[Reports][API] Réponse:', response.data)
        
        reports.value = formatReportData(response.data.results)
      } catch (error) {
        console.error('[Reports][Error] Erreur lors du chargement:', error)
        showError('Erreur lors du chargement des rapports')
      } finally {
        loading.value = false
      }
    }
    
    const generateReport = async () => {
      if (!form.value) return
      
      const isValid = await form.value.validate()
      if (!isValid) return
      
      try {
        generating.value = true
        console.log('[Reports][Generate] Génération du rapport...')
        
        const response = await reportsApi.generateReport({
          name: reportForm.value.name,
          type: reportForm.value.type,
          format: reportForm.value.format,
          start_date: reportForm.value.startDate,
          end_date: reportForm.value.endDate,
          site: reportForm.value.site || null
        })
        
        console.log('[Reports][Generate] Rapport généré:', response.data)
        showSuccess('Rapport en cours de génération')
        await loadReports()
        
        if (dashboardView.value) {
          dashboardView.value.showForm = false
        }
      } catch (error) {
        console.error('[Reports][Error] Erreur lors de la génération:', error)
        showError(error.response?.data?.error || 'Erreur lors de la génération du rapport')
      } finally {
        generating.value = false
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
    
    // Charger les sites
    const loadSites = async () => {
      try {
        const response = await sitesApi.getAllSites()
        if (response.data?.results) {
          siteOptions.value = [
            { title: 'Tous les sites', value: null },
            ...response.data.results.map(site => ({
              title: site.name,
              value: site.id
            }))
          ]
        }
      } catch (error) {
        console.error('Erreur lors du chargement des sites:', error)
        siteOptions.value = []
      }
    }

    const applyFilters = async () => {
      try {
        loading.value = true
        const siteId = sitesStore.getCurrentSiteId || reportForm.value.site
        if (siteId) {
          const response = await reportsApi.getReportsBySite(siteId)
          reports.value = response.data?.results || []
        }
      } catch (error) {
        console.error('Erreur lors du chargement des rapports:', error)
        reports.value = []
      } finally {
        loading.value = false
      }
    }

    const resetFilters = () => {
      filters.value = {
        search: '',
        type: '',
        format: ''
      }
      applyFilters()
    }

    // Watch for changes in current site
    watch(() => sitesStore.getCurrentSiteId, (newSiteId) => {
      if (newSiteId) {
        reportForm.value.site = newSiteId
        loadReports()
      }
    })

    onMounted(async () => {
      await loadSites()
      if (sitesStore.getCurrentSiteId) {
        reportForm.value.site = sitesStore.getCurrentSiteId
      }
      await loadReports()
    })
    
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
      deleteReport,
      loadReports,
      currentSiteId,
      showDeleteConfirmDialog,
      filters,
      applyFilters,
      resetFilters,
      dashboardView,
      openDialog,
      formErrors
    }
  }
}
</script>

<style scoped>
/* Style des boutons dans le tableau */
:deep(.v-data-table .v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-data-table .v-btn--icon[color="primary"]) {
  color: #00346E !important;
}

:deep(.v-data-table .v-btn--icon[color="error"]) {
  color: #F78C48 !important;
}

:deep(.v-data-table .v-btn--icon[color="warning"]) {
  color: #FB8C00 !important;
}

:deep(.v-data-table .v-btn--icon[color="grey"]) {
  color: #999999 !important;
  opacity: 0.5 !important;
  cursor: default !important;
  pointer-events: none !important;
}

/* Assurer que les icônes dans les boutons sont visibles */
:deep(.v-data-table .v-btn--icon .v-icon) {
  opacity: 1 !important;
  color: inherit !important;
}

/* Style pour le formulaire */
.text-subtitle-1 {
  color: rgba(0, 0, 0, 0.87) !important;
  font-weight: 500 !important;
}

:deep(.v-card-title) {
  font-size: 1.1rem !important;
  font-weight: 500 !important;
  color: rgba(0, 0, 0, 0.87) !important;
}
</style>

