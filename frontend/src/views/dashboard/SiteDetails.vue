<template>
  <div>
    <div class="d-flex align-center mb-4">
      <v-btn icon="mdi-arrow-left" variant="text" to="/dashboard/sites" class="mr-4"></v-btn>
      <Title level="2" class="text-h5">{{ site?.name }}</Title>
    </div>

    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-col>
    </v-row>

    <template v-else>
      <v-card>
        <v-tabs v-model="activeTab" color="#00346E">
          <v-tab value="details">Informations</v-tab>
          <v-tab value="schedules">Plannings</v-tab>
          <v-tab value="timesheets">Pointages</v-tab>
          <v-tab value="anomalies">Anomalies</v-tab>
          <v-tab value="reports">Rapports</v-tab>
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
                        <v-icon>mdi-domain</v-icon>
                      </template>
                      <v-list-item-title>Nom</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.name }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-map-marker</v-icon>
                      </template>
                      <v-list-item-title>Adresse</v-list-item-title>
                      <v-list-item-subtitle class="white-space-pre-wrap">
                        {{ site?.address }}
                        {{ site?.postal_code }} {{ site?.city }}
                        {{ site?.country }}
                        <v-btn
                          icon
                          variant="text"
                          size="small"
                          :href="formatAddressForMaps(
                            site?.address || '',
                            site?.postal_code || '',
                            site?.city || '',
                            site?.country || ''
                          )"
                          target="_blank"
                          color="primary"
                          class="mt-2"
                        >
                          <v-icon>mdi-map-marker</v-icon>
                          <v-tooltip activator="parent">Ouvrir dans Google Maps</v-tooltip>
                        </v-btn>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-nfc</v-icon>
                      </template>
                      <v-list-item-title>ID NFC</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.nfc_id }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-qrcode</v-icon>
                      </template>
                      <v-list-item-title>QR Code</v-list-item-title>
                      <v-list-item-subtitle>
                        <div v-if="site?.qr_code">
                          <v-btn
                            color="#00346E"
                            size="small"
                            prepend-icon="mdi-download"
                            @click="downloadQRCode"
                          >
                            Télécharger
                          </v-btn>
                        </div>
                        <v-progress-circular
                          v-else
                          indeterminate
                          color="primary"
                          size="24"
                        ></v-progress-circular>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-office-building</v-icon>
                      </template>
                      <v-list-item-title>Organisation</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.organization_name }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-account-tie</v-icon>
                      </template>
                      <v-list-item-title>Manager</v-list-item-title>
                      <v-list-item-subtitle>{{ (site as any)?.manager_name || 'Aucun manager assigné' }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-alert</v-icon>
                      </template>
                      <v-list-item-title>Marge de retard</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.late_margin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>

                <v-col cols="12" md="6">
                  <v-card class="qr-code-card" variant="outlined">
                    <v-card-title class="d-flex align-center">
                      <v-icon icon="mdi-qrcode" class="mr-2"></v-icon>
                      QR Code du site
                    </v-card-title>
                    <v-card-text class="text-center">
                      <div v-if="site?.qr_code" class="qr-code-container">
                        <v-img
                          :src="site.qr_code"
                          width="400"
                          height="400"
                          class="mx-auto mb-4"
                        ></v-img>
                        <div class="d-flex gap-2">
                          <v-btn
                            color="#00346E"
                            prepend-icon="mdi-download"
                            @click="downloadQRCode"
                          >
                            Télécharger
                          </v-btn>
                          <v-btn
                            color="#F78C48"
                            prepend-icon="mdi-refresh"
                            @click="generateQRCode"
                          >
                            Régénérer
                          </v-btn>
                        </div>
                      </div>
                      <v-progress-circular
                        v-else
                        indeterminate
                        color="primary"
                      ></v-progress-circular>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12">
                  <v-divider class="my-4"></v-divider>
                  <Title level="3" class="mb-4">Informations système</Title>
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-calendar-plus</v-icon>
                      </template>
                      <v-list-item-title>Créé le</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.created_at ? new Date(site.created_at).toLocaleString() : '' }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-calendar-edit</v-icon>
                      </template>
                      <v-list-item-title>Mis à jour le</v-list-item-title>
                      <v-list-item-subtitle>{{ site?.updated_at ? new Date(site.updated_at).toLocaleString() : '' }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>Statut</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip
                          :color="site?.is_active ? 'success' : 'error'"
                          size="small"
                        >
                          {{ site?.is_active ? 'Actif' : 'Inactif' }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- Onglet Plannings -->
            <v-window-item value="schedules">
              <v-data-table
                :headers="schedulesHeaders"
                :items="site?.schedules || []"
                :loading="loadingSchedules"
                :no-data-text="'Aucun planning trouvé'"
              >
                <template #[`item.type`]="{ item }">
                  <v-chip
                    :color="item.schedule_type === 'FIXED' ? 'primary' : 'success'"
                    size="small"
                  >
                    {{ item.schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-window-item>

            <!-- Onglet Pointages -->
            <v-window-item value="timesheets">
              <TimesheetsView 
                :site-id="Number(route.params.id)"
                :is-detail-view="true"
              ></TimesheetsView>
            </v-window-item>

            <!-- Onglet Anomalies -->
            <v-window-item value="anomalies">
              <AnomaliesView 
                :site-id="Number(route.params.id)"
                :is-detail-view="true"
              ></AnomaliesView>
            </v-window-item>

            <!-- Onglet Rapports -->
            <v-window-item value="reports">
              <ReportsView 
                :site-id="Number(route.params.id)"
              ></ReportsView>
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>

<script lang="ts">
import type { Site } from '@/types/api'
import type { ExtendedSchedule } from '@/types/sites'
import { Title } from '@/components/typography'

// Extended Site with additional properties needed for UI
interface ExtendedSite extends Omit<Site, 'schedules' | 'organization_name' | 'manager_name'> {
  schedules?: ExtendedSchedule[];
  download_qr_code?: string;
  manager_name: string;
  organization_name: string;
}
</script>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import TimesheetsView from '@/views/dashboard/Timesheets.vue'
import AnomaliesView from '@/views/dashboard/Anomalies.vue'
import ReportsView from '@/views/dashboard/Reports.vue'
import { sitesApi, schedulesApi } from '@/services/api'
import { formatAddressForMaps } from '@/utils/formatters'
import { generateStyledQRCode } from '@/utils/qrcode'

// Type guard to ensure schedule data is properly typed
function isScheduleArray(data: unknown): data is any[] {
  return Array.isArray(data);
}

const route = useRoute()
const loading = ref(true)
const loadingSchedules = ref(false)
const activeTab = ref('details')
const site = ref<ExtendedSite | null>(null)

const schedulesHeaders = ref([
  { title: 'Nom', align: 'start' as const, key: 'name' },
  { title: 'Type', align: 'center' as const, key: 'type' },
  { title: 'Heures min. quotidiennes', align: 'center' as const, key: 'min_daily_hours' },
  { title: 'Heures min. hebdomadaires', align: 'center' as const, key: 'min_weekly_hours' },
  { title: 'Employés assignés', align: 'center' as const, key: 'assigned_employees_count' }
])

const loadSiteDetails = async () => {
  try {
    loading.value = true
    const siteId = route.params.id
    
    // Charger les détails du site
    const siteResponse = await sitesApi.getSite(Number(siteId))
    
    // Créer un objet étendu avec les propriétés supplémentaires requises
    const siteData = siteResponse.data as unknown as Site & { manager_name?: string; organization_name?: string };
    site.value = {
      ...siteData,
      schedules: [],
      download_qr_code: '',
      manager_name: siteData.manager_name || '',
      organization_name: siteData.organization_name || ''
    } as ExtendedSite

    // Si le site n'a pas de QR code, on le génère
    if (site.value && !site.value.qr_code) {
      await generateQRCode()
    }

    // Charger les plannings
    loadingSchedules.value = true
    const schedulesResponse = await schedulesApi.getSchedulesBySite(Number(siteId))
    
    // Adapter selon l'API - Peut retourner un array direct ou un object avec results
    const schedulesData = 
      'results' in schedulesResponse.data ? schedulesResponse.data.results :
      Array.isArray(schedulesResponse.data) ? schedulesResponse.data : []
    
    if (site.value && isScheduleArray(schedulesData)) {
      site.value.schedules = schedulesData.map((schedule) => ({
        ...schedule,
        id: schedule.id,
        name: schedule.site_name || '',
        min_daily_hours: 0,
        min_weekly_hours: 0,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: 30,
        late_departure_limit: 30,
        break_duration: 60,
        min_break_start: '09:00',
        max_break_end: '17:00',
        frequency_hours: 0,
        frequency_type: 'DAILY',
        frequency_count: 1,
        time_window: 8,
        assigned_employees_count: 0
      })) as ExtendedSchedule[]
    }
  } catch (error) {
    console.error('Erreur lors du chargement des détails du site:', error)
  } finally {
    loading.value = false
    loadingSchedules.value = false
  }
}

const generateQRCode = async () => {
  if (!site.value) return
  try {
    // Générer une version sans cadre pour la prévisualisation
    const previewQRCode = await generateStyledQRCode(site.value, {
      width: 500,
      height: 500,
      qrSize: 500,
      showFrame: false
    })
    
    // Générer une version avec cadre pour le téléchargement
    const downloadQRCode = await generateStyledQRCode(site.value, {
      width: 500,
      height: 700,
      qrSize: 400,
      showFrame: true,
      radius: 20
    })
    
    if (site.value) {
      site.value.qr_code = previewQRCode
      site.value.download_qr_code = downloadQRCode
    }
  } catch (error) {
    console.error('Erreur lors de la génération du QR code:', error)
  }
}

const downloadQRCode = async () => {
  if (!site.value) return
  try {
    // Utiliser la version avec cadre pour le téléchargement
    if (!site.value.download_qr_code) {
      await generateQRCode()
    }
    
    const link = document.createElement('a')
    link.href = site.value.download_qr_code || ''
    link.download = `qr-code-${site.value.name.toLowerCase().replace(/\s+/g, '-')}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('Erreur lors du téléchargement du QR code:', error)
  }
}

onMounted(loadSiteDetails)
</script>

<style scoped>
.white-space-pre-wrap {
  white-space: pre-wrap;
}

.qr-code-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

:deep(.v-img.mx-auto) {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 8px;
  background-color: white;
}

.gap-2 {
  gap: 8px;
}

:deep(.v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-btn--icon .v-icon) {
  color: rgb(0, 52, 110) !important;
  opacity: 1 !important;
}
</style> 