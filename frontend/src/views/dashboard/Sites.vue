<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Sites</h1>
      <v-btn color="#00346E" prepend-icon="mdi-plus" @click="showCreateDialog = true">
        Ajouter un site
      </v-btn>
    </div>
    
    <!-- Vue principale des sites -->
    <template v-if="!selectedSite">
      <v-card>
        <v-data-table
          :headers="headers"
          :items="sites"
          :loading="loading"
          :items-per-page="itemsPerPage"
          :total-items="totalSites"
          :page.sync="currentPage"
          :no-data-text="'Aucun site trouvé'"
          :loading-text="'Chargement des sites...'"
          :items-per-page-text="'Lignes par page'"
          :page-text="'{0}-{1} sur {2}'"
          :items-per-page-options="itemsPerPageOptions"
          class="elevation-1"
          @update:options="handleTableUpdate"
        >
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon
              variant="text"
              size="small"
              @click="viewSiteDetails(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              color="#00346E"
              @click="editSite(item)"
            >
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              color="#F78C48"
              @click="deleteSite(item.id)"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card>
    </template>

    <!-- Vue détaillée d'un site -->
    <template v-else>
      <div class="d-flex align-center mb-4">
        <v-btn icon="mdi-arrow-left" variant="text" @click="selectedSite = null" class="mr-4"></v-btn>
        <h2 class="text-h5">{{ selectedSite.name }}</h2>
      </div>

      <v-card>
        <v-tabs v-model="activeTab" color="#00346E">
          <v-tab value="details">Informations</v-tab>
          <v-tab value="schedules">Plannings</v-tab>
          <v-tab value="employees">Employés</v-tab>
        </v-tabs>

        <v-card-text>
          <!-- Onglet Informations -->
          <v-window v-model="activeTab">
            <v-window-item value="details">
              <v-row>
                <v-col cols="12" md="6">
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-map-marker</v-icon>
                      </template>
                      <v-list-item-title>Adresse</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.address }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-nfc</v-icon>
                      </template>
                      <v-list-item-title>ID NFC</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.nfcId }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-domain</v-icon>
                      </template>
                      <v-list-item-title>Organisation</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.organization }}</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
                <v-col cols="12" md="6">
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-alert</v-icon>
                      </template>
                      <v-list-item-title>Marge de retard</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.lateMargin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-check</v-icon>
                      </template>
                      <v-list-item-title>Marge de départ anticipé</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.earlyDepartureMargin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-email-alert</v-icon>
                      </template>
                      <v-list-item-title>Emails pour les alertes</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.alertEmails }}</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- Onglet Plannings -->
            <v-window-item value="schedules">
              <div class="d-flex justify-space-between align-center mb-4">
                <div></div>
                <v-btn color="#00346E" prepend-icon="mdi-plus" @click="showScheduleDialog = true">
                  Ajouter un planning
                </v-btn>
              </div>
              <v-data-table
                :headers="scheduleHeaders"
                :items="selectedSite.schedules || []"
                :loading="loadingSchedules"
                :no-data-text="'Aucun planning trouvé'"
              >
                <template #[`item.type`]="{ item }">
                  <v-chip
                    :color="item.schedule_type === 'FIXED' ? '#00346E' : '#F78C48'"
                    size="small"
                  >
                    {{ item.schedule_type === 'FIXED' ? 'Fixe (gardien)' : 'Fréquence (nettoyage)' }}
                  </v-chip>
                </template>
                <template #[`item.actions`]="{ item }">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    @click="viewScheduleDetails(item)"
                  >
                    <v-icon>mdi-eye</v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="#00346E"
                    @click="editSchedule(item)"
                  >
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="#F78C48"
                    @click="deleteSchedule(item)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-data-table>
            </v-window-item>

            <!-- Onglet Employés -->
            <v-window-item value="employees">
              <div class="d-flex justify-space-between align-center mb-4">
                <div></div>
                <v-btn color="#00346E" prepend-icon="mdi-plus" @click="showEmployeeDialog = true">
                  Assigner un employé
                </v-btn>
              </div>
              <v-data-table
                :headers="employeeHeaders"
                :items="siteEmployees"
                :loading="loadingEmployees"
                :no-data-text="'Aucun employé trouvé'"
              >
                <template #[`item.status`]="{ item }">
                  <v-chip
                    :color="item.is_active ? 'success' : 'error'"
                    size="small"
                  >
                    {{ item.is_active ? 'Actif' : 'Inactif' }}
                  </v-chip>
                </template>
                <template #[`item.actions`]="{ item }">
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    @click="viewEmployeeDetails(item)"
                  >
                    <v-icon>mdi-eye</v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="#00346E"
                    @click="editEmployee(item)"
                  >
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="#F78C48"
                    @click="unassignEmployee(item)"
                  >
                    <v-icon>mdi-account-remove</v-icon>
                  </v-btn>
                </template>
              </v-data-table>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </template>

    <!-- Dialog pour créer/éditer un site -->
    <v-dialog v-model="showCreateDialog" max-width="800px" @update:model-value="onDialogClose">
      <v-card>
        <v-card-title>
          {{ editedItem ? 'Modifier le site' : 'Nouveau site' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form" @submit.prevent="saveSite">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.name"
                  label="Nom du site"
                  required
                  :rules="[v => !!v || 'Le nom est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.nfcId"
                  label="ID NFC"
                  required
                  :prefix="'PG'"
                  placeholder="123456"
                  :rules="[
                    v => !!v || 'L\'ID NFC est requis',
                    v => /^\d{6}$/.test(v) || 'L\'ID NFC doit être composé de 6 chiffres'
                  ]"
                  hint="Entrez uniquement les 6 chiffres, PG sera ajouté automatiquement"
                  persistent-hint
                  @update:model-value="formatNfcId"
                  maxlength="6"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.address"
                  label="Adresse"
                  required
                  :rules="[v => !!v || 'L\'adresse est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.postal_code"
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
                  v-model="siteForm.city"
                  label="Ville"
                  required
                  :rules="[v => !!v || 'La ville est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.country"
                  label="Pays"
                  required
                  value="France"
                  :rules="[v => !!v || 'Le pays est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.lateMargin"
                  label="Marge de retard (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de retard est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.earlyDepartureMargin"
                  label="Marge de départ anticipé (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de départ anticipé est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.ambiguousMargin"
                  label="Marge pour cas ambigus (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge pour cas ambigus est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.alertEmails"
                  label="Emails pour les alertes (séparés par des virgules)"
                  required
                  :rules="[
                    v => !!v || 'Au moins un email est requis',
                    v => v.split(',').every(email => /.+@.+\..+/.test(email.trim())) || 'Format d\'email invalide'
                  ]"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="siteForm.organization"
                  :items="organizations"
                  label="Franchise"
                  item-title="name"
                  item-value="id"
                  required
                  :rules="[v => !!v || 'La franchise est requise']"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de géolocalisation</v-divider>
                <v-switch
                  v-model="siteForm.requireGeolocation"
                  label="Géolocalisation requise"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.requireGeolocation"
                  v-model="siteForm.geolocationRadius"
                  label="Rayon de géolocalisation (mètres)"
                  type="number"
                  required
                  :rules="[v => !!v || 'Le rayon de géolocalisation est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de synchronisation</v-divider>
                <v-switch
                  v-model="siteForm.allowOfflineMode"
                  label="Autoriser le mode hors ligne"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.allowOfflineMode"
                  v-model="siteForm.maxOfflineDuration"
                  label="Durée maximale hors ligne (heures)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La durée maximale hors ligne est requise']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="#F78C48" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="#00346E" @click="saveSite" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialogs pour les plannings et employés -->
    <v-dialog v-model="showScheduleDialog" max-width="800px">
      <!-- Contenu du dialog de planning -->
    </v-dialog>

    <v-dialog v-model="showEmployeeDialog" max-width="600px">
      <v-card>
        <v-card-title>Assigner un employé</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="employeeForm.employee"
                :items="availableEmployees"
                label="Employé"
                item-title="formatted_name"
                item-value="id"
                :rules="[v => !!v || 'L\'employé est requis']"
                @update:model-value="val => console.log('Employé sélectionné:', val)"
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="employeeForm.schedule"
                :items="selectedSite.schedules || []"
                label="Planning"
                item-title="name"
                item-value="id"
                :rules="[v => !!v || 'Le planning est requis']"
                @update:model-value="val => console.log('Planning sélectionné:', val)"
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="#F78C48" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn 
            color="#00346E" 
            @click="assignEmployee" 
            :loading="saving"
            :disabled="!employeeForm.employee || !employeeForm.schedule"
          >
            Assigner
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { sitesApi } from '@/services/api'

export default {
  name: 'SitesView',
  setup() {
    // États généraux
    const loading = ref(true)
    const saving = ref(false)
    const showCreateDialog = ref(false)
    const showScheduleDialog = ref(false)
    const showEmployeeDialog = ref(false)
    const form = ref(null)
    const editedItem = ref(null)
    const organizations = ref([])
    const selectedSite = ref(null)
    const activeTab = ref('details')
    const loadingSchedules = ref(false)
    const loadingEmployees = ref(false)
    const siteEmployees = ref([])
    const availableEmployees = ref([])
    const employeeForm = ref({
      employee: null,
      schedule: null
    })
    const employeeFormRef = ref(null)

    // Formatage des données
    const formatEmployeeName = (employee) => {
      if (!employee) return ''
      return `${employee.first_name} ${employee.last_name} (${employee.email})`
    }

    // En-têtes des tableaux
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Franchise', align: 'start', key: 'organization' },
      { title: 'Employés', align: 'center', key: 'employeesCount' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const scheduleHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Employés assignés', align: 'center', key: 'employeesCount' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const employeeHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    // Pagination
    const sites = ref([])
    const totalSites = ref(0)
    const currentPage = ref(1)
    const itemsPerPage = ref(10)
    const itemsPerPageOptions = ref([
      { title: '5', value: 5 },
      { title: '10', value: 10 },
      { title: '15', value: 15 },
      { title: 'Tout', value: -1 }
    ])

    // Formulaire du site
    const siteForm = ref({
      name: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      nfcId: '',
      organization: null,
      lateMargin: 15,
      earlyDepartureMargin: 15,
      ambiguousMargin: 20,
      alertEmails: '',
      requireGeolocation: true,
      geolocationRadius: 100,
      allowOfflineMode: true,
      maxOfflineDuration: 24
    })

    // Chargement des données
    const fetchSites = async (page = 1, perPage = itemsPerPage.value) => {
      try {
        loading.value = true
        const response = await sitesApi.getAllSites(page, perPage)
        sites.value = response.data.results
        totalSites.value = response.data.count
        currentPage.value = page
      } catch (error) {
        console.error('Erreur lors du chargement des sites:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchSiteEmployees = async (siteId) => {
      try {
        loadingEmployees.value = true
        // Appel API pour récupérer les employés du site
        const response = await sitesApi.getSiteEmployees(siteId)
        siteEmployees.value = response.data.results
      } catch (error) {
        console.error('Erreur lors du chargement des employés:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    const fetchAvailableEmployees = async () => {
      try {
        loadingEmployees.value = true
        // Appel API pour récupérer tous les employés disponibles
        const response = await sitesApi.getAvailableEmployees()
        // Ajouter le nom formaté à chaque employé
        availableEmployees.value = response.data.results.map(employee => ({
          ...employee,
          formatted_name: formatEmployeeName(employee)
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des employés disponibles:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    // Actions sur les sites
    const viewSiteDetails = (site) => {
      selectedSite.value = site
      activeTab.value = 'details'
      if (site.id) {
        fetchSiteEmployees(site.id)
        fetchAvailableEmployees()
      }
    }

    const editSite = (site) => {
      editedItem.value = site
      siteForm.value = {
        name: site.name,
        address: site.address,
        postal_code: site.postal_code,
        city: site.city,
        country: site.country || 'France',
        nfcId: site.nfc_id?.replace('PG', '') || '',
        organization: site.organization,
        lateMargin: site.late_margin || 15,
        earlyDepartureMargin: site.early_departure_margin || 15,
        ambiguousMargin: site.ambiguous_margin || 20,
        alertEmails: site.alert_emails || '',
        requireGeolocation: site.require_geolocation ?? true,
        geolocationRadius: site.geolocation_radius || 100,
        allowOfflineMode: site.allow_offline_mode ?? true,
        maxOfflineDuration: site.max_offline_duration || 24
      }
      showCreateDialog.value = true
    }

    const saveSite = async () => {
      if (!form.value) return
      const { valid } = await form.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const siteData = { ...siteForm.value }
        siteData.nfcId = 'PG' + siteData.nfcId
        
        if (editedItem.value) {
          await sitesApi.updateSite(editedItem.value.id, siteData)
        } else {
          await sitesApi.createSite(siteData)
        }
        await fetchSites(currentPage.value)
        closeDialog()
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement du site:', error)
      } finally {
        saving.value = false
      }
    }

    const deleteSite = async (siteId) => {
      try {
        await sitesApi.deleteSite(siteId)
        await fetchSites(currentPage.value, itemsPerPage.value)
      } catch (error) {
        console.error('Erreur lors de la suppression du site:', error)
      }
    }

    // Actions sur les plannings
    const viewScheduleDetails = (schedule) => {
      // Implémenter la logique pour afficher les détails du planning
    }

    const editSchedule = (schedule) => {
      // Implémenter la logique pour éditer un planning
    }

    const deleteSchedule = async (schedule) => {
      try {
        await sitesApi.deleteSchedule(selectedSite.value.id, schedule.id)
        // Recharger les plannings
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
      } catch (error) {
        console.error('Erreur lors de la suppression du planning:', error)
      }
    }

    // Actions sur les employés
    const viewEmployeeDetails = (employee) => {
      // Implémenter la logique pour afficher les détails de l'employé
    }

    const editEmployee = (employee) => {
      // Implémenter la logique pour éditer un employé
    }

    const unassignEmployee = async (employee) => {
      try {
        await sitesApi.unassignEmployee(selectedSite.value.id, employee.id)
        await fetchSiteEmployees(selectedSite.value.id)
      } catch (error) {
        console.error('Erreur lors de la désassignation de l\'employé:', error)
      }
    }

    // Utilitaires
    const handleTableUpdate = (options) => {
      const { page, itemsPerPage: newItemsPerPage } = options
      fetchSites(page, newItemsPerPage)
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      showScheduleDialog.value = false
      showEmployeeDialog.value = false
      editedItem.value = null
      resetForm()
      // Réinitialiser le formulaire d'employé
      employeeForm.value = {
        employee: null,
        schedule: null
      }
    }

    const onDialogClose = (val) => {
      if (!val) {
        editedItem.value = null
        resetForm()
      }
    }

    const resetForm = () => {
      if (form.value) {
        form.value.reset()
      }
      siteForm.value = {
        name: '',
        address: '',
        postal_code: '',
        city: '',
        country: 'France',
        nfcId: '',
        organization: null,
        lateMargin: 15,
        earlyDepartureMargin: 15,
        ambiguousMargin: 20,
        alertEmails: '',
        requireGeolocation: true,
        geolocationRadius: 100,
        allowOfflineMode: true,
        maxOfflineDuration: 24
      }
    }

    const formatNfcId = (value) => {
      if (!value) {
        siteForm.value.nfcId = ''
        return
      }
      
      const numbers = String(value).replace(/\D/g, '')
      siteForm.value.nfcId = numbers.substring(0, 6)
    }

    const assignEmployee = async () => {
      console.log('Tentative d\'assignation d\'un employé:', employeeForm.value)

      if (!employeeForm.value.employee || !employeeForm.value.schedule) {
        console.log('Formulaire incomplet')
        return
      }

      if (!selectedSite.value?.id) {
        console.error('ID du site non trouvé')
        return
      }

      saving.value = true
      try {
        console.log('Envoi de la requête d\'assignation:', {
          siteId: selectedSite.value.id,
          scheduleId: employeeForm.value.schedule,
          employeeId: employeeForm.value.employee
        })

        await sitesApi.assignEmployeeToSchedule(
          selectedSite.value.id,
          employeeForm.value.schedule,
          employeeForm.value.employee
        )

        console.log('Assignation réussie')
        await fetchSiteEmployees(selectedSite.value.id)
        closeDialog()
      } catch (error) {
        console.error('Erreur lors de l\'assignation de l\'employé:', error)
        if (error.response?.data) {
          console.error('Détails de l\'erreur:', error.response.data)
        }
      } finally {
        saving.value = false
      }
    }

    onMounted(() => {
      fetchSites()
    })
    
    return {
      // États
      loading,
      saving,
      showCreateDialog,
      showScheduleDialog,
      showEmployeeDialog,
      form,
      employeeForm,
      siteForm,
      organizations,
      selectedSite,
      activeTab,
      loadingSchedules,
      loadingEmployees,
      siteEmployees,
      availableEmployees,
      formatEmployeeName,

      // Données
      headers,
      scheduleHeaders,
      employeeHeaders,
      sites,
      totalSites,
      currentPage,
      itemsPerPage,
      itemsPerPageOptions,
      editedItem,

      // Actions
      handleTableUpdate,
      viewSiteDetails,
      editSite,
      deleteSite,
      closeDialog,
      onDialogClose,
      saveSite,
      formatNfcId,
      viewScheduleDetails,
      editSchedule,
      deleteSchedule,
      viewEmployeeDetails,
      editEmployee,
      unassignEmployee,
      assignEmployee
    }
  }
}
</script>

<style scoped>
.v-data-table {
  border-radius: 8px;
}
</style>

