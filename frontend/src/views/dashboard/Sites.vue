<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Sites</h1>
      <v-btn color="#00346E" prepend-icon="mdi-plus" @click="openCreateDialog">
        Ajouter un site
      </v-btn>
    </div>
    
    <!-- Vue principale des sites -->
    <template v-if="!selectedSite">
      <v-card>
        <v-data-table
          :headers="headers"
          :items="sites || []"
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
          @click:row="(_: any, { item }: any) => viewSiteDetails(item)"
        >
          <template v-slot:item.address="{ item }">
            {{ item.address }}, {{ item.postal_code }} {{ item.city }}
            <v-btn
              icon
              variant="text"
              size="x-small"
              :href="formatAddressForMaps(item.address, item.postal_code, item.city, item.country)"
              target="_blank"
              color="primary"
            >
              <v-icon>mdi-map-marker</v-icon>
            </v-btn>
          </template>

          <template v-slot:item.status="{ item }">
            <v-chip
              :color="item.is_active ? 'success' : 'error'"
              size="small"
            >
              {{ item.is_active ? 'Actif' : 'Inactif' }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              variant="text"
              size="small"
              :to="`/dashboard/sites/${item.id}`"
            >
              <v-icon>mdi-eye</v-icon>
              <v-tooltip activator="parent">Voir les détails</v-tooltip>
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
              :color="item.is_active ? 'error' : 'success'"
              @click="toggleSiteStatus(item)"
              :loading="item.isUpdating"
            >
              <v-icon>{{ item.is_active ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              color="#F78C48"
              @click="deleteSite(item)"
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
                      <v-list-item-subtitle>{{ selectedSite.name }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-map-marker</v-icon>
                      </template>
                      <v-list-item-title>Adresse</v-list-item-title>
                      <v-list-item-subtitle class="white-space-pre-wrap">
                        {{ selectedSite.address }}
                        {{ selectedSite.postal_code }} {{ selectedSite.city }}
                        {{ selectedSite.country }}
                        <v-btn
                          icon
                          variant="text"
                          size="small"
                          :href="formatAddressForMaps(selectedSite.address, selectedSite.postal_code, selectedSite.city, selectedSite.country)"
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
                      <v-list-item-subtitle>{{ selectedSite.nfc_id }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-qrcode</v-icon>
                      </template>
                      <v-list-item-title>QR Code</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-btn
                          color="#00346E"
                          size="small"
                          prepend-icon="mdi-download"
                          @click="downloadQRCode(selectedSite)"
                          :loading="!selectedSite.qr_code"
                        >
                          Télécharger
                        </v-btn>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-office-building</v-icon>
                      </template>
                      <v-list-item-title>Organisation</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.organization_name }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-account-tie</v-icon>
                      </template>
                      <v-list-item-title>Manager</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.manager_name || 'Aucun manager assigné' }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-alert</v-icon>
                      </template>
                      <v-list-item-title>Marge de retard</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.late_margin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-check</v-icon>
                      </template>
                      <v-list-item-title>Marge de départ anticipé</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.early_departure_margin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-clock-question</v-icon>
                      </template>
                      <v-list-item-title>Marge pour cas ambigus</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.ambiguous_margin }} minutes</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-email-alert</v-icon>
                      </template>
                      <v-list-item-title>Emails pour les alertes</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.alert_emails }}</v-list-item-subtitle>
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
                      <div v-if="selectedSite.qr_code" class="qr-code-container">
                        <v-img
                          :src="selectedSite.qr_code"
                          max-width="250"
                          class="mx-auto mb-4"
                        ></v-img>
                        <v-btn
                          color="#00346E"
                          prepend-icon="mdi-download"
                          @click="downloadQRCode(selectedSite)"
                        >
                          Télécharger
                        </v-btn>
                        <v-btn
                          color="#F78C48"
                          prepend-icon="mdi-refresh"
                          class="ml-2"
                          @click="generateQRCode(selectedSite)"
                        >
                          Régénérer
                        </v-btn>
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
                  <h3 class="text-h6 mb-4">Paramètres de géolocalisation</h3>
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-map-marker-radius</v-icon>
                      </template>
                      <v-list-item-title>Géolocalisation requise</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip
                          :color="selectedSite.require_geolocation ? 'success' : 'error'"
                          size="small"
                        >
                          {{ selectedSite.require_geolocation ? 'Oui' : 'Non' }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="selectedSite.require_geolocation">
                      <template #prepend>
                        <v-icon>mdi-radius</v-icon>
                      </template>
                      <v-list-item-title>Rayon de géolocalisation</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.geolocation_radius }} mètres</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
                <v-col cols="12">
                  <v-divider class="my-4"></v-divider>
                  <h3 class="text-h6 mb-4">Paramètres de synchronisation</h3>
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-wifi-off</v-icon>
                      </template>
                      <v-list-item-title>Mode hors ligne autorisé</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip
                          :color="selectedSite.allow_offline_mode ? 'success' : 'error'"
                          size="small"
                        >
                          {{ selectedSite.allow_offline_mode ? 'Oui' : 'Non' }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="selectedSite.allow_offline_mode">
                      <template #prepend>
                        <v-icon>mdi-timer-sand</v-icon>
                      </template>
                      <v-list-item-title>Durée maximale hors ligne</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedSite.max_offline_duration }} heures</v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
                <v-col cols="12">
                  <v-divider class="my-4"></v-divider>
                  <h3 class="text-h6 mb-4">Informations système</h3>
                  <v-list>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-calendar-plus</v-icon>
                      </template>
                      <v-list-item-title>Créé le</v-list-item-title>
                      <v-list-item-subtitle>{{ new Date(selectedSite.created_at).toLocaleString() }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-calendar-edit</v-icon>
                      </template>
                      <v-list-item-title>Mis à jour le</v-list-item-title>
                      <v-list-item-subtitle>{{ new Date(selectedSite.updated_at).toLocaleString() }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template #prepend>
                        <v-icon>mdi-check-circle</v-icon>
                      </template>
                      <v-list-item-title>Statut</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip
                          :color="selectedSite.is_active ? 'success' : 'error'"
                          size="small"
                        >
                          {{ selectedSite.is_active ? 'Actif' : 'Inactif' }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- Onglet Plannings -->
            <v-window-item value="schedules">
              <div class="d-flex justify-space-between align-center mb-4">
                <div></div>
                <v-btn color="#00346E" prepend-icon="mdi-plus" @click="showCreateScheduleDialog">
                  Ajouter un planning
                </v-btn>
              </div>
              <v-data-table
                :headers="scheduleHeaders"
                :items="selectedSite?.schedules || []"
                :loading="loadingSchedules"
                :no-data-text="'Aucun planning trouvé'"
                :items-per-page="-1"
                hide-default-footer
              >
                <template #[`item.type`]="{ item }">
                  <v-chip
                    :color="item.schedule_type === 'FIXED' ? '#00346E' : '#F78C48'"
                    size="small"
                  >
                    {{ item.schedule_type === 'FIXED' ? 'Fixe (gardien)' : 'Fréquence (nettoyage)' }}
                  </v-chip>
                </template>
                <template #[`item.employees`]="{ item }">
                  <div class="d-flex align-center">
                    <div v-if="item.assigned_employees && item.assigned_employees.length > 0">
                      <v-chip
                        v-for="employee in item.assigned_employees"
                        :key="employee.employee"
                        class="mr-1 mb-1"
                        closable
                        @click:close="unassignEmployeeFromSchedule(item.id, employee.employee)"
                      >
                        {{ employee.employee }}
                      </v-chip>
                    </div>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="#00346E"
                      @click="showAssignEmployeeDialog(item)"
                    >
                      <v-icon>mdi-account-plus</v-icon>
                    </v-btn>
                  </div>
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

            <!-- Onglet Timesheets -->
            <v-window-item value="timesheets">
              <TimesheetsView 
                :site-id="selectedSite.id"
                :is-detail-view="true"
              ></TimesheetsView>
            </v-window-item>

            <!-- Onglet Anomalies -->
            <v-window-item value="anomalies">
              <AnomaliesView 
                :site-id="selectedSite.id"
                :is-detail-view="true"
              ></AnomaliesView>
            </v-window-item>

            <!-- Onglet Rapports -->
            <v-window-item value="reports">
              <ReportsView 
                :site-id="selectedSite.id"
              ></ReportsView>
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
          <v-form ref="form" :model-value="formValid">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.name"
                  label="Nom"
                  :rules="[v => !!v || 'Le nom est requis']"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="siteForm.organization"
                  :items="organizations"
                  label="Organisation"
                  item-title="name"
                  item-value="id"
                  :rules="[(v: number) => !!v || 'L\'organisation est requise']"
                  :no-data-text="'Aucune organisation disponible'"
                  @update:model-value="loadManagers"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="siteForm.manager"
                  :items="managers"
                  label="Manager"
                  item-title="name"
                  item-value="id"
                  :rules="[(v: number) => !!v || 'Le manager est requis']"
                  :no-data-text="'Aucun manager disponible'"
                  :disabled="!siteForm.organization"
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="siteForm.nfcId"
                  label="ID NFC"
                  :rules="[
                    (v: string) => !!v || 'L\'ID NFC est requis',
                    (v: string) => /^\d{4}$/.test(v) || 'L\'ID NFC doit contenir 4 chiffres'
                  ]"
                  :hint="nfcIdPreview"
                  persistent-hint
                  :disabled="!siteForm.organization"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.address"
                  label="Adresse"
                  required
                  :rules="[(v: string) => !!v || 'L\'adresse est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.postal_code"
                  label="Code postal"
                  required
                  :rules="[
                    (v: string) => !!v || 'Le code postal est requis',
                    (v: string) => /^\d{5}$/.test(v) || 'Le code postal doit contenir 5 chiffres'
                  ]"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.city"
                  label="Ville"
                  required
                  :rules="[(v: string) => !!v || 'La ville est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.country"
                  label="Pays"
                  required
                  value="France"
                  :rules="[(v: string) => !!v || 'Le pays est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.late_margin"
                  label="Marge de retard (minutes)"
                  type="number"
                  required
                  :rules="[(v: number) => !!v || 'La marge de retard est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.early_departure_margin"
                  label="Marge de départ anticipé (minutes)"
                  type="number"
                  required
                  :rules="[(v: number) => !!v || 'La marge de départ anticipé est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.ambiguous_margin"
                  label="Marge pour cas ambigus (minutes)"
                  type="number"
                  required
                  :rules="[(v: number) => !!v || 'La marge pour cas ambigus est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.alert_emails"
                  label="Emails pour les alertes (séparés par des virgules)"
                  required
                  :rules="[
                    (v: string) => !!v || 'Au moins un email est requis',
                    (v: string) => v.split(',').every((email: string) => /.+@.+\..+/.test(email.trim())) || 'Format d\'email invalide'
                  ]"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de géolocalisation</v-divider>
                <v-switch
                  v-model="siteForm.require_geolocation"
                  label="Géolocalisation requise"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.require_geolocation"
                  v-model="siteForm.geolocation_radius"
                  label="Rayon de géolocalisation (mètres)"
                  type="number"
                  required
                  :rules="[(v: number) => !!v || 'Le rayon de géolocalisation est requis']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Paramètres de synchronisation</v-divider>
                <v-switch
                  v-model="siteForm.allow_offline_mode"
                  label="Autoriser le mode hors ligne"
                  color="primary"
                ></v-switch>
                <v-text-field
                  v-if="siteForm.allow_offline_mode"
                  v-model="siteForm.max_offline_duration"
                  label="Durée maximale hors ligne (heures)"
                  type="number"
                  required
                  :rules="[(v: number) => !!v || 'La durée maximale hors ligne est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-divider class="mb-3">Statut du site</v-divider>
                <v-switch
                  v-model="siteForm.is_active"
                  label="Site actif"
                  color="success"
                ></v-switch>
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

    <!-- Dialog pour les plannings -->
    <v-dialog v-model="showScheduleDialog" max-width="800px" persistent>
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>{{ selectedSchedule ? 'Modifier le planning' : 'Nouveau planning' }}</span>
          <v-btn icon="mdi-close" variant="text" @click="closeScheduleDialog"></v-btn>
        </v-card-title>

        <v-card-text>
          <v-form ref="scheduleFormRef" @submit.prevent>
            <v-container>
              <v-row>
                <!-- Informations de base -->
                <v-col cols="12">
                  <v-radio-group
                    v-model="scheduleForm.schedule_type"
                    label="Type de planning*"
                    :rules="[(v: string) => !!v || 'Le type est requis']"
                    hide-details="auto"
                  >
                    <v-radio
                      label="Fixe (gardien)"
                      value="FIXED"
                      color="#00346E"
                    ></v-radio>
                    <v-radio
                      label="Fréquence (nettoyage)"
                      value="FREQUENCY"
                      color="#F78C48"
                    ></v-radio>
                  </v-radio-group>
                </v-col>

                <!-- Paramètres spécifiques au type FIXED (gardien) -->
                <template v-if="scheduleForm.schedule_type === 'FIXED'">
                  <!-- Heures -->
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="scheduleForm.min_daily_hours"
                      label="Heures minimales par jour*"
                      type="number"
                      min="0"
                      step="0.5"
                      :rules="[(v: number) => !!v || 'Les heures minimales par jour sont requises']"
                      hide-details="auto"
                    ></v-text-field>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="scheduleForm.min_weekly_hours"
                      label="Heures minimales par semaine*"
                      type="number"
                      min="0"
                      step="0.5"
                      :rules="[(v: number) => !!v || 'Les heures minimales par semaine sont requises']"
                      hide-details="auto"
                    ></v-text-field>
                  </v-col>

                  <!-- Paramètres de pointage pour FIXED -->
                  <v-col cols="12">
                    <v-card variant="outlined" class="pa-4">
                      <div class="text-subtitle-1 mb-4">
                        Paramètres de pointage
                        <v-tooltip text="Pour les gardiens : configurez les marges de flexibilité pour les arrivées et départs">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" class="ml-2">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-row>
                        <v-col cols="12" md="6">
                          <v-switch
                            v-model="scheduleForm.allow_early_arrival"
                            label="Autoriser les arrivées en avance"
                            color="#00346E"
                            hide-details
                          >
                            <template v-slot:append>
                              <v-tooltip text="Permet au gardien d'arriver avant l'heure prévue dans la limite configurée">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-switch>
                        </v-col>

                        <v-col cols="12" md="6">
                          <v-switch
                            v-model="scheduleForm.allow_late_departure"
                            label="Autoriser les départs en retard"
                            color="#00346E"
                            hide-details
                          >
                            <template v-slot:append>
                              <v-tooltip text="Permet au gardien de partir après l'heure prévue dans la limite configurée">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-switch>
                        </v-col>

                        <v-col cols="12" md="6" v-if="scheduleForm.allow_early_arrival">
                          <v-text-field
                            v-model="scheduleForm.early_arrival_limit"
                            label="Limite d'arrivée en avance (minutes)"
                            type="number"
                            min="0"
                            :rules="[(v: number) => !!v || 'La limite d\'arrivée en avance est requise']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Nombre de minutes maximum autorisées pour une arrivée anticipée">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>

                        <v-col cols="12" md="6" v-if="scheduleForm.allow_late_departure">
                          <v-text-field
                            v-model="scheduleForm.late_departure_limit"
                            label="Limite de départ en retard (minutes)"
                            type="number"
                            min="0"
                            :rules="[(v: number) => !!v || 'La limite de départ en retard est requise']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Nombre de minutes maximum autorisées pour un départ tardif">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>

                  <!-- Paramètres de pause pour FIXED -->
                  <v-col cols="12">
                    <v-card variant="outlined" class="pa-4">
                      <div class="text-subtitle-1 mb-4">
                        Paramètres de pause
                        <v-tooltip text="Pour les gardiens : configurez les horaires de pause autorisés">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" class="ml-2">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-row>
                        <v-col cols="12" md="4">
                          <v-text-field
                            v-model="scheduleForm.break_duration"
                            label="Durée de la pause (minutes)*"
                            type="number"
                            min="0"
                            :rules="[(v: number) => !!v || 'La durée de la pause est requise']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Durée totale de pause autorisée par jour">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>

                        <v-col cols="12" md="4">
                          <v-text-field
                            v-model="scheduleForm.min_break_start"
                            label="Début de pause min.*"
                            type="time"
                            :rules="[(v: string) => !!v || 'L\'heure de début de pause est requise']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Heure la plus tôt à laquelle la pause peut commencer">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>

                        <v-col cols="12" md="4">
                          <v-text-field
                            v-model="scheduleForm.max_break_end"
                            label="Fin de pause max.*"
                            type="time"
                            :rules="[(v: string) => !!v || 'L\'heure de fin de pause est requise']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Heure la plus tard à laquelle la pause doit se terminer">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>
                </template>

                <!-- Paramètres spécifiques au type FREQUENCY (nettoyage) -->
                <template v-else>
                  <v-col cols="12">
                    <v-card variant="outlined" class="pa-4">
                      <div class="text-subtitle-1 mb-4">
                        Paramètres de fréquence
                        <v-tooltip text="Pour le nettoyage : définissez la fréquence des passages et leur durée">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" class="ml-2">mdi-help-circle-outline</v-icon>
                          </template>
                        </v-tooltip>
                      </div>
                      <v-row>
                        <v-col cols="12" md="6">
                          <v-text-field
                            v-model="scheduleForm.frequency_hours"
                            label="Nombre d'heures par passage*"
                            type="number"
                            min="0"
                            step="0.5"
                            :rules="[(v: number) => !!v || 'Le nombre d\'heures par passage est requis']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Durée prévue pour chaque intervention de nettoyage">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>
                        <v-col cols="12" md="6">
                          <v-select
                            v-model="scheduleForm.frequency_type"
                            :items="[
                              { title: 'Par jour', value: 'DAILY' },
                              { title: 'Par semaine', value: 'WEEKLY' },
                              { title: 'Par mois', value: 'MONTHLY' }
                            ]"
                            item-title="title"
                            item-value="value"
                            label="Type de fréquence*"
                            :rules="[(v: string) => !!v || 'Le type de fréquence est requis']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Définit la période sur laquelle compter les passages">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-select>
                        </v-col>
                        <v-col cols="12" md="6">
                          <v-text-field
                            v-model="scheduleForm.frequency_count"
                            label="Nombre de passages*"
                            type="number"
                            min="1"
                            :rules="[(v: number) => !!v || 'Le nombre de passages est requis']"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Nombre d'interventions sur la période choisie (ex: 3 fois par semaine)">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>
                        <v-col cols="12" md="6">
                          <v-text-field
                            v-model="scheduleForm.time_window"
                            label="Plage horaire (heures)*"
                            type="number"
                            min="1"
                            max="24"
                            :rules="[
                              (v: number) => !!v || 'La plage horaire est requise',
                              (v: number) => v <= 24 || 'La plage horaire ne peut pas dépasser 24 heures'
                            ]"
                            hide-details="auto"
                          >
                            <template v-slot:append-inner>
                              <v-tooltip text="Fenêtre de temps disponible pour effectuer l'intervention">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                                </template>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>
                      </v-row>
                      <!-- Résumé pour le planning de fréquence -->
                      <v-row>
                        <v-col cols="12" class="pt-4">
                          <v-card color="grey-lighten-4" class="pa-3">
                            <div class="text-body-2">
                              <v-icon color="#00346E" class="mr-2">mdi-information</v-icon>
                              <span v-if="scheduleForm.frequency_type && scheduleForm.frequency_count && scheduleForm.frequency_hours && scheduleForm.time_window">
                                {{ scheduleForm.frequency_count }} passage{{ scheduleForm.frequency_count > 1 ? 's' : '' }} 
                                {{ scheduleForm.frequency_type === 'DAILY' ? 'par jour' : 
                                   scheduleForm.frequency_type === 'WEEKLY' ? 'par semaine' : 'par mois' }} 
                                de {{ scheduleForm.frequency_hours }} heure{{ scheduleForm.frequency_hours > 1 ? 's' : '' }} 
                                sur une plage de {{ scheduleForm.time_window }} heure{{ scheduleForm.time_window > 1 ? 's' : '' }}.
                              </span>
                              <span v-else>Veuillez remplir tous les champs pour voir le résumé.</span>
                            </div>
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-col>
                </template>

                <!-- Horaires par jour - uniquement pour le type FIXED -->
                <v-col cols="12" v-if="scheduleForm.schedule_type === 'FIXED'">
                  <v-card variant="outlined" class="pa-4">
                    <div class="text-subtitle-1 mb-4">
                      Horaires par jour
                      <v-tooltip text="Pour les gardiens : définissez les horaires précis pour chaque jour">
                        <template v-slot:activator="{ props }">
                          <v-icon v-bind="props" size="small" class="ml-2">mdi-help-circle-outline</v-icon>
                        </template>
                      </v-tooltip>
                    </div>
                    <v-row v-for="(day, index) in weekDays" :key="day.value">
                      <v-col cols="12" md="3">
                        <v-switch
                          v-model="scheduleForm.days[index].enabled"
                          :label="day.text"
                          color="#00346E"
                          hide-details
                        ></v-switch>
                      </v-col>
                      <v-col cols="12" md="9" v-if="scheduleForm.days[index].enabled">
                        <v-row>
                          <v-col cols="12" md="6">
                            <div class="d-flex align-center">
                              <v-text-field
                                v-model="scheduleForm.days[index].start_time_1"
                                label="Début matin"
                                type="time"
                                hide-details="auto"
                                class="mr-2"
                              ></v-text-field>
                              <v-text-field
                                v-model="scheduleForm.days[index].end_time_1"
                                label="Fin matin"
                                type="time"
                                hide-details="auto"
                              ></v-text-field>
                            </div>
                          </v-col>
                          <v-col cols="12" md="6">
                            <div class="d-flex align-center">
                              <v-text-field
                                v-model="scheduleForm.days[index].start_time_2"
                                label="Début après-midi"
                                type="time"
                                hide-details="auto"
                                class="mr-2"
                              ></v-text-field>
                              <v-text-field
                                v-model="scheduleForm.days[index].end_time_2"
                                label="Fin après-midi"
                                type="time"
                                hide-details="auto"
                              ></v-text-field>
                            </div>
                          </v-col>
                        </v-row>
                      </v-col>
                    </v-row>
                    <!-- Résumé pour le planning fixe -->
                    <v-row>
                      <v-col cols="12" class="pt-4">
                        <v-card color="grey-lighten-4" class="pa-3">
                          <div class="text-body-2">
                            <v-icon color="#00346E" class="mr-2">mdi-information</v-icon>
                            <template v-if="scheduleForm.days.some((day: ScheduleDay) => day.enabled)">
                              Planning actif {{ scheduleForm.days.filter((day: ScheduleDay) => day.enabled).length }} jour{{ scheduleForm.days.filter((day: ScheduleDay) => day.enabled).length > 1 ? 's' : '' }} 
                              par semaine avec pause de {{ scheduleForm.break_duration }} minutes 
                              entre {{ scheduleForm.min_break_start }} et {{ scheduleForm.max_break_end }}.
                              <template v-if="scheduleForm.allow_early_arrival || scheduleForm.allow_late_departure">
                                <br>Flexibilité : 
                                <template v-if="scheduleForm.allow_early_arrival">arrivée jusqu'à {{ scheduleForm.early_arrival_limit }} minutes en avance</template>
                                <template v-if="scheduleForm.allow_early_arrival && scheduleForm.allow_late_departure"> et </template>
                                <template v-if="scheduleForm.allow_late_departure">départ jusqu'à {{ scheduleForm.late_departure_limit }} minutes en retard</template>
                              </template>
                            </template>
                            <span v-else>Veuillez sélectionner au moins un jour pour voir le résumé.</span>
                          </div>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="error"
            variant="text"
            @click="closeScheduleDialog"
            :disabled="saving"
          >
            Annuler
          </v-btn>
          <v-btn
            color="primary"
            @click="saveSchedule"
            :loading="saving"
            :disabled="!isScheduleFormValid"
          >
            {{ selectedSchedule ? 'Modifier' : 'Créer' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog pour assigner un employé -->
    <v-dialog v-model="showAssignDialog" max-width="500px">
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
                :rules="[(v: number) => !!v || 'L\'employé est requis']"
                :no-data-text="'Aucun employé disponible'"
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
            :disabled="!employeeForm.employee"
          >
            Assigner
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="showDeleteDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Confirmation de suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer ce site ? Cette action est irréversible.
          <div class="mt-4 text-subtitle-1">
            {{ siteToDelete?.name }}
          </div>
          <div class="text-caption">
            {{ siteToDelete?.address }}<br>
            {{ siteToDelete?.postal_code }} {{ siteToDelete?.city }}<br>
            {{ siteToDelete?.country }}
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn 
            color="error" 
            @click="confirmDeleteSite"
            :loading="deleting"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog pour le calendrier -->
    <v-dialog v-model="showCalendarDialog" max-width="1200px">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Calendrier du planning: {{ selectedScheduleForCalendar?.name }}</span>
          <v-btn icon="mdi-close" variant="text" @click="showCalendarDialog = false"></v-btn>
        </v-card-title>
        <v-card-text>
          <schedule-calendar
            v-if="selectedScheduleForCalendar"
            :schedule="selectedScheduleForCalendar"
          ></schedule-calendar>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, computed, onMounted } from 'vue'
import ScheduleCalendar from '@/components/ScheduleCalendar.vue'
import TimesheetsView from '@/views/dashboard/Timesheets.vue'
import AnomaliesView from '@/views/dashboard/Anomalies.vue'
import ReportsView from '@/views/dashboard/Reports.vue'
import { sitesApi, schedulesApi, organizationsApi, usersApi, anomaliesApi, reportsApi, timesheetsApi, type Site, type Schedule, type Employee, type Organization } from '@/services/api'
import QRCode from 'qrcode'
import type { EditingTimesheet, Filters, SiteOption, TableOptions, Timesheet } from '@/types/sites'
import { formatPhoneNumber, formatAddressForMaps } from '@/utils/formatters'
import { useRouter } from 'vue-router'

// Interfaces
interface WeekDay {
  text: string;
  value: number;
}

interface ScheduleDetail {
  id?: number;
  day_of_week: number;
  start_time_1: string;
  end_time_1: string;
  start_time_2: string;
  end_time_2: string;
}

interface SiteForm {
  name: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  nfcId: string;
  organization: number | null;
  manager: number | null;
  late_margin: number;
  early_departure_margin: number;
  ambiguous_margin: number;
  alert_emails: string;
  require_geolocation: boolean;
  geolocation_radius: number;
  allow_offline_mode: boolean;
  max_offline_duration: number;
  is_active: boolean;
}

interface ScheduleForm {
  name: string;
  schedule_type: 'FIXED' | 'FREQUENCY';
  min_daily_hours: number;
  min_weekly_hours: number;
  allow_early_arrival: boolean;
  allow_late_departure: boolean;
  early_arrival_limit: number;
  late_departure_limit: number;
  break_duration: number;
  min_break_start: string;
  max_break_end: string;
  days: ScheduleDay[];
  frequency_hours: number;
  frequency_type: 'DAILY' | 'WEEKLY' | 'MONTHLY';
  frequency_count: number;
  time_window: number;
}

interface ScheduleDay {
  enabled: boolean;
  start_time_1: string;
  end_time_1: string;
  start_time_2: string;
  end_time_2: string;
}

interface EmployeeForm {
  employee: number | null;
  schedule: number | null;
}

interface Manager {
  id: number;
  name: string;
}

interface Anomaly {
  id: number;
  site_id: number;
  employee_id: number;
  employee_name: string;
  type: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Report {
  id: number;
  site_id: number;
  type: string;
  period_start: string;
  period_end: string;
  data: any;
  created_at: string;
  updated_at: string;
}

// Add loadingEmployees ref
const loadingEmployees = ref<boolean>(false)

// Update the Site interface to extend the API type
interface ExtendedSite extends Omit<Site, 'schedules'> {
  isUpdating?: boolean;
  timesheets?: Timesheet[];
  anomalies?: Anomaly[];
  reports?: Report[];
  schedules?: Schedule[];
  manager_name?: string;
}

export default defineComponent({
  name: 'SitesView',
  components: {
    ScheduleCalendar,
    TimesheetsView,
    AnomaliesView,
    ReportsView
  },
  setup() {
    const router = useRouter()

    // Jours de la semaine
    const weekDays: WeekDay[] = [
      { text: 'Lundi', value: 1 },
      { text: 'Mardi', value: 2 },
      { text: 'Mercredi', value: 3 },
      { text: 'Jeudi', value: 4 },
      { text: 'Vendredi', value: 5 },
      { text: 'Samedi', value: 6 },
      { text: 'Dimanche', value: 0 }
    ]

    // Initialisation du formulaire de planning
    const initScheduleDays = (): ScheduleDay[] => {
      return weekDays.map(() => ({
        enabled: false,
        start_time_1: '08:00',
        end_time_1: '12:00',
        start_time_2: '14:00',
        end_time_2: '18:00'
      }))
    }

    // États généraux
    const loading = ref<boolean>(true)
    const saving = ref<boolean>(false)
    const showCreateDialog = ref<boolean>(false)
    const showScheduleDialog = ref<boolean>(false)
    const showEmployeeDialog = ref<boolean>(false)
    const showAssignDialog = ref<boolean>(false)
    const selectedSchedule = ref<Schedule | null>(null)
    const form = ref<any>(null)
    const valid = ref<boolean>(false)
    const editedItem = ref<ExtendedSite | null>(null)
    const organizations = ref<Organization[]>([])
    const managers = ref<Manager[]>([])
    const selectedSite = ref<ExtendedSite | null>(null)
    const activeTab = ref<'details' | 'schedules' | 'timesheets' | 'anomalies' | 'reports'>('details')
    const loadingSchedules = ref<boolean>(false)
    const loadingTimesheets = ref<boolean>(false)
    const loadingAnomalies = ref<boolean>(false)
    const loadingReports = ref<boolean>(false)
    const siteEmployees = ref<Employee[]>([])
    const availableEmployees = ref<Employee[]>([])
    const employeeForm = ref<EmployeeForm>({
      employee: null,
      schedule: null
    })
    const employeeFormRef = ref<any>(null)
    const scheduleForm = ref<ScheduleForm>({
      name: '',
      schedule_type: 'FIXED',
      min_daily_hours: 0,
      min_weekly_hours: 0,
      allow_early_arrival: false,
      allow_late_departure: false,
      early_arrival_limit: 30,
      late_departure_limit: 30,
      break_duration: 60,
      min_break_start: '09:00',
      max_break_end: '17:00',
      days: initScheduleDays(),
      frequency_hours: 0,
      frequency_type: 'DAILY',
      frequency_count: 1,
      time_window: 8
    })
    const scheduleFormRef = ref<any>(null)
    const showCalendarDialog = ref<boolean>(false)
    const selectedScheduleForCalendar = ref<Schedule | null>(null)
    const showDeleteDialog = ref<boolean>(false)
    const siteToDelete = ref<Site | null>(null)
    const deleting = ref<boolean>(false)

    // Formatage des données
    const formatEmployeeName = (employee: Employee): string => {
      if (!employee) return ''
      return `${employee.first_name} ${employee.last_name} (${employee.email})`
    }

    // En-têtes des tableaux
    const headers = ref([
      { title: 'Nom', align: 'start' as const, key: 'name' },
      { title: 'Adresse', align: 'start' as const, key: 'address' },
      { title: 'ID NFC', align: 'start' as const, key: 'nfc_id' },
      { title: 'Organisation', align: 'start' as const, key: 'organization_name' },
      { title: 'Statut', align: 'center' as const, key: 'status' },
      { title: 'Actions', align: 'end' as const, key: 'actions', sortable: false }
    ])

    const scheduleHeaders = ref([
      { title: 'Nom', align: 'start' as const, key: 'name' },
      { title: 'Type', align: 'center' as const, key: 'type' },
      { title: 'Employés', align: 'start' as const, key: 'employees' },
      { title: 'Actions', align: 'end' as const, key: 'actions', sortable: false }
    ])

    // Pagination
    const sites = ref<ExtendedSite[]>([])
    const totalSites = ref<number>(0)
    const currentPage = ref<number>(1)
    const itemsPerPage = ref<number>(10)
    const itemsPerPageOptions = ref([
      { title: '5', value: 5 },
      { title: '10', value: 10 },
      { title: '15', value: 15 },
      { title: 'Tout', value: -1 }
    ])

    // Formulaire du site
    const siteForm = ref<SiteForm>({
      name: '',
      address: '',
      postal_code: '',
      city: '',
      country: 'France',
      nfcId: '',
      organization: null,
      manager: null,
      late_margin: 15,
      early_departure_margin: 15,
      ambiguous_margin: 20,
      alert_emails: '',
      require_geolocation: true,
      geolocation_radius: 100,
      allow_offline_mode: true,
      max_offline_duration: 24,
      is_active: true
    })

    // Validation des IDs de sites
    const validateSiteId = (siteId: string): boolean => {
      if (!siteId || !siteId.includes('-')) return false;
      
      try {
        const [orgPart, sitePart] = siteId.split('-');
        
        // Valider la partie organisation
        if (!orgPart || !orgPart.match(/^\d{3}$/)) return false;
        
        // Valider la partie site
        if (!sitePart || !sitePart.match(/^S\d{4}$/)) return false;
        
        const siteNumber = parseInt(sitePart.slice(1));
        return siteNumber > 0 && siteNumber < 10000;
      } catch {
        return false;
      }
    };

    // Chargement des données
    const fetchSites = async (page: number = 1, perPage: number = itemsPerPage.value): Promise<void> => {
      try {
        loading.value = true
        console.log('[Sites][Data] Chargement des sites avec paramètres:', { page, perPage })
        const response = await sitesApi.getAllSites(page, perPage)
        console.log('[Sites][Data] Réponse API reçue:', {
          count: response.data.count,
          resultsCount: response.data.results?.length || 0
        })
        sites.value = Array.isArray(response.data.results) ? response.data.results : []
        totalSites.value = response.data.count || 0
        currentPage.value = page
        console.log('[Sites][Data] Sites chargés avec succès:', {
          totalSites: totalSites.value,
          currentPage: currentPage.value,
          sitesCount: sites.value.length
        })
      } catch (error) {
        console.error('[Sites][Data] Erreur lors du chargement des sites:', error)
        sites.value = []
        totalSites.value = 0
      } finally {
        loading.value = false
      }
    }

    const fetchSiteEmployees = async (siteId: number): Promise<void> => {
      try {
        loadingEmployees.value = true
        const response = await sitesApi.getSiteEmployees(siteId)
        siteEmployees.value = response.data.results
      } catch (error: unknown) {
        console.error('Erreur lors du chargement des employés:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    const fetchAvailableEmployees = async (): Promise<void> => {
      try {
        loadingEmployees.value = true
        const response = await schedulesApi.getAvailableEmployees()
        
        const assignedEmployeeIds = selectedSchedule.value?.assigned_employees?.map(emp => emp.employee) || []
        
        availableEmployees.value = response.data.results
          .filter((employee: Employee) => {
            return !assignedEmployeeIds.includes(employee.id) && 
                   employee.organization === selectedSite.value?.organization
          })
          .map((employee: Employee) => ({
            ...employee,
            formatted_name: formatEmployeeName(employee)
          }))
      } catch (error: unknown) {
        console.error('Erreur lors du chargement des employés disponibles:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    const fetchOrganizations = async (): Promise<void> => {
      try {
        const response = await organizationsApi.getAllOrganizations()
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
      }
    }

    // Charger les managers
    const loadManagers = async () => {
      try {
        const response = await usersApi.getAllUsers({
          role: 'MANAGER',
          organization: siteForm.value.organization
        })
        managers.value = response.data.results.map((manager: any) => ({
          id: manager.id,
          name: `${manager.first_name} ${manager.last_name}`
        }))
      } catch (error) {
        console.error('Erreur lors du chargement des managers:', error)
      }
    }

    // Mettre à jour la liste des managers quand l'organisation change
    watch(() => siteForm.value.organization, async (newOrgId) => {
      if (newOrgId) {
        siteForm.value.manager = null // Réinitialiser le manager sélectionné
        await loadManagers()
      } else {
        managers.value = []
      }
    })

    // Validation du formulaire pour s'assurer que le manager appartient à l'organisation
    const validateManager = (managerId: number | null): boolean => {
      if (!managerId || !siteForm.value.organization) return false
      return managers.value.some(manager => manager.id === managerId)
    }

    // Actions sur les sites
    const viewSiteDetails = async (site: Site): Promise<void> => {
      router.push(`/dashboard/sites/${site.id}`);
    }

    const editSite = (site: Site): void => {
      editedItem.value = site
      siteForm.value = {
        name: site.name || '',
        address: site.address || '',
        postal_code: site.postal_code || '',
        city: site.city || '',
        country: site.country || 'France',
        nfcId: site.nfc_id ? site.nfc_id.split('-')[1].slice(1) : '',  // Extraire les 4 chiffres après S
        organization: site.organization || null,
        manager: site.manager || null,
        late_margin: site.late_margin || 15,
        early_departure_margin: site.early_departure_margin || 15,
        ambiguous_margin: site.ambiguous_margin || 20,
        alert_emails: site.alert_emails || '',
        require_geolocation: site.require_geolocation ?? true,
        geolocation_radius: site.geolocation_radius || 100,
        allow_offline_mode: site.allow_offline_mode ?? true,
        max_offline_duration: site.max_offline_duration || 24,
        is_active: site.is_active ?? true
      }
      showCreateDialog.value = true
    }

    // Ajouter cette nouvelle méthode pour ouvrir le dialogue de création
    const openCreateDialog = (): void => {
      editedItem.value = null
      resetForm()
      showCreateDialog.value = true
    }

    const saveSite = async (): Promise<void> => {
      console.log('Starting site save process')
      try {
        if (!form.value) {
          console.warn('Form reference is null')
          return
        }
        
        console.log('Form current state:', form.value)
        console.log('Site form data:', siteForm.value)
        
        // Validation manuelle des champs requis
        if (!siteForm.value.name || !siteForm.value.address || !siteForm.value.postal_code || 
            !siteForm.value.city || !siteForm.value.organization) {
          console.warn('Form validation failed - missing required fields')
          return
        }

        saving.value = true
        const organization = organizations.value.find(org => org.id === siteForm.value.organization)
        console.log('Selected organization:', organization)
        
        if (!organization || !siteForm.value.organization) {
          console.error('Organization not found:', { 
            orgId: siteForm.value.organization, 
            availableOrgs: organizations.value 
          })
          throw new Error('Organisation non trouvée')
        }

        const siteData = {
          name: siteForm.value.name,
          address: siteForm.value.address,
          postal_code: siteForm.value.postal_code,
          city: siteForm.value.city,
          country: siteForm.value.country,
          organization: siteForm.value.organization,
          manager: siteForm.value.manager,
          late_margin: parseInt(siteForm.value.late_margin.toString()),
          early_departure_margin: parseInt(siteForm.value.early_departure_margin.toString()),
          ambiguous_margin: parseInt(siteForm.value.ambiguous_margin.toString()),
          alert_emails: siteForm.value.alert_emails,
          require_geolocation: siteForm.value.require_geolocation,
          geolocation_radius: parseInt(siteForm.value.geolocation_radius.toString()),
          allow_offline_mode: siteForm.value.allow_offline_mode,
          max_offline_duration: parseInt(siteForm.value.max_offline_duration.toString()),
          is_active: siteForm.value.is_active
        }
        console.log('Prepared site data:', siteData)
        
        if (editedItem.value) {
          console.log('Updating existing site:', editedItem.value.id)
          await sitesApi.updateSite(editedItem.value.id, siteData)
        } else {
          console.log('Creating new site')
          await sitesApi.createSite(siteData)
        }
        await fetchSites(currentPage.value)
        closeDialog()
      } catch (error) {
        console.error('Detailed error in saveSite:', error)
        if (error instanceof Error) {
          console.error('Error message:', error.message)
          console.error('Error stack:', error.stack)
        }
      } finally {
        saving.value = false
      }
    }

    const deleteSite = (site: Site): void => {
      siteToDelete.value = site
      showDeleteDialog.value = true
    }

    const confirmDeleteSite = async (): Promise<void> => {
      if (!siteToDelete.value) return
      
      try {
        deleting.value = true
        await sitesApi.deleteSite(siteToDelete.value.id)
        await fetchSites(currentPage.value, itemsPerPage.value)
        showDeleteDialog.value = false
        siteToDelete.value = null
      } catch (error) {
        console.error('Erreur lors de la suppression du site:', error)
      } finally {
        deleting.value = false
      }
    }

    // Actions sur les plannings
    const showCreateScheduleDialog = (): void => {
      selectedSchedule.value = null
      resetScheduleForm()
      showScheduleDialog.value = true
    }

    const viewScheduleDetails = (schedule: Schedule): void => {
      selectedScheduleForCalendar.value = schedule
      showCalendarDialog.value = true
    }

    const editSchedule = (schedule: Schedule): void => {
      selectedSchedule.value = schedule
      const defaultForm: ScheduleForm = {
        name: schedule.name,
        schedule_type: schedule.schedule_type,
        min_daily_hours: 0,
        min_weekly_hours: 0,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: 30,
        late_departure_limit: 30,
        break_duration: 60,
        min_break_start: '09:00',
        max_break_end: '17:00',
        days: initScheduleDays(),
        frequency_hours: 0,
        frequency_type: 'DAILY',
        frequency_count: 1,
        time_window: 8
      }

      if (schedule.schedule_type === 'FIXED') {
        scheduleForm.value = {
          ...defaultForm,
          min_daily_hours: schedule.min_daily_hours || 0,
          min_weekly_hours: schedule.min_weekly_hours || 0,
          allow_early_arrival: schedule.allow_early_arrival || false,
          allow_late_departure: schedule.allow_late_departure || false,
          early_arrival_limit: schedule.early_arrival_limit || 30,
          late_departure_limit: schedule.late_departure_limit || 30,
          break_duration: schedule.break_duration || 60,
          min_break_start: schedule.min_break_start || '09:00',
          max_break_end: schedule.max_break_end || '17:00',
          days: schedule.details ? schedule.details.map(detail => ({
            enabled: true,
            start_time_1: detail.start_time_1 || '08:00',
            end_time_1: detail.end_time_1 || '12:00',
            start_time_2: detail.start_time_2 || '14:00',
            end_time_2: detail.end_time_2 || '18:00'
          })) : initScheduleDays()
        }
      } else {
        scheduleForm.value = {
          ...defaultForm,
          frequency_hours: schedule.frequency_hours || 0,
          frequency_type: schedule.frequency_type || 'DAILY',
          frequency_count: schedule.frequency_count || 1,
          time_window: schedule.time_window || 8
        }
      }
      showScheduleDialog.value = true
    }

    const deleteSchedule = async (schedule: Schedule): Promise<void> => {
      if (!selectedSite.value) return
      try {
        await sitesApi.deleteSchedule(selectedSite.value.id, schedule.id)
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
      } catch (error) {
        console.error('Erreur lors de la suppression du planning:', error)
      }
    }

    // Utilitaires
    const handleTableUpdate = (options: any): void => {
      console.log('Table options updated:', options)
      const { page, itemsPerPage: newItemsPerPage } = options
      console.log('Pagination values:', { page, newItemsPerPage })
      fetchSites(page, newItemsPerPage)
    }

    const closeDialog = (): void => {
      showCreateDialog.value = false
      showScheduleDialog.value = false
      showAssignDialog.value = false
      editedItem.value = null
      selectedSchedule.value = null
      employeeForm.value = {
        employee: null,
        schedule: null
      }
      resetScheduleForm()
    }

    const onDialogClose = (val: boolean): void => {
      if (!val) {
        editedItem.value = null
        resetForm()
      }
    }

    const resetForm = (): void => {
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
        manager: null,
        late_margin: 15,
        early_departure_margin: 15,
        ambiguous_margin: 20,
        alert_emails: '',
        require_geolocation: true,
        geolocation_radius: 100,
        allow_offline_mode: true,
        max_offline_duration: 24,
        is_active: true
      }
    }

    const formatNfcId = (value: string): void => {
      if (!value) return
      // Ne garder que les chiffres
      const numbers = String(value).replace(/\D/g, '')
      // Limiter à 4 chiffres
      siteForm.value.nfcId = numbers.substring(0, 4)
    }

    // Méthodes pour la gestion des employés
    const showAssignEmployeeDialog = (schedule: Schedule): void => {
      selectedSchedule.value = schedule
      showAssignDialog.value = true
      fetchAvailableEmployees()
    }

    const unassignEmployeeFromSchedule = async (scheduleId: number, employeeId: number): Promise<void> => {
      if (!selectedSite.value) return
      
      try {
        await schedulesApi.unassignEmployee(selectedSite.value.id, scheduleId, employeeId)
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
      } catch (error) {
        console.error('Erreur lors de la désassignation de l\'employé:', error)
      }
    }

    const assignEmployee = async (): Promise<void> => {
      if (!employeeForm.value.employee || !selectedSchedule.value || !selectedSite.value) {
        console.log('Formulaire incomplet')
        return
      }

      const selectedEmployee = availableEmployees.value.find(emp => emp.id === employeeForm.value.employee)
      if (!selectedEmployee || selectedEmployee.organization !== selectedSite.value.organization) {
        console.error('L\'employé doit appartenir à la même organisation que le site')
        return
      }

      saving.value = true
      try {
        await schedulesApi.assignEmployee(
          selectedSite.value.id,
          selectedSchedule.value.id,
          employeeForm.value.employee
        )

        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
        
        showAssignDialog.value = false
        employeeForm.value.employee = null
      } catch (error) {
        console.error('Erreur lors de l\'assignation de l\'employé:', error)
        if (error && typeof error === 'object' && 'response' in error && error.response && typeof error.response === 'object' && 'data' in error.response) {
          console.error('Détails de l\'erreur:', error.response.data)
        }
      } finally {
        saving.value = false
      }
    }

    const saveSchedule = async (): Promise<void> => {
      if (!scheduleFormRef.value || !selectedSite.value) return
      const { valid } = await scheduleFormRef.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const scheduleData: ScheduleForm = {
          name: scheduleForm.value.name,
          schedule_type: scheduleForm.value.schedule_type,
          min_daily_hours: scheduleForm.value.min_daily_hours,
          min_weekly_hours: scheduleForm.value.min_weekly_hours,
          allow_early_arrival: scheduleForm.value.allow_early_arrival,
          allow_late_departure: scheduleForm.value.allow_late_departure,
          early_arrival_limit: scheduleForm.value.early_arrival_limit,
          late_departure_limit: scheduleForm.value.late_departure_limit,
          break_duration: scheduleForm.value.break_duration,
          min_break_start: scheduleForm.value.min_break_start,
          max_break_end: scheduleForm.value.max_break_end,
          days: scheduleForm.value.days,
          frequency_hours: scheduleForm.value.frequency_hours,
          frequency_type: scheduleForm.value.frequency_type,
          frequency_count: scheduleForm.value.frequency_count,
          time_window: scheduleForm.value.time_window
        }

        if (scheduleForm.value.schedule_type === 'FIXED') {
          Object.assign(scheduleData, {
            min_daily_hours: parseFloat(scheduleForm.value.min_daily_hours.toString()) || 0,
            min_weekly_hours: parseFloat(scheduleForm.value.min_weekly_hours.toString()) || 0,
            allow_early_arrival: scheduleForm.value.allow_early_arrival,
            allow_late_departure: scheduleForm.value.allow_late_departure,
            early_arrival_limit: parseInt(scheduleForm.value.early_arrival_limit.toString()) || 30,
            late_departure_limit: parseInt(scheduleForm.value.late_departure_limit.toString()) || 30,
            break_duration: parseInt(scheduleForm.value.break_duration.toString()) || 60,
            min_break_start: scheduleForm.value.min_break_start,
            max_break_end: scheduleForm.value.max_break_end,
            details: scheduleForm.value.days
              .map((day, index) => day.enabled ? {
                day_of_week: weekDays[index].value,
                start_time_1: day.start_time_1,
                end_time_1: day.end_time_1,
                start_time_2: day.start_time_2,
                end_time_2: day.end_time_2
              } : null)
              .filter(Boolean)
          })
        } else {
          Object.assign(scheduleData, {
            frequency_hours: parseFloat(scheduleForm.value.frequency_hours.toString()) || 0,
            frequency_type: scheduleForm.value.frequency_type,
            frequency_count: parseInt(scheduleForm.value.frequency_count.toString()) || 1,
            time_window: parseInt(scheduleForm.value.time_window.toString()) || 8
          })
        }

        if (selectedSchedule.value?.id) {
          await sitesApi.updateSchedule(selectedSite.value.id, selectedSchedule.value.id, scheduleData)
        } else {
          await sitesApi.createSchedule(selectedSite.value.id, scheduleData)
        }

        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
        
        closeScheduleDialog()
      } catch (error: unknown) {
        console.error('Erreur lors de l\'enregistrement du planning:', error)
      } finally {
        saving.value = false
      }
    }

    const resetScheduleForm = (): void => {
      scheduleForm.value = {
        name: '',
        schedule_type: 'FIXED',
        min_daily_hours: 0,
        min_weekly_hours: 0,
        allow_early_arrival: false,
        allow_late_departure: false,
        early_arrival_limit: 30,
        late_departure_limit: 30,
        break_duration: 60,
        min_break_start: '09:00',
        max_break_end: '17:00',
        days: initScheduleDays(),
        frequency_hours: 0,
        frequency_type: 'DAILY',
        frequency_count: 1,
        time_window: 8
      }
    }

    const isScheduleFormValid = computed((): boolean => {
      return Boolean(scheduleForm.value.schedule_type)
    })

    const closeScheduleDialog = (): void => {
      showScheduleDialog.value = false
      selectedSchedule.value = null
      resetScheduleForm()
    }

    // Fonction commune pour générer le QR code stylisé
    const generateStyledQRCode = async (site: Site, options: {
      width?: number;
      height?: number;
      qrSize?: number;
      showFrame?: boolean;
      radius?: number;
    } = {}): Promise<string> => {
      console.log('[Sites][QR Code][generateStyledQRCode] Début de la génération pour le site:', site.name);
      console.log('[Sites][QR Code][generateStyledQRCode] Options:', options);
      console.log('[Sites][QR Code][generateStyledQRCode] Données du site:', { id: site.id, nfc_id: site.nfc_id, name: site.name });

      const {
        width = 500,
        height = 700,
        qrSize = 400,
        showFrame = true,
        radius = 20
      } = options;

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('[Sites][QR Code][generateStyledQRCode] Erreur: Impossible d\'obtenir le contexte du canvas');
        throw new Error('Could not get canvas context');
      }
      
      console.log('[Sites][QR Code][generateStyledQRCode] Canvas créé avec dimensions:', { width, height });
      canvas.width = width;
      canvas.height = height;

      // Fond blanc
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, width, height);

      // Générer le QR Code avec qrcode
      const qrData = JSON.stringify({
        type: 'PG_SITE',
        site_id: site.id,
        nfc_id: site.nfc_id,
        name: site.name
      });
      console.log('[Sites][QR Code][generateStyledQRCode] Données encodées dans le QR code:', qrData);

      try {
        console.log('[Sites][QR Code][generateStyledQRCode] Chargement du logo...');
        // Charger le logo
        const logo = new Image();
        await new Promise<void>((resolve, reject) => {
          logo.onload = () => {
            console.log('[Sites][QR Code][generateStyledQRCode] Logo chargé avec succès');
            resolve();
          };
          logo.onerror = (error) => {
            console.error('[Sites][QR Code][generateStyledQRCode] Erreur de chargement du logo:', error);
            reject(error);
          };
          logo.src = '/icons/logo.png';
        });

        // Calculer la taille du logo (20% de la taille du QR code)
        const logoSize = qrSize * 0.2;
        const logoAspectRatio = logo.width / logo.height;
        const logoWidth = logoSize;
        const logoHeight = logoSize / logoAspectRatio;
        console.log('[Sites][QR Code][generateStyledQRCode] Dimensions du logo calculées:', { logoWidth, logoHeight });

        // Générer le QR code avec une zone centrale transparente pour le logo
        console.log('[Sites][QR Code][generateStyledQRCode] Génération du QR code...');
        const qrCodeDataUrl = await QRCode.toDataURL(qrData, {
          width: qrSize,
          margin: 1,
          color: {
            dark: '#00346E',
            light: '#FFFFFF'
          }
        });
        console.log('[Sites][QR Code][generateStyledQRCode] QR code généré avec succès');

        const qrImage = new Image();
        await new Promise<void>((resolve, reject) => {
          qrImage.onload = () => {
            console.log('[Sites][QR Code][generateStyledQRCode] Image QR code chargée');
            resolve();
          };
          qrImage.onerror = (error) => {
            console.error('[Sites][QR Code][generateStyledQRCode] Erreur de chargement de l\'image QR code:', error);
            reject(error);
          };
          qrImage.src = qrCodeDataUrl;
        });

        const qrX = (width - qrSize) / 2;
        const qrY = showFrame ? 50 : 0;
        ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize);
        console.log('[Sites][QR Code][generateStyledQRCode] QR code dessiné sur le canvas');

        // Dessiner le logo au centre du QR code
        const logoX = qrX + (qrSize - logoWidth) / 2;
        const logoY = qrY + (qrSize - logoHeight) / 2;
        console.log('[Sites][QR Code][generateStyledQRCode] Position du logo calculée:', { logoX, logoY });

        // Créer un cercle blanc pour le fond du logo
        ctx.beginPath();
        ctx.arc(logoX + logoWidth/2, logoY + logoHeight/2, logoWidth/2 + 5, 0, Math.PI * 2);
        ctx.fillStyle = '#FFFFFF';
        ctx.fill();
        console.log('[Sites][QR Code][generateStyledQRCode] Fond blanc du logo créé');

        // Dessiner le logo
        ctx.drawImage(logo, logoX, logoY, logoWidth, logoHeight);
        console.log('[Sites][QR Code][generateStyledQRCode] Logo dessiné sur le canvas');

        if (showFrame) {
          console.log('[Sites][QR Code][generateStyledQRCode] Ajout du cadre et du texte');
          ctx.strokeStyle = '#F78C48';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(100, 480);
          ctx.lineTo(width - 100, 480);
          ctx.stroke();

          // Configuration du texte
          ctx.fillStyle = '#F78C48';
          ctx.font = 'bold 24px Arial';
          ctx.textAlign = 'center';
          
          // Calculer la largeur maximale disponible pour le texte
          const maxWidth = width - 100;
          
          // Fonction pour découper le texte en lignes
          const getLines = (text: string, maxWidth: number): string[] => {
            const words = text.split(' ');
            const lines = [];
            let currentLine = words[0];

            for (let i = 1; i < words.length; i++) {
              const word = words[i];
              const width = ctx.measureText(currentLine + ' ' + word).width;
              if (width < maxWidth) {
                currentLine += ' ' + word;
              } else {
                lines.push(currentLine);
                currentLine = word;
              }
            }
            lines.push(currentLine);
            return lines;
          };

          // Découper le texte en lignes
          const lines = getLines(site.name, maxWidth - 40);
          console.log('[Sites][QR Code][generateStyledQRCode] Texte découpé en lignes:', lines);
          
          // Calculer la hauteur totale du texte
          const lineHeight = 30;
          const totalHeight = lines.length * lineHeight;
          
          // Position de départ pour le texte
          let y = 530;
          
          // Ajuster la position verticale si nécessaire pour centrer le texte
          if (lines.length > 1) {
            y = y - (totalHeight / 2) + (lineHeight / 2);
          }
          
          // Dessiner chaque ligne
          lines.forEach((line, index) => {
            ctx.fillText(line, width / 2, y + (index * lineHeight));
          });
          console.log('[Sites][QR Code][generateStyledQRCode] Texte ajouté au canvas');
        }

        console.log('[Sites][QR Code][generateStyledQRCode] Génération terminée avec succès');
        return canvas.toDataURL('image/png');
      } catch (error) {
        console.error('[Sites][QR Code][generateStyledQRCode] Erreur détaillée:', error);
        if (error instanceof Error) {
          console.error('[Sites][QR Code][generateStyledQRCode] Message:', error.message);
          console.error('[Sites][QR Code][generateStyledQRCode] Stack:', error.stack);
        }
        throw error;
      }
    };

    const generateQRCode = async (site: Site): Promise<void> => {
      console.log('[Sites][QR Code][generateQRCode] Début de la génération pour le site:', {
        id: site.id,
        name: site.name,
        hasQRCode: !!site.qr_code,
        qrCodeType: site.qr_code ? (site.qr_code.startsWith('data:') ? 'data URL' : 'autre format') : 'aucun'
      });
      
      try {
        // Toujours générer un nouveau QR code si inexistant ou au mauvais format
        if (!site.qr_code || !site.qr_code.startsWith('data:')) {
          console.log('[Sites][QR Code][generateQRCode] Génération d\'un nouveau QR code...');
          const qrCode = await generateStyledQRCode(site, {
            width: 500,
            height: 500,
            qrSize: 500,
            showFrame: false
          });
          console.log('[Sites][QR Code][generateQRCode] QR code généré avec succès, longueur:', qrCode.length);

          // Mettre à jour le QR code localement
          if (selectedSite.value && selectedSite.value.id === site.id) {
            console.log('[Sites][QR Code][generateQRCode] Mise à jour du QR code pour le site sélectionné');
            selectedSite.value.qr_code = qrCode;
          }

          // Mettre à jour le QR code dans la liste des sites
          const siteIndex = sites.value.findIndex(s => s.id === site.id);
          if (siteIndex !== -1) {
            console.log('[Sites][QR Code][generateQRCode] Mise à jour du QR code dans la liste des sites');
            sites.value[siteIndex].qr_code = qrCode;
          }
        } else {
          console.log('[Sites][QR Code][generateQRCode] QR code existant et valide, génération ignorée');
        }
      } catch (error: unknown) {
        console.error('[Sites][QR Code][generateQRCode] Erreur lors de la génération:', error);
        if (error instanceof Error) {
          console.error('[Sites][QR Code][generateQRCode] Message:', error.message);
          console.error('[Sites][QR Code][generateQRCode] Stack:', error.stack);
        }
        throw error;
      }
    };

    const downloadQRCode = async (site: Site): Promise<void> => {
      console.log('[Sites][QR Code][downloadQRCode] Début du téléchargement pour le site:', {
        id: site.id,
        name: site.name,
        hasQRCode: !!site.qr_code
      });
      
      try {
        // Toujours générer un nouveau QR code pour le téléchargement
        console.log('[Sites][QR Code][downloadQRCode] Génération du QR code pour le téléchargement...');
        const qrCode = await generateStyledQRCode(site, {
          width: 500,
          height: 700,
          qrSize: 400,
          showFrame: true
        });
        console.log('[Sites][QR Code][downloadQRCode] QR code généré avec succès');

        // Mettre à jour le QR code dans le site si nécessaire
        if (!site.qr_code) {
          console.log('[Sites][QR Code][downloadQRCode] Mise à jour du QR code manquant dans le site');
          if (selectedSite.value && selectedSite.value.id === site.id) {
            selectedSite.value.qr_code = qrCode;
          }
          const siteIndex = sites.value.findIndex(s => s.id === site.id);
          if (siteIndex !== -1) {
            sites.value[siteIndex].qr_code = qrCode;
          }
        }

        const fileName = `qr-code-${site.name.toLowerCase().replace(/\s+/g, '-')}.png`;
        console.log('[Sites][QR Code][downloadQRCode] Nom du fichier:', fileName);

        const link = document.createElement('a');
        link.href = qrCode;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        console.log('[Sites][QR Code][downloadQRCode] Téléchargement initié');
      } catch (error) {
        console.error('[Sites][QR Code][downloadQRCode] Erreur détaillée:', error);
        if (error instanceof Error) {
          console.error('[Sites][QR Code][downloadQRCode] Message:', error.message);
          console.error('[Sites][QR Code][downloadQRCode] Stack:', error.stack);
        }
      }
    };

    const toggleSiteStatus = async (site: ExtendedSite): Promise<void> => {
      try {
        site.isUpdating = true
        const updatedSite = await sitesApi.updateSite(site.id, {
          is_active: !site.is_active
        })
        
        // Mettre à jour le site dans la liste
        const index = sites.value.findIndex(s => s.id === site.id)
        if (index !== -1) {
          sites.value[index] = updatedSite.data
        }
        
        // Si le site est actuellement sélectionné, mettre à jour aussi selectedSite
        if (selectedSite.value?.id === site.id) {
          selectedSite.value = updatedSite.data
        }
      } catch (error) {
        console.error('Erreur lors de la modification du statut du site:', error)
      } finally {
        site.isUpdating = false
      }
    }

    // Charger les données initiales
    onMounted(async () => {
      await Promise.all([
        fetchSites(),
        fetchOrganizations(),
        loadManagers()
      ])
    })
    
    const formValid = computed(() => {
      return form.value?.valid ?? false
    })

    // Dans la section script, ajouter la computed property pour la prévisualisation
    const nfcIdPreview = computed(() => {
      if (!siteForm.value.organization || !siteForm.value.nfcId) return ''
      const org = organizations.value.find(o => o.id === siteForm.value.organization)
      if (!org) return ''
      return `${org.org_id}-S${siteForm.value.nfcId.padStart(4, '0')}`
    })
    
    return {
      // États
      loading,
      saving,
      deleting,
      showDeleteDialog,
      siteToDelete,
      showCreateDialog,
      showScheduleDialog,
      showEmployeeDialog,
      showAssignDialog,
      selectedSchedule,
      form,
      formValid,
      scheduleForm,
      scheduleFormRef,
      employeeForm,
      siteForm,
      organizations,
      managers,
      selectedSite,
      activeTab,
      loadingSchedules,
      loadingTimesheets,
      loadingAnomalies,
      loadingReports,
      siteEmployees,
      availableEmployees,
      formatEmployeeName,

      // Données
      headers,
      scheduleHeaders,
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
      saveSchedule,
      showAssignEmployeeDialog,
      assignEmployee,
      unassignEmployeeFromSchedule,
      showCreateScheduleDialog,
      openCreateDialog,
      loadManagers,  // Ajout de loadManagers ici

      // Nouvelles données
      showCalendarDialog,
      selectedScheduleForCalendar,
      isScheduleFormValid,
      closeScheduleDialog,

      // Jours de la semaine
      weekDays,
      // Fonctions pour la gestion des QR codes
      generateQRCode,
      downloadQRCode,
      toggleSiteStatus,
      confirmDeleteSite,
      nfcIdPreview,
      formatPhoneNumber,
      formatAddressForMaps
    }
  }
})
</script>

<style scoped>
.white-space-pre-wrap {
  white-space: pre-wrap !important;
}

.v-data-table {
  border-radius: 8px;
}

.schedule-type-select {
  z-index: 1000;
}

:deep(.v-select-list) {
  z-index: 1001;
}

.v-card {
  border-radius: 8px;
}

.v-card.outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.mr-2 {
  margin-right: 8px;
}

.qr-code-card {
  height: 100%;
}

.qr-code-container {
  padding: 16px;
}

.v-img.mx-auto {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  padding: 8px;
}

/* Styles pour les boutons d'action */
:deep(.v-btn--icon) {
  background-color: transparent !important;
}

:deep(.v-btn--icon .v-icon) {
  color: inherit !important;
  opacity: 1 !important;
}

:deep(.v-data-table .v-btn--icon) {
  margin: 0 4px;
}

:deep(.v-btn--icon.v-btn--density-default) {
  width: 36px;
  height: 36px;
}

:deep(.v-btn--icon.v-btn--size-small) {
  width: 32px;
  height: 32px;
}

/* Style des boutons colorés */
:deep(.v-btn--icon[color="#00346E"]) {
  color: #00346E !important;
}

:deep(.v-btn--icon[color="#F78C48"]) {
  color: #F78C48 !important;
}

:deep(.v-btn--icon[color="error"]) {
  color: rgb(var(--v-theme-error)) !important;
}

/* Style des boutons normaux */
:deep(.v-btn:not(.v-btn--icon)) {
  font-weight: 500;
  letter-spacing: 0.0892857143em;
}

:deep(.v-btn[color="#00346E"]:not(.v-btn--icon)) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="#F78C48"]:not(.v-btn--icon)) {
  background-color: #F78C48 !important;
  color: white !important;
}
</style>
