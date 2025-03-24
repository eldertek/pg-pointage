<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center">
        <v-btn icon="mdi-arrow-left" variant="text" :to="'/dashboard/schedules'" class="mr-4"></v-btn>
        <h1 class="text-h4">{{ schedule?.name || 'Détails du planning' }}</h1>
      </div>
      <div class="d-flex">
        <v-btn
          color="#00346E"
          prepend-icon="mdi-pencil"
          class="mr-2"
          @click="editSchedule"
          :disabled="loading"
        >
          Modifier
        </v-btn>
        <v-btn
          color="#F78C48"
          prepend-icon="mdi-delete"
          @click="confirmDelete"
          :disabled="loading"
        >
          Supprimer
        </v-btn>
      </div>
    </div>
    
    <v-card v-if="loading" class="pa-4">
      <div class="d-flex justify-center">
        <v-progress-circular indeterminate color="#00346E"></v-progress-circular>
      </div>
    </v-card>

    <template v-else-if="schedule">
          <v-card class="mb-4">
            <v-card-title>Informations générales</v-card-title>
            <v-card-text>
          <v-row>
            <v-col cols="12" sm="6" md="4">
              <strong>Site :</strong> {{ schedule.site?.name || '-' }}
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <strong>Type :</strong> {{ schedule.schedule_type === 'FIXED' ? 'Fixe (gardien)' : 'Fréquence (nettoyage)' }}
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <strong>Heures min. quotidiennes :</strong> {{ schedule.min_daily_hours ? `${schedule.min_daily_hours}h` : '-' }}
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <strong>Heures min. hebdomadaires :</strong> {{ schedule.min_weekly_hours ? `${schedule.min_weekly_hours}h` : '-' }}
            </v-col>
          </v-row>
            </v-card-text>
          </v-card>
        
          <v-card class="mb-4">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Employés assignés</span>
          <v-btn
            color="#00346E"
            prepend-icon="mdi-account-plus"
            @click="showAssignDialog = true"
            size="small"
          >
            Assigner un employé
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="employeeHeaders"
            :items="employees"
            :loading="loadingEmployees"
            :no-data-text="'Aucun employé assigné'"
            :loading-text="'Chargement des employés...'"
          >
            <template #item.actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                color="#F78C48"
                @click="unassignEmployee(item.raw)"
              >
                <v-icon>mdi-account-remove</v-icon>
                  </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
      
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Détails du planning</span>
          <v-btn
            color="#00346E"
            prepend-icon="mdi-plus"
            @click="showDetailDialog = true"
            size="small"
          >
            Ajouter un détail
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="detailHeaders"
            :items="details"
            :loading="loadingDetails"
            :no-data-text="'Aucun détail trouvé'"
            :loading-text="'Chargement des détails...'"
          >
            <template #item.actions="{ item }">
              <v-btn
                icon
                variant="text"
                size="small"
                color="#00346E"
                @click="editDetail(item.raw)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                color="#F78C48"
                @click="confirmDeleteDetail(item.raw)"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </template>

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

    <!-- Dialog de confirmation de suppression de détail -->
    <v-dialog v-model="showDeleteDetailDialog" max-width="400">
      <v-card>
        <v-card-title>Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer ce détail ? Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDeleteDetailDialog = false">Annuler</v-btn>
          <v-btn color="#F78C48" @click="deleteDetail" :loading="deletingDetail">Supprimer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog d'assignation d'employé -->
    <v-dialog v-model="showAssignDialog" max-width="500">
      <v-card>
        <v-card-title>Assigner un employé</v-card-title>
        <v-card-text>
          <v-autocomplete
            v-model="selectedEmployee"
            :items="availableEmployees"
            item-title="name"
            item-value="id"
            label="Sélectionner un employé"
            :loading="loadingAvailableEmployees"
            :no-data-text="'Aucun employé disponible'"
          ></v-autocomplete>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showAssignDialog = false">Annuler</v-btn>
          <v-btn
            color="#00346E"
            @click="assignEmployee"
            :loading="assigning"
            :disabled="!selectedEmployee"
          >
            Assigner
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog d'ajout/modification de détail -->
    <v-dialog v-model="showDetailDialog" max-width="500">
      <v-card>
        <v-card-title>{{ editingDetail ? 'Modifier le détail' : 'Ajouter un détail' }}</v-card-title>
        <v-card-text>
          <v-form ref="detailForm" v-model="detailFormValid">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="detailForm.day"
                  label="Jour"
                  type="number"
                  min="1"
                  max="7"
                  :rules="[v => !!v || 'Le jour est requis', v => (v >= 1 && v <= 7) || 'Le jour doit être entre 1 et 7']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="detailForm.start_time"
                  label="Heure de début"
                  type="time"
                  :rules="[v => !!v || 'L\'heure de début est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="detailForm.end_time"
                  label="Heure de fin"
                  type="time"
                  :rules="[v => !!v || 'L\'heure de fin est requise']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDetailDialog = false">Annuler</v-btn>
          <v-btn
            color="#00346E"
            @click="saveDetail"
            :loading="savingDetail"
            :disabled="!detailFormValid"
          >
            {{ editingDetail ? 'Modifier' : 'Ajouter' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sitesApi } from '@/services/api'

export default {
  name: 'ScheduleDetailView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const scheduleId = route.params.id
    const siteId = ref(null)
    
    // États généraux
    const loading = ref(true)
    const deleting = ref(false)
    const schedule = ref(null)
    const showDeleteDialog = ref(false)
    
    // États pour les employés
    const loadingEmployees = ref(true)
    const employees = ref([])
    const employeeHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
    // États pour l'assignation d'employés
    const showAssignDialog = ref(false)
    const selectedEmployee = ref(null)
    const availableEmployees = ref([])
    const loadingAvailableEmployees = ref(false)
    const assigning = ref(false)

    // États pour les détails
    const loadingDetails = ref(true)
    const details = ref([])
    const detailHeaders = ref([
      { title: 'Jour', align: 'start', key: 'day' },
      { title: 'Heure de début', align: 'start', key: 'start_time' },
      { title: 'Heure de fin', align: 'start', key: 'end_time' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    // États pour la gestion des détails
    const showDetailDialog = ref(false)
    const showDeleteDetailDialog = ref(false)
    const detailForm = ref({
      day: '',
      start_time: '',
      end_time: ''
    })
    const detailFormValid = ref(false)
    const editingDetail = ref(null)
    const detailToDelete = ref(null)
    const savingDetail = ref(false)
    const deletingDetail = ref(false)

    // Chargement des données
    const loadSchedule = async () => {
      try {
        loading.value = true
        // Récupérer tous les sites pour trouver le planning
        const sitesResponse = await sitesApi.getAllSites()
        const sites = sitesResponse.data.results

        // Trouver le site qui contient le planning recherché
        let foundSchedule = null
        let foundSite = null

        for (const site of sites) {
          if (site.schedules) {
            const schedule = site.schedules.find(s => s.id === parseInt(scheduleId))
            if (schedule) {
              foundSchedule = schedule
              foundSite = site
              break
            }
          }
        }

        if (foundSchedule && foundSite) {
          siteId.value = foundSite.id
          schedule.value = {
            ...foundSchedule,
            site: foundSite
          }
        }
      } catch (error) {
        console.error('Erreur lors du chargement du planning:', error)
      } finally {
        loading.value = false
      }
    }
    
    const loadEmployees = async () => {
      if (!siteId.value) return

      try {
        loadingEmployees.value = true
        const response = await sitesApi.getScheduleEmployees(siteId.value, scheduleId)
        employees.value = response.data.map(employee => ({
          id: employee.id,
          name: `${employee.first_name} ${employee.last_name}`,
          email: employee.email,
          phone: employee.phone || '-'
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des employés:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    const loadDetails = async () => {
      if (!siteId.value) return

      try {
        loadingDetails.value = true
        const response = await sitesApi.getScheduleDetails(siteId.value, scheduleId)
        details.value = response.data.map(detail => ({
          id: detail.id,
          day: detail.day,
          start_time: detail.start_time,
          end_time: detail.end_time
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des détails:', error)
      } finally {
        loadingDetails.value = false
      }
    }

    // Actions sur le planning
    const editSchedule = () => {
      router.push(`/dashboard/schedules/${scheduleId}/edit`)
    }

    const confirmDelete = () => {
      showDeleteDialog.value = true
    }

    const deleteSchedule = async () => {
      if (!siteId.value) return

      try {
        deleting.value = true
        await sitesApi.deleteSchedule(siteId.value, scheduleId)
        router.push('/dashboard/schedules')
      } catch (error) {
        console.error('Erreur lors de la suppression du planning:', error)
      } finally {
        deleting.value = false
        showDeleteDialog.value = false
      }
    }

    // Actions sur les employés
    const unassignEmployee = async (employee) => {
      if (!siteId.value) return

      try {
        await sitesApi.unassignEmployee(siteId.value, employee.id)
        await loadEmployees()
      } catch (error) {
        console.error('Erreur lors de la désassignation de l\'employé:', error)
      }
    }

    const assignEmployee = async () => {
      if (!selectedEmployee.value || !siteId.value) return

      try {
        assigning.value = true
        await sitesApi.assignEmployee(siteId.value, {
          employee: selectedEmployee.value,
          schedule: scheduleId
        })
        await loadEmployees()
        showAssignDialog.value = false
        selectedEmployee.value = null
      } catch (error) {
        console.error('Erreur lors de l\'assignation de l\'employé:', error)
      } finally {
        assigning.value = false
      }
    }

    // Actions sur les détails
    const editDetail = (detail) => {
      editingDetail.value = detail
      detailForm.value = {
        day: detail.day,
        start_time: detail.start_time,
        end_time: detail.end_time
      }
      showDetailDialog.value = true
    }

    const confirmDeleteDetail = (detail) => {
      detailToDelete.value = detail
      showDeleteDetailDialog.value = true
    }

    const deleteDetail = async () => {
      if (!detailToDelete.value || !siteId.value) return

      try {
        deletingDetail.value = true
        await sitesApi.deleteScheduleDetail(siteId.value, scheduleId, detailToDelete.value.id)
        await loadDetails()
        showDeleteDetailDialog.value = false
        detailToDelete.value = null
      } catch (error) {
        console.error('Erreur lors de la suppression du détail:', error)
      } finally {
        deletingDetail.value = false
      }
    }

    const saveDetail = async () => {
      if (!siteId.value) return

      try {
        savingDetail.value = true
        if (editingDetail.value) {
          await sitesApi.updateScheduleDetail(siteId.value, scheduleId, editingDetail.value.id, detailForm.value)
        } else {
          await sitesApi.createScheduleDetail(siteId.value, scheduleId, detailForm.value)
        }
        await loadDetails()
        showDetailDialog.value = false
        editingDetail.value = null
        detailForm.value = {
          day: '',
          start_time: '',
          end_time: ''
        }
      } catch (error) {
        console.error('Erreur lors de la sauvegarde du détail:', error)
      } finally {
        savingDetail.value = false
      }
    }

    onMounted(() => {
      loadSchedule().then(() => {
        if (siteId.value) {
          loadEmployees()
          loadDetails()
        }
      })
    })
    
    return {
      // États généraux
      loading,
      deleting,
      schedule,
      showDeleteDialog,

      // États des employés
      loadingEmployees,
      employees,
      employeeHeaders,
      showAssignDialog,
      selectedEmployee,
      availableEmployees,
      loadingAvailableEmployees,
      assigning,

      // États des détails
      loadingDetails,
      details,
      detailHeaders,
      showDetailDialog,
      showDeleteDetailDialog,
      detailForm,
      detailFormValid,
      editingDetail,
      savingDetail,
      deletingDetail,

      // Actions
      editSchedule,
      confirmDelete,
      deleteSchedule,
      unassignEmployee,
      assignEmployee,
      editDetail,
      confirmDeleteDetail,
      deleteDetail,
      saveDetail
    }
  }
}
</script>

