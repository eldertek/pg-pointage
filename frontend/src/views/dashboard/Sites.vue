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
          <template #[`item.address`]="{ item }">
            {{ item.address }}<br>
            {{ item.postal_code }} {{ item.city }}<br>
            {{ item.country }}
          </template>

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
                      <v-list-item-subtitle>{{ selectedSite.organization }}</v-list-item-subtitle>
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
                :items="selectedSite.schedules || []"
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
                        :key="employee.id"
                        class="mr-1 mb-1"
                        closable
                        @click:close="unassignEmployeeFromSchedule(item.id, employee.id)"
                      >
                        {{ employee.employee_name }}
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
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.late_margin"
                  label="Marge de retard (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de retard est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.early_departure_margin"
                  label="Marge de départ anticipé (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge de départ anticipé est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="siteForm.ambiguous_margin"
                  label="Marge pour cas ambigus (minutes)"
                  type="number"
                  required
                  :rules="[v => !!v || 'La marge pour cas ambigus est requise']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="siteForm.alert_emails"
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
                  :no-data-text="'Aucune franchise disponible'"
                ></v-select>
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
                  :rules="[v => !!v || 'Le rayon de géolocalisation est requis']"
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
                  :rules="[v => !!v || 'La durée maximale hors ligne est requise']"
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
                  <v-text-field
                    v-model="scheduleForm.name"
                    label="Nom du planning*"
                    :rules="[v => !!v || 'Le nom est requis']"
                    hide-details="auto"
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <v-radio-group
                    v-model="scheduleForm.schedule_type"
                    label="Type de planning*"
                    :rules="[v => !!v || 'Le type est requis']"
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
                      :rules="[v => !!v || 'Les heures minimales par jour sont requises']"
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
                      :rules="[v => !!v || 'Les heures minimales par semaine sont requises']"
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
                            :rules="[v => !!v || 'La limite d\'arrivée en avance est requise']"
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
                            :rules="[v => !!v || 'La limite de départ en retard est requise']"
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
                            :rules="[v => !!v || 'La durée de la pause est requise']"
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
                            :rules="[v => !!v || 'L\'heure de début de pause est requise']"
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
                            :rules="[v => !!v || 'L\'heure de fin de pause est requise']"
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
                            :rules="[v => !!v || 'Le nombre d\'heures par passage est requis']"
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
                            :rules="[v => !!v || 'Le type de fréquence est requis']"
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
                            :rules="[v => !!v || 'Le nombre de passages est requis']"
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
                              v => !!v || 'La plage horaire est requise',
                              v => v <= 24 || 'La plage horaire ne peut pas dépasser 24 heures'
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
                            <template v-if="scheduleForm.days.some(day => day.enabled)">
                              Planning actif {{ scheduleForm.days.filter(day => day.enabled).length }} jour{{ scheduleForm.days.filter(day => day.enabled).length > 1 ? 's' : '' }} 
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
                :rules="[v => !!v || 'L\'employé est requis']"
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

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { sitesApi, schedulesApi, organizationsApi } from '@/services/api'
import ScheduleCalendar from '@/components/ScheduleCalendar.vue'
import QRCode from 'qrcode'

export default {
  name: 'SitesView',
  components: {
    ScheduleCalendar
  },
  setup() {
    // Jours de la semaine
    const weekDays = [
      { text: 'Lundi', value: 1 },
      { text: 'Mardi', value: 2 },
      { text: 'Mercredi', value: 3 },
      { text: 'Jeudi', value: 4 },
      { text: 'Vendredi', value: 5 },
      { text: 'Samedi', value: 6 },
      { text: 'Dimanche', value: 0 }
    ]

    // Initialisation du formulaire de planning
    const initScheduleDays = () => {
      return weekDays.map(() => ({
        enabled: false,
        start_time_1: '08:00',
        end_time_1: '12:00',
        start_time_2: '14:00',
        end_time_2: '18:00'
      }))
    }

    // États généraux
    const loading = ref(true)
    const saving = ref(false)
    const showCreateDialog = ref(false)
    const showScheduleDialog = ref(false)
    const showEmployeeDialog = ref(false)
    const showAssignDialog = ref(false)
    const selectedSchedule = ref(null)
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
    const scheduleForm = ref({
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
    const scheduleFormRef = ref(null)
    const showCalendarDialog = ref(false)
    const selectedScheduleForCalendar = ref(null)

    // Formatage des données
    const formatEmployeeName = (employee) => {
      if (!employee) return ''
      return `${employee.first_name} ${employee.last_name} (${employee.email})`
    }

    // En-têtes des tableaux
    const headers = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'ID NFC', align: 'start', key: 'nfc_id' },
      { title: 'Franchise', align: 'start', key: 'organization' },
      { title: 'Statut', align: 'center', key: 'status' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const scheduleHeaders = ref([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Type', align: 'center', key: 'type' },
      { title: 'Employés', align: 'start', key: 'employees' },
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
        const response = await schedulesApi.getAvailableEmployees()
        
        // Filtrer les employés déjà assignés au planning sélectionné
        const assignedEmployeeIds = selectedSchedule.value.assigned_employees?.map(emp => emp.employee) || []
        
        // Ajouter le nom formaté à chaque employé et filtrer les employés déjà assignés
        availableEmployees.value = response.data.results
          .filter(employee => !assignedEmployeeIds.includes(employee.id))
          .map(employee => ({
            ...employee,
            formatted_name: formatEmployeeName(employee)
          }))
      } catch (error) {
        console.error('Erreur lors du chargement des employés disponibles:', error)
      } finally {
        loadingEmployees.value = false
      }
    }

    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.getAllOrganizations()
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
      }
    }

    // Actions sur les sites
    const viewSiteDetails = async (site) => {
      selectedSite.value = site
      activeTab.value = 'details'
      
      // Générer automatiquement le QR code si non existant
      if (!site.qr_code) {
        await generateQRCode(site)
      }
    }

    const editSite = (site) => {
      editedItem.value = site
      siteForm.value = {
        name: site.name || '',
        address: site.address || '',
        postal_code: site.postal_code || '',
        city: site.city || '',
        country: site.country || 'France',
        nfcId: site.nfc_id?.replace('PG', '') || '',
        organization: site.organization || null,
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

    const saveSite = async () => {
      if (!form.value) return
      const { valid } = await form.value.validate()
      if (!valid) return

      saving.value = true
      try {
        const siteData = {
          name: siteForm.value.name,
          address: siteForm.value.address,
          postal_code: siteForm.value.postal_code,
          city: siteForm.value.city,
          country: siteForm.value.country,
          nfc_id: 'PG' + siteForm.value.nfcId,
          organization: siteForm.value.organization,
          late_margin: parseInt(siteForm.value.late_margin),
          early_departure_margin: parseInt(siteForm.value.early_departure_margin),
          ambiguous_margin: parseInt(siteForm.value.ambiguous_margin),
          alert_emails: siteForm.value.alert_emails,
          require_geolocation: siteForm.value.require_geolocation,
          geolocation_radius: parseInt(siteForm.value.geolocation_radius),
          allow_offline_mode: siteForm.value.allow_offline_mode,
          max_offline_duration: parseInt(siteForm.value.max_offline_duration),
          is_active: siteForm.value.is_active
        }
        
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
    const showCreateScheduleDialog = () => {
      selectedSchedule.value = null
      resetScheduleForm()
      showScheduleDialog.value = true
    }

    const viewScheduleDetails = (schedule) => {
      selectedScheduleForCalendar.value = schedule
      showCalendarDialog.value = true
    }

    const editSchedule = (schedule) => {
      selectedSchedule.value = schedule
      scheduleForm.value = {
        name: schedule.name,
        schedule_type: schedule.schedule_type,
        ...(schedule.schedule_type === 'FIXED' ? {
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
        } : {
          frequency_hours: schedule.frequency_hours || 0,
          frequency_type: schedule.frequency_type || 'DAILY',
          frequency_count: schedule.frequency_count || 1,
          time_window: schedule.time_window || 8
        })
      }
      showScheduleDialog.value = true
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

    // Utilitaires
    const handleTableUpdate = (options) => {
      const { page, itemsPerPage: newItemsPerPage } = options
      fetchSites(page, newItemsPerPage)
    }

    const closeDialog = () => {
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

    const formatNfcId = (value) => {
      if (!value) {
        siteForm.value.nfcId = ''
        return
      }
      
      const numbers = String(value).replace(/\D/g, '')
      siteForm.value.nfcId = numbers.substring(0, 6)
    }

    // Méthodes pour la gestion des employés
    const showAssignEmployeeDialog = (schedule) => {
      selectedSchedule.value = schedule
      showAssignDialog.value = true
      fetchAvailableEmployees()
    }

    const unassignEmployeeFromSchedule = async (scheduleId, employeeId) => {
      if (!selectedSite.value) return
      
      try {
        await schedulesApi.unassignEmployee(selectedSite.value.id, scheduleId, employeeId)
        // Recharger les données du site pour mettre à jour la liste des employés
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
      } catch (error) {
        console.error('Erreur lors de la désassignation de l\'employé:', error)
      }
    }

    const assignEmployee = async () => {
      if (!employeeForm.value.employee || !selectedSchedule.value || !selectedSite.value) {
        console.log('Formulaire incomplet')
        return
      }

      saving.value = true
      try {
        await schedulesApi.assignEmployee(
          selectedSite.value.id,
          selectedSchedule.value.id,
          employeeForm.value.employee
        )

        // Recharger les données du site
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
        
        // Fermer le dialogue et réinitialiser le formulaire
        showAssignDialog.value = false
        employeeForm.value.employee = null
      } catch (error) {
        console.error('Erreur lors de l\'assignation de l\'employé:', error)
        if (error.response?.data) {
          console.error('Détails de l\'erreur:', error.response.data)
        }
      } finally {
        saving.value = false
      }
    }

    const saveSchedule = async () => {
      if (!scheduleFormRef.value) return
      const { valid } = await scheduleFormRef.value.validate()
      if (!valid || !selectedSite.value) return

      saving.value = true
      try {
        const scheduleData = {
          site: selectedSite.value.id,
          name: scheduleForm.value.name,
          schedule_type: scheduleForm.value.schedule_type,
        }

        // Ajouter les champs spécifiques selon le type de planning
        if (scheduleForm.value.schedule_type === 'FIXED') {
          Object.assign(scheduleData, {
            min_daily_hours: parseFloat(scheduleForm.value.min_daily_hours) || 0,
            min_weekly_hours: parseFloat(scheduleForm.value.min_weekly_hours) || 0,
            allow_early_arrival: scheduleForm.value.allow_early_arrival,
            allow_late_departure: scheduleForm.value.allow_late_departure,
            early_arrival_limit: parseInt(scheduleForm.value.early_arrival_limit) || 30,
            late_departure_limit: parseInt(scheduleForm.value.late_departure_limit) || 30,
            break_duration: parseInt(scheduleForm.value.break_duration) || 60,
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
            frequency_hours: parseFloat(scheduleForm.value.frequency_hours) || 0,
            frequency_type: scheduleForm.value.frequency_type,
            frequency_count: parseInt(scheduleForm.value.frequency_count) || 1,
            time_window: parseInt(scheduleForm.value.time_window) || 8
          })
        }

        console.log('Saving schedule with data:', scheduleData)

        if (selectedSchedule.value?.id) {
          await sitesApi.updateSchedule(selectedSite.value.id, selectedSchedule.value.id, scheduleData)
        } else {
          await sitesApi.createSchedule(selectedSite.value.id, scheduleData)
        }

        // Recharger les données du site
        const response = await sitesApi.getSite(selectedSite.value.id)
        selectedSite.value = response.data
        
        closeScheduleDialog()
      } catch (error) {
        console.error('Erreur lors de l\'enregistrement du planning:', error)
      } finally {
        saving.value = false
      }
    }

    const resetScheduleForm = () => {
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

    const isScheduleFormValid = computed(() => {
      return scheduleForm.value.name && scheduleForm.value.schedule_type
    })

    const closeScheduleDialog = () => {
      showScheduleDialog.value = false
      selectedSchedule.value = null
      resetScheduleForm()
    }

    // Fonctions pour la gestion des QR codes
    const generateQRCode = async (site) => {
      try {
        // Créer un objet avec les données nécessaires pour le scan
        const qrData = {
          type: 'PG_SITE',
          nfc_id: site.nfc_id,
          site_id: site.id,
          name: site.name
        }

        // Générer le QR code en base64 localement
        const qrCodeDataUrl = await QRCode.toDataURL(JSON.stringify(qrData), {
          width: 300,
          margin: 2,
          color: {
            dark: '#00346E',
            light: '#FFFFFF'
          }
        })

        // Mettre à jour le QR code localement sans l'envoyer au serveur
        selectedSite.value = {
          ...selectedSite.value,
          qr_code: qrCodeDataUrl
        }
      } catch (error) {
        console.error('Erreur lors de la génération du QR code:', error)
      }
    }

    const downloadQRCode = (site) => {
      if (!site.qr_code) return

      // Créer un lien temporaire pour le téléchargement
      const link = document.createElement('a')
      link.href = site.qr_code
      link.download = `qr-code-${site.name.toLowerCase().replace(/\s+/g, '-')}.png`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    onMounted(() => {
      fetchSites()
      fetchOrganizations()
    })
    
    return {
      // États
      loading,
      saving,
      showCreateDialog,
      showScheduleDialog,
      showEmployeeDialog,
      showAssignDialog,
      selectedSchedule,
      form,
      scheduleForm,
      scheduleFormRef,
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
    }
  }
}
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
</style>

