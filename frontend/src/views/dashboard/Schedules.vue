<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Plannings</h1>
      <v-btn color="#00346E" prepend-icon="mdi-plus" @click="showScheduleDialog = true">
        Ajouter un planning
      </v-btn>
    </div>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="schedules"
        :loading="loading"
        :items-per-page="10"
        :no-data-text="'Aucun planning trouvé'"
        :loading-text="'Chargement des plannings...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        class="elevation-1"
        @update:options="loadSchedules"
        fixed-header
        height="calc(100vh - 250px)"
      >
        <template #item.type="{ item }">
          <v-chip
            :color="item?.raw?.schedule_type === 'FIXED' ? 'primary' : 'secondary'"
            size="small"
          >
            {{ item?.raw?.schedule_type === 'FIXED' ? 'Fixe (gardien)' : 'Fréquence (nettoyage)' }}
          </v-chip>
        </template>

        <template #item.minDailyHours="{ item }">
          {{ item.raw.minDailyHours }}
        </template>

        <template #item.minWeeklyHours="{ item }">
          {{ item.raw.minWeeklyHours }}
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex justify-end gap-2">
            <v-btn
              icon="mdi-eye"
              variant="text"
              size="small"
              color="primary"
              :to="`/dashboard/schedules/${item.raw.id}`"
              :title="'Voir les détails'"
            />
            <v-btn
              icon="mdi-pencil"
              variant="text"
              size="small"
              color="warning"
              @click="editSchedule(item.raw)"
              :title="'Modifier'"
            />
            <v-btn
              icon="mdi-delete"
              variant="text"
              size="small"
              color="error"
              @click="confirmDelete(item.raw)"
              :title="'Supprimer'"
            />
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer ce planning ? Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn color="#F78C48" @click="deleteSchedule" :loading="deleting">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog pour créer/modifier un planning -->
    <v-dialog v-model="showScheduleDialog" max-width="800px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>{{ editingSchedule ? 'Modifier le planning' : 'Créer un nouveau planning' }}</v-card-title>
        <v-card-text>
          <v-form ref="scheduleForm" @submit.prevent="saveSchedule">
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="formData.site"
                  label="Site"
                  :items="sites"
                  item-title="name"
                  item-value="id"
                  required
                  :rules="[v => !!v || 'Le site est requis']"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="formData.schedule_type"
                  label="Type de planning"
                  :items="[
                    { title: 'Fixe (gardien)', value: 'FIXED' },
                    { title: 'Fréquence (nettoyage)', value: 'FREQUENCY' }
                  ]"
                  required
                ></v-select>
              </v-col>
              
              <template v-if="formData.schedule_type === 'FIXED'">
                <v-col cols="12">
                  <v-divider class="my-4">Configuration des jours et horaires</v-divider>
                </v-col>
                
                <!-- Sélection des jours de travail -->
                <v-col cols="12">
                  <v-select
                    v-model="formData.working_days"
                    label="Jours de travail"
                    :items="[
                      { title: 'Lundi', value: 1 },
                      { title: 'Mardi', value: 2 },
                      { title: 'Mercredi', value: 3 },
                      { title: 'Jeudi', value: 4 },
                      { title: 'Vendredi', value: 5 },
                      { title: 'Samedi', value: 6 },
                      { title: 'Dimanche', value: 7 }
                    ]"
                    multiple
                    chips
                    required
                    :rules="[v => v.length > 0 || 'Sélectionnez au moins un jour']"
                  ></v-select>
                </v-col>

                <!-- Configuration des horaires pour chaque jour -->
                <v-col cols="12" v-for="day in formData.working_days" :key="day">
                  <v-card class="pa-3">
                    <div class="text-h6 mb-2">{{ ['', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][day] }}</div>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).morning_start"
                          label="Début matin"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de début est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).morning_end"
                          label="Fin matin"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de fin est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).afternoon_start"
                          label="Début après-midi"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de début est requise']"
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6">
                        <v-text-field
                          v-model="getScheduleForDay(day).afternoon_end"
                          label="Fin après-midi"
                          type="time"
                          required
                          :rules="[v => !!v || 'L\'heure de fin est requise']"
                        ></v-text-field>
                      </v-col>
                    </v-row>
                  </v-card>
                </v-col>
              </template>
              
              <template v-if="formData.schedule_type === 'FREQUENCY'">
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.min_daily_hours"
                    label="Heures min. quotidiennes"
                    type="number"
                    required
                    :rules="[v => !!v || 'Les heures quotidiennes sont requises']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.min_weekly_hours"
                    label="Heures min. hebdomadaires"
                    type="number"
                    required
                    :rules="[v => !!v || 'Les heures hebdomadaires sont requises']"
                  ></v-text-field>
                </v-col>
              </template>
              
              <v-col cols="12">
                <v-divider class="my-4">Paramètres de flexibilité</v-divider>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-switch
                  v-model="formData.allow_early_arrival"
                  label="Autoriser l'arrivée en avance"
                  color="primary"
                  :hint="'Permet à l\'employé de pointer avant son heure de début prévue'"
                  persistent-hint
                ></v-switch>
              </v-col>
              <v-col cols="12" md="6">
                <v-switch
                  v-model="formData.allow_late_departure"
                  label="Autoriser le départ tardif"
                  color="primary"
                  :hint="'Permet à l\'employé de pointer après son heure de fin prévue'"
                  persistent-hint
                ></v-switch>
              </v-col>
              
              <v-col cols="12" md="6" v-if="formData.allow_early_arrival">
                <v-text-field
                  v-model="formData.early_arrival_limit"
                  label="Limite d'arrivée en avance (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La limite d\'arrivée en avance est requise']"
                  :hint="'Nombre de minutes maximum avant l\'heure prévue où l\'employé peut pointer'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6" v-if="formData.allow_late_departure">
                <v-text-field
                  v-model="formData.late_departure_limit"
                  label="Limite de départ tardif (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La limite de départ tardif est requise']"
                  :hint="'Nombre de minutes maximum après l\'heure prévue où l\'employé peut pointer'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              
              <v-col cols="12">
                <v-divider class="my-4">Paramètres de pause</v-divider>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="formData.break_duration"
                  label="Durée de pause (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La durée de pause est requise']"
                  :hint="'Durée obligatoire de la pause en minutes (ex: 60 pour 1h de pause déjeuner)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="formData.min_break_start"
                  label="Début pause au plus tôt"
                  type="time"
                  :rules="[v => !v || /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(v) || 'Format invalide (HH:MM)']"
                  :hint="'Heure la plus tôt à laquelle la pause peut commencer (ex: 11:30)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="formData.max_break_end"
                  label="Fin pause au plus tard"
                  type="time"
                  :rules="[v => !v || /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(v) || 'Format invalide (HH:MM)']"
                  :hint="'Heure la plus tard à laquelle la pause doit se terminer (ex: 14:00)'"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="#00346E" @click="saveSchedule" :loading="saving">
            {{ editingSchedule ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { sitesApi } from '@/services/api'

export default {
  name: 'SchedulesView',
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const deleting = ref(false)
    const saving = ref(false)
    const showDeleteDialog = ref(false)
    const showScheduleDialog = ref(false)
    const scheduleToDelete = ref(null)
    const scheduleForm = ref(null)
    const editingSchedule = ref(null)
    const sites = ref([])
    
    const headers = ref([
      { title: 'Site', align: 'start', key: 'site', width: '25%' },
      { title: 'Type', align: 'center', key: 'type', width: '20%' },
      { title: 'Heures min. quotidiennes', align: 'center', key: 'minDailyHours', width: '20%' },
      { title: 'Heures min. hebdomadaires', align: 'center', key: 'minWeeklyHours', width: '20%' },
      { title: 'Employés assignés', align: 'center', key: 'employeesCount', width: '10%' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false, width: '150px' }
    ])
    
    const schedules = ref([])
    const pagination = ref({
      page: 1,
      itemsPerPage: 10,
      pageCount: 0,
      itemsLength: 0
    })

    const formData = ref({
      site: null,
      schedule_type: 'FIXED',
      working_days: [],
      min_daily_hours: null,
      min_weekly_hours: null,
      allow_early_arrival: false,
      allow_late_departure: false,
      early_arrival_limit: null,
      late_departure_limit: null,
      break_duration: 60,
      min_break_start: null,
      max_break_end: null,
      schedules: {}
    })

    const loadSites = async () => {
      try {
        const response = await sitesApi.getAllSites()
        sites.value = response.data.results
      } catch (error) {
        console.error('Erreur lors du chargement des sites:', error)
      }
    }

    const loadSchedules = async (options) => {
      try {
        loading.value = true
        const page = options?.page || 1
        const perPage = options?.itemsPerPage || 10

        // Récupérer tous les sites avec leurs plannings
        const response = await sitesApi.getAllSites(page, perPage)
        const sites = response.data.results || []
        
        console.log('Sites reçus:', sites)

        // Extraire et formater tous les plannings de tous les sites
        const allSchedules = []
        sites.forEach(site => {
          const schedules = site.schedules || []
          schedules.forEach(schedule => {
            if (schedule) {  // Vérifier que le planning existe
              allSchedules.push({
                id: schedule.id,
                site: site.name || '',
                siteId: site.id,
                schedule_type: schedule.schedule_type || 'FIXED',
                type: schedule.schedule_type === 'FIXED' ? 'Fixe (gardien)' : 'Fréquence (nettoyage)',
                minDailyHours: schedule.min_daily_hours ? `${schedule.min_daily_hours}h` : '-',
                minWeeklyHours: schedule.min_weekly_hours ? `${schedule.min_weekly_hours}h` : '-',
                employeesCount: schedule.employees_count || 0,
                working_days: schedule.working_days || [],
                schedules: schedule.schedules || {},
                allow_early_arrival: schedule.allow_early_arrival || false,
                allow_late_departure: schedule.allow_late_departure || false,
                early_arrival_limit: schedule.early_arrival_limit || 30,
                late_departure_limit: schedule.late_departure_limit || 30,
                break_duration: schedule.break_duration || 60,
                min_break_start: schedule.min_break_start || null,
                max_break_end: schedule.max_break_end || null,
                raw: schedule  // Ajouter l'objet brut pour accès direct
              })
            }
          })
        })

        console.log('Plannings extraits:', allSchedules)

        schedules.value = allSchedules
        pagination.value = {
          page: page,
          itemsPerPage: perPage,
          pageCount: Math.ceil(allSchedules.length / perPage),
          itemsLength: allSchedules.length
        }
      } catch (error) {
        console.error('Erreur lors du chargement des plannings:', error)
      } finally {
        loading.value = false
      }
    }

    const createSchedule = () => {
      editingSchedule.value = null
      resetScheduleForm()
      showScheduleDialog.value = true
    }

    const editSchedule = (schedule) => {
      editingSchedule.value = true
      formData.value = {
        site: schedule.site_id,
        schedule_type: schedule.type,
        working_days: schedule.working_days || [],
        min_daily_hours: schedule.min_daily_hours,
        min_weekly_hours: schedule.min_weekly_hours,
        allow_early_arrival: schedule.allow_early_arrival,
        allow_late_departure: schedule.allow_late_departure,
        early_arrival_limit: schedule.early_arrival_limit,
        late_departure_limit: schedule.late_departure_limit,
        break_duration: schedule.break_duration,
        min_break_start: schedule.min_break_start,
        max_break_end: schedule.max_break_end,
        schedules: schedule.schedules || {}
      }
      showScheduleDialog.value = true
    }

    const confirmDelete = (schedule) => {
      scheduleToDelete.value = schedule
      showDeleteDialog.value = true
    }

    const deleteSchedule = async () => {
      if (!scheduleToDelete.value) return

      try {
        deleting.value = true
        await sitesApi.deleteSchedule(scheduleToDelete.value.siteId, scheduleToDelete.value.id)
        await loadSchedules(pagination.value)
        showDeleteDialog.value = false
        scheduleToDelete.value = null
      } catch (error) {
        console.error('Erreur lors de la suppression du planning:', error)
      } finally {
        deleting.value = false
      }
    }

    const saveSchedule = async () => {
      const { valid } = await scheduleForm.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const scheduleData = {
          site: formData.value.site,
          type: formData.value.schedule_type,
          working_days: formData.value.working_days,
          min_daily_hours: formData.value.min_daily_hours,
          min_weekly_hours: formData.value.min_weekly_hours,
          allow_early_arrival: formData.value.allow_early_arrival,
          allow_late_departure: formData.value.allow_late_departure,
          early_arrival_limit: formData.value.early_arrival_limit,
          late_departure_limit: formData.value.late_departure_limit,
          break_duration: formData.value.break_duration,
          min_break_start: formData.value.min_break_start,
          max_break_end: formData.value.max_break_end,
          schedules: formData.value.schedules
        }

        if (editingSchedule.value) {
          await sitesApi.updateSchedule(formData.value.site, editingSchedule.value, scheduleData)
        } else {
          await sitesApi.createSchedule(formData.value.site, scheduleData)
        }

        showScheduleDialog.value = false
        resetScheduleForm()
        await loadSchedules()
      } catch (error) {
        console.error('Error saving schedule:', error)
      } finally {
        saving.value = false
      }
    }

    const closeDialog = () => {
      showScheduleDialog.value = false
      showDeleteDialog.value = false
      resetScheduleForm()
    }

    const onDialogClose = (val) => {
      if (!val) {
        resetScheduleForm()
      }
    }

    const resetScheduleForm = () => {
      formData.value = {
        site: null,
        schedule_type: 'FIXED',
        working_days: [],
        min_daily_hours: null,
        min_weekly_hours: null,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: null,
        late_departure_limit: null,
        break_duration: 60,
        min_break_start: null,
        max_break_end: null,
        schedules: {}
      }
    }

    const getScheduleForDay = (day) => {
      if (!formData.value.schedules[day]) {
        formData.value.schedules[day] = {
          morning_start: '',
          morning_end: '',
          afternoon_start: '',
          afternoon_end: ''
        }
      }
      return formData.value.schedules[day]
    }

    onMounted(() => {
      loadSchedules()
      loadSites()
    })
    
    return {
      loading,
      deleting,
      saving,
      headers,
      schedules,
      sites,
      showDeleteDialog,
      showScheduleDialog,
      scheduleForm,
      formData,
      editingSchedule,
      loadSchedules,
      createSchedule,
      editSchedule,
      confirmDelete,
      deleteSchedule,
      saveSchedule,
      closeDialog,
      onDialogClose,
      getScheduleForDay
    }
  }
}
</script>

