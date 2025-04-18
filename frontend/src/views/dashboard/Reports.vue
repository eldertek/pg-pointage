<template>
  <DashboardView
    ref="dashboardView"
    :title="$t('reports.title')"
    :form-title="$t('reports.generateReport')"
    :saving="generating"
    @save="generateReport"
  >
    <!-- Statistiques -->
    <v-card class="mb-4">
      <v-card-title>{{ $t('dashboard.statistiques_des_rapports') }}</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" sm="4">
            <div class="text-h4">{{ totalReports }}</div>
            <div class="text-subtitle-1">{{ $t('dashboard.rapports_gnrs') }}</div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="text-h4">{{ pendingReports }}</div>
            <div class="text-subtitle-1">{{ $t('timesheets.statuses.PENDING') }}</div>
          </v-col>
          <v-col cols="12" sm="4">
            <div class="text-h4">{{ completedReports }}</div>
            <div class="text-subtitle-1">{{ $t('dashboard.complts') }}</div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Actions -->
    <template #actions>
      <v-btn
        color="primary"
        prepend-icon="mdi-file-plus"
        @click="openDialog()"
      >
        {{ $t('reports.generateReport') }}
      </v-btn>
    </template>

    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="filters.search"
            :label="$t('common.search')"
            variant="outlined"
            prepend-inner-icon="mdi-magnify"
            clearable
            @update:model-value="applyFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.type"
            :label="$t('reports.reportType')"
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
            :label="$t('dashboard.format')"
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
      :no-data-text="$t('dashboard.aucun_rapport_trouv')"
      :loading-text="$t('dashboard.chargement_des_rapports')"
      :items-per-page-text="$t('dashboard.lignes_par_page')"
      :page-text="$t('dashboard.01_sur_2')"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: $t('common.all'), value: -1 }
      ]"
      class="elevation-1"
    >
      <template #item.actions="{ item }">
        <v-btn
          v-tooltip="$t('dashboard.tlcharger')"
          icon
          variant="text"
          size="small"
          color="primary"
          @click="downloadReport(item.id)"
        >
          <v-icon>mdi-download</v-icon>
        </v-btn>
        <v-btn
          v-tooltip="$t('common.delete')"
          icon
          variant="text"
          size="small"
          color="error"
          @click="deleteReport(item.id)"
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
              :label="$t('dashboard.nom_du_rapport')"
              density="comfortable"
              variant="outlined"
              :rules="[rules.required]"
            ></v-text-field>
          </v-col>

          <v-col cols="12" sm="6">
            <v-select
              v-model="reportForm.type"
              :label="$t('reports.reportType')"
              :items="reportTypeOptions"
              density="comfortable"
              variant="outlined"
              :rules="[rules.required]"
            ></v-select>
          </v-col>

          <v-col cols="12" sm="6">
            <v-select
              v-model="reportForm.format"
              :label="$t('dashboard.format_de_rapport')"
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
              :label="$t('timesheets.site')"
              :items="siteOptions"
              density="comfortable"
              variant="outlined"
              clearable
            ></v-select>
          </v-col>
        </v-row>

        <v-card variant="outlined" class="pa-4">
          <v-card-title class="text-subtitle-1 mb-4">{{ $t('dashboard.priode_du_rapport') }}</v-card-title>
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="reportForm.startDate"
                :label="$t('reports.startDate')"
                type="date"
                density="comfortable"
                variant="outlined"
                :rules="[rules.required]"
              ></v-text-field>
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="reportForm.endDate"
                :label="$t('reports.endDate')"
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
import { useI18n } from 'vue-i18n'
import { ref, watch, onMounted, computed } from 'vue'
import { reportsApi, sitesApi } from '@/services/api'
import { useSitesStore } from '@/stores/sites'
import { useConfirmDialog } from '@/utils/dialogs'
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
    const { dialogState, handleConfirm } = useConfirmDialog()

    // Computed pour le site courant - priorité au siteId passé en prop
    const currentSiteId = computed(() => props.siteId || sitesStore.getCurrentSiteId)

    const { t } = useI18n()

    const headers = ref([
      { title: t('common.site'), align: 'start', key: 'site_name' },
      { title: t('common.type'), align: 'start', key: 'report_type_display' },
      { title: t('dashboard.format'), align: 'center', key: 'report_format_display' },
      { title: t('reports.period'), align: 'start', key: 'period' },
      { title: t('reports.createdBy'), align: 'start', key: 'created_by_name' },
      { title: t('common.actions'), align: 'end', key: 'actions', sortable: false }
    ])

    const reportTypeOptions = ref([
      { title: t('reports.types.DAILY'), value: 'DAILY' },
      { title: t('reports.types.WEEKLY'), value: 'WEEKLY' },
      { title: t('reports.types.MONTHLY'), value: 'MONTHLY' },
    ])

    const reportFormatOptions = ref([
      { title: t('reports.formats.PDF'), value: 'PDF' },
      { title: t('reports.formats.CSV'), value: 'CSV' },
      { title: t('reports.formats.EXCEL'), value: 'EXCEL' }
    ])

    const siteOptions = ref([t('reports.allSites')])
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
      required: v => !!v || t('common.fieldRequired')
    }

    const dateRangeRule = v => {
      if (!v || !reportForm.value.startDate) return true
      return new Date(v) >= new Date(reportForm.value.startDate) || t('reports.endDateAfterStartDate')
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
        ...report, // Keep all original data
        created_at: new Date(report.created_at).toLocaleDateString()
      }))
    }

    const loadReports = async () => {
      try {
        loading.value = true
        console.log('[Reports][Load] Loading reports...')

        const params = {
          search: filters.value.search,
          type: filters.value.type,
          format: filters.value.format,
          site: currentSiteId.value
        }

        const response = await reportsApi.getAllReports(params)
        console.log('[Reports][API] Response:', response.data)

        reports.value = formatReportData(response.data.results)
      } catch (error) {
        console.error('[Reports][Error] Error loading reports:', error)
        showError(t('profile.fetchError') + ' ' + t('reports.title'))
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
        console.log('[Reports][Generate] Generating report...')

        const response = await reportsApi.generateReport({
          name: reportForm.value.name,
          type: reportForm.value.type,
          format: reportForm.value.format,
          start_date: reportForm.value.startDate,
          end_date: reportForm.value.endDate,
          site: reportForm.value.site || null
        })

        console.log('[Reports][Generate] Report generated:', response.data)
        showSuccess(t('reports.reportGenerated'))
        await loadReports()

        if (dashboardView.value) {
          dashboardView.value.showForm = false
        }
      } catch (error) {
        console.error('[Reports][Error] Error generating report:', error)
        showError(error.response?.data?.error || t('profile.generationError') + ' ' + t('reports.title'))
      } finally {
        generating.value = false
      }
    }

    const downloadReport = (id) => {
      // Download simulation
      console.log(`Downloading report ${id}`)
      showSuccess(t('profile.downloadStarted'))
    }

    const confirmDelete = (id) => {
      dialogState.value = {
        show: true,
        title: t('common.delete') + ' ' + t('reports.title').toLowerCase(),
        message: t('common.deleteConfirmation') + ' ' + t('reports.title').toLowerCase() + '? ' + t('common.cette_action_est_irrversible'),
        confirmText: t('common.delete'),
        cancelText: t('common.cancel'),
        confirmColor: 'error',
        loading: false,
        onConfirm: async () => {
          try {
            dialogState.value.loading = true
            await reportsApi.deleteReport(id)
            await loadReports()
            showSuccess(t('reports.title') + ' ' + t('profile.reportDeleted'))
          } catch (error) {
            console.error('Error deleting report:', error)
            showError(error.response?.data?.error || t('profile.deleteError') + ' ' + t('reports.title'))
          } finally {
            dialogState.value.loading = false
            dialogState.value.show = false
          }
        }
      }
    }

    const deleteReport = async (id) => {
      confirmDelete(id)
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
            { title: t('reports.allSites'), value: null },
            ...response.data.results.map(site => ({
              title: site.name,
              value: site.id
            }))
          ]
        }
      } catch (error) {
        console.error('Error loading sites:', error)
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
        console.error('Error loading reports:', error)
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

    const totalReports = ref(0)
    const pendingReports = ref(0)
    const completedReports = ref(0)

    const loadReportStatistics = async () => {
      try {
        const response = await reportsApi.getAllReports()
        const reports = response.data?.results || []

        totalReports.value = reports.length
        pendingReports.value = reports.filter(r => r.status === 'PENDING').length
        completedReports.value = reports.filter(r => r.status === 'COMPLETED').length
      } catch (error) {
        console.error('Error loading statistics:', error)
      }
    }

    // Charger les statistiques initiales
    loadReportStatistics()

    // Recharger périodiquement (toutes les 5 minutes)
    setInterval(loadReportStatistics, 5 * 60 * 1000)

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
      formErrors,
      totalReports,
      pendingReports,
      completedReports,
      dialogState,
      handleConfirm
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

