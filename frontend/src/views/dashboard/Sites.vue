<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Sites</h1>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">
        Ajouter un site
      </v-btn>
    </div>
    
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
            :to="`/dashboard/sites/${item.id}`"
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editSite(item)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click="deleteSite(item.id)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

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
          <v-btn color="error" variant="text" @click="closeDialog">Annuler</v-btn>
          <v-btn color="primary" @click="saveSite" :loading="saving">Enregistrer</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { sitesApi } from '@/services/api'
import api from '@/services/api'

export default {
  name: 'SitesView',
  setup() {
    const loading = ref(true)
    const saving = ref(false)
    const showCreateDialog = ref(false)
    const form = ref(null)
    const editedItem = ref(null)
    const organizations = ref([])

    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Franchise', align: 'start', key: 'organization' },
      { title: 'Employés', align: 'center', key: 'employeesCount' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])
    
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

    const fetchOrganizations = async () => {
      try {
        const response = await api.get('/organizations/')
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
      }
    }

    const handleTableUpdate = (options) => {
      const { page, itemsPerPage: newItemsPerPage } = options
      fetchSites(page, newItemsPerPage)
    }

    const editSite = (item) => {
      editedItem.value = item
      siteForm.value = {
        name: item.name,
        address: item.address,
        postal_code: item.postal_code,
        city: item.city,
        country: item.country || 'France',
        nfcId: item.nfc_id?.replace('PG', '') || '',
        organization: item.organization,
        lateMargin: item.late_margin || 15,
        earlyDepartureMargin: item.early_departure_margin || 15,
        ambiguousMargin: item.ambiguous_margin || 20,
        alertEmails: item.alert_emails || '',
        requireGeolocation: item.require_geolocation ?? true,
        geolocationRadius: item.geolocation_radius || 100,
        allowOfflineMode: item.allow_offline_mode ?? true,
        maxOfflineDuration: item.max_offline_duration || 24
      }
      showCreateDialog.value = true
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      editedItem.value = null
      resetForm()
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

    const formatNfcId = (value) => {
      if (!value) {
        siteForm.value.nfcId = ''
        return
      }
      
      const numbers = String(value).replace(/\D/g, '')
      
      siteForm.value.nfcId = numbers.substring(0, 6)
    }

    onMounted(() => {
      fetchSites()
      fetchOrganizations()
    })
    
    return {
      loading,
      saving,
      headers,
      sites,
      totalSites,
      currentPage,
      itemsPerPage,
      itemsPerPageOptions,
      showCreateDialog,
      form,
      siteForm,
      organizations,
      handleTableUpdate,
      editSite,
      deleteSite,
      closeDialog,
      onDialogClose,
      saveSite,
      editedItem,
      formatNfcId
    }
  }
}
</script>

