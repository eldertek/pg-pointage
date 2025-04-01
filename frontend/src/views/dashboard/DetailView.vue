<template>
  <v-container fluid>
    <!-- En-tête avec titre et actions -->
    <div class="d-flex align-center mb-4">
      <v-btn
        v-if="showBackButton"
        icon="mdi-arrow-left"
        variant="text"
        :to="backRoute"
        class="mr-4"
      ></v-btn>
      <Title :level="1" class="font-weight-bold">{{ title }}</Title>
      <v-spacer></v-spacer>
      <v-btn
        :color="isOwnProfile ? 'grey' : 'primary'"
        prepend-icon="mdi-pencil"
        class="mr-2"
        :disabled="isOwnProfile"
        @click.stop="editItem"
      >
        Modifier
      </v-btn>
      <v-btn
        v-if="allowDelete"
        :color="isOwnProfile ? 'grey' : 'error'"
        prepend-icon="mdi-delete"
        :disabled="isOwnProfile"
        @click.stop="confirmDelete"
      >
        Supprimer
        <v-tooltip v-if="isOwnProfile" activator="parent">
          Vous ne pouvez pas supprimer votre propre compte
        </v-tooltip>
      </v-btn>
    </div>

    <!-- Loader -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-col>
    </v-row>

    <template v-else>
      <!-- Vue détaillée du site avec onglets -->
      <template v-if="props.type === 'site'">
        <v-card>
          <v-tabs v-model="activeTab" color="#00346E">
            <v-tab value="details">Informations</v-tab>
            <v-tab value="employees">Employés</v-tab>
            <v-tab value="plannings">Plannings</v-tab>
            <v-tab value="pointages">Pointages</v-tab>
            <v-tab value="anomalies">Anomalies</v-tab>
            <v-tab value="reports">Rapports</v-tab>
          </v-tabs>

          <v-card-text>
            <v-window v-model="activeTab" :reverse="reverse">
              <!-- Onglet Informations -->
              <v-window-item value="details">
                <v-card class="elevation-1">
                  <v-toolbar flat>
                    <v-toolbar-title>Informations</v-toolbar-title>
                    <v-spacer></v-spacer>
                  </v-toolbar>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-list>
                          <template v-for="(field) in displayFields" :key="field.key || index">
                            <v-list-item>
                              <template #prepend>
                                <v-icon>{{ field.icon }}</v-icon>
                              </template>
                              <v-list-item-title>{{ field.label }}</v-list-item-title>
                              <v-list-item-subtitle>
                                <!-- Adresse avec carte -->
                                <template v-if="field.type === 'address' && isAddressField(field)">
                                  <AddressWithMap
                                    :address="item[field.address]"
                                    :postal-code="item[field.postalCode]"
                                    :city="item[field.city]"
                                    :country="item[field.country]"
                                  />
                                </template>
                                
                                <!-- Statut avec puce -->
                                <template v-else-if="field.type === 'status'">
                                  <StatusChip
                                    :status="item[field.key]"
                                    :active-label="field.activeLabel"
                                    :inactive-label="field.inactiveLabel"
                                  />
                                </template>

                                <!-- Rôle avec puce -->
                                <template v-else-if="field.type === 'role'">
                                  <v-chip
                                    :color="item[field.key] === 'MANAGER' ? 'primary' : 'success'"
                                    size="small"
                                  >
                                    {{ item[field.key] === 'MANAGER' ? 'Manager' : 'Employé' }}
                                  </v-chip>
                                </template>

                                <!-- Valeur par défaut -->
                                <template v-else>
                                  {{ formatFieldValue(field, item[field.key]) }}
                                </template>
                              </v-list-item-subtitle>
                            </v-list-item>
                          </template>
                        </v-list>
                      </v-col>

                      <v-col cols="12" md="6">
                        <!-- QR Code -->
                        <v-card class="qr-code-card" variant="outlined">
                          <v-card-title class="d-flex align-center">
                            <v-icon icon="mdi-qrcode" class="mr-2"></v-icon>
                            QR Code du site
                          </v-card-title>
                          <v-card-text class="text-center">
                            <div v-if="item.qr_code" class="qr-code-container">
                              <v-img
                                :src="item.qr_code"
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
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>
              <v-window-item value="employees">
                <DataTable
                  title="Employés"
                  :headers="employeesHeaders"
                  :items="employees"
                  :no-data-text="'Aucun employé trouvé'"
                  :detail-route="'/dashboard/admin/users/:id'"
                  :edit-route="'/dashboard/admin/users/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                  @delete="(item: TableItem) => handleDelete('employees', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.id}`)"
                >
                  <template #toolbar-actions>
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-account-plus"
                      @click="openAssignEmployeesDialog"
                    >
                      Assigner un employé
                    </v-btn>
                  </template>
                  
                  <template #item.is_active="{ item }">
                    <StatusChip :status="item.is_active" />
                  </template>
                  
                  <template #item.created_at="{ item }">
                    {{ formatDate(item.created_at) }}
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      :to="`/dashboard/admin/users/${item.id}`"
                      @click.stop
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="unassignEmployeeFromSite(item.id)"
                    >
                      <v-icon>mdi-account-remove</v-icon>
                      <v-tooltip activator="parent">Retirer du site</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Plannings -->
              <v-window-item value="plannings">
                <DataTable
                  title="Plannings"
                  :headers="planningsHeaders"
                  :items="item.schedules || []"
                  :no-data-text="'Aucun planning trouvé'"
                  :detail-route="'/dashboard/sites/:id/schedules/:id'"
                  :edit-route="'/dashboard/sites/:id/schedules/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('schedules', item)"
                  @delete="(item: TableItem) => handleDelete('schedules', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/sites/${itemId}/schedules/${item.id}`)"
                >
                  <template #item.schedule_type="{ item }">
                    <v-chip
                      :color="(item as ScheduleItem).schedule_type === 'FIXED' ? 'primary' : 'warning'"
                      size="small"
                    >
                      {{ (item as ScheduleItem).schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
                    </v-chip>
                  </template>

                  <template #item.site="{ item }">
                    {{ (item as ScheduleWithSite).site_name }}
                  </template>

                  <template #item.details="{ item }">
                    <div v-for="detail in (item as ScheduleWithSite).details" :key="detail.id" class="mb-1">
                      <strong>{{ getDayName(detail.day_of_week) }}:</strong>
                      <template v-if="(item as ScheduleWithSite).schedule_type === 'FIXED'">
                        <template v-if="detail.day_type === 'FULL'">
                          {{ detail.start_time_1 }}-{{ detail.end_time_1 }} / {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                        </template>
                        <template v-else-if="detail.day_type === 'AM'">
                          {{ detail.start_time_1 }}-{{ detail.end_time_1 }}
                        </template>
                        <template v-else-if="detail.day_type === 'PM'">
                          {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                        </template>
                      </template>
                      <template v-else>
                        {{ detail.frequency_duration }} minutes
                      </template>
                    </div>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Pointages -->
              <v-window-item value="pointages">
                <DataTable
                  title="Pointages"
                  :headers="pointagesHeaders"
                  :items="timesheets"
                  :no-data-text="'Aucun pointage trouvé'"
                  @row-click="(item: TableItem) => showTimesheetDetails(item)"
                >
                  <template #item.entry_type="{ item }">
                    <v-chip
                      :color="item.entry_type === 'ARRIVAL' ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ item.entry_type === 'ARRIVAL' ? 'Arrivée' : 'Départ' }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="item.status"
                      type="timesheet"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showTimesheetDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Anomalies -->
              <v-window-item value="anomalies">
                <DataTable
                  title="Anomalies"
                  :headers="anomaliesHeaders"
                  :items="anomalies"
                  :no-data-text="'Aucune anomalie trouvée'"
                  @row-click="(item: TableItem) => showAnomalyDetails(item)"
                >
                  <template #item.type="{ item }">
                    <v-chip
                      :color="getAnomalyTypeColor(item.anomaly_type_display)"
                      size="small"
                    >
                      {{ item.anomaly_type_display }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="item.status_display"
                      type="anomaly"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      v-if="item.status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="success"
                      @click.stop="handleResolveAnomaly(item)"
                    >
                      <v-icon>mdi-check</v-icon>
                      <v-tooltip activator="parent">Résoudre</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="item.status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="warning"
                      @click.stop="handleIgnoreAnomaly(item)"
                    >
                      <v-icon>mdi-eye-off</v-icon>
                      <v-tooltip activator="parent">Ignorer</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showAnomalyDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Rapports -->
              <v-window-item value="reports">
                <DataTable
                  title="Rapports"
                  :headers="reportsHeaders"
                  :items="reports as TableItem[]"
                  :no-data-text="'Aucun rapport trouvé'"
                  @row-click="(item: TableItem) => showReportDetails(item as ReportItem)"
                >
                  <template #item.type="{ item }">
                    <v-chip
                      :color="getReportTypeColor((item as ReportItem).report_type_display)"
                      size="small"
                    >
                      {{ (item as ReportItem).report_type_display }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="(item as ReportItem).status_display"
                      type="report"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="success"
                      @click.stop="handleApproveReport(item as ReportItem)"
                    >
                      <v-icon>mdi-check</v-icon>
                      <v-tooltip activator="parent">Approuver</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="handleRejectReport(item as ReportItem)"
                    >
                      <v-icon>mdi-close</v-icon>
                      <v-tooltip activator="parent">Rejeter</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showReportDetails(item as ReportItem)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </template>

      <!-- Vue détaillée de l'utilisateur avec onglets -->
      <template v-else-if="props.type === 'user'">
        <v-card>
          <v-tabs v-model="activeTab" color="#00346E">
            <v-tab value="details">Informations</v-tab>
            <v-tab value="sites">Sites</v-tab>
            <v-tab value="plannings">Plannings</v-tab>
            <v-tab value="pointages">Pointages</v-tab>
            <v-tab value="anomalies">Anomalies</v-tab>
            <v-tab value="reports">Rapports</v-tab>
          </v-tabs>

          <v-card-text>
            <v-window v-model="activeTab" :reverse="reverse">
              <!-- Onglet Informations -->
              <v-window-item value="details">
                <v-card class="elevation-1">
                  <v-toolbar flat>
                    <v-toolbar-title>Informations</v-toolbar-title>
                    <v-spacer></v-spacer>
                  </v-toolbar>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-list>
                          <template v-for="(field) in displayFields" :key="field.key || index">
                            <v-list-item>
                              <template #prepend>
                                <v-icon>{{ field.icon }}</v-icon>
                              </template>
                              <v-list-item-title>{{ field.label }}</v-list-item-title>
                              <v-list-item-subtitle>
                                <template v-if="field.type === 'status'">
                                  <StatusChip
                                    :status="item[field.key]"
                                    :active-label="field.activeLabel"
                                    :inactive-label="field.inactiveLabel"
                                  />
                                </template>
                                <template v-else-if="field.type === 'role'">
                                  <v-chip
                                    :color="item[field.key] === 'MANAGER' ? 'primary' : 'success'"
                                    size="small"
                                  >
                                    {{ item[field.key] === 'MANAGER' ? 'Manager' : 'Employé' }}
                                  </v-chip>
                                </template>
                                <template v-else>
                                  {{ formatFieldValue(field, item[field.key]) }}
                                </template>
                              </v-list-item-subtitle>
                            </v-list-item>
                          </template>
                        </v-list>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-card class="mb-4">
                          <v-card-title>Statistiques</v-card-title>
                          <v-card-text>
                            <v-row>
                              <template v-for="(stat) in statistics" :key="stat.label">
                                <v-col :cols="12 / statistics.length" class="text-center">
                                  <div class="text-h4">{{ stat.value }}</div>
                                  <div class="text-subtitle-1">{{ stat.label }}</div>
                                </v-col>
                              </template>
                            </v-row>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- Nouvel onglet Employés -->
              <v-window-item value="employees">
                <DataTable
                  title="Employés"
                  :headers="employeesHeaders"
                  :items="employees"
                  :no-data-text="'Aucun employé trouvé'"
                  :detail-route="'/dashboard/admin/users/:id'"
                  :edit-route="'/dashboard/admin/users/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                  @delete="(item: TableItem) => handleDelete('employees', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.id}`)"
                >
                  <template #toolbar-actions>
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-account-plus"
                      @click="openAssignEmployeesDialog"
                    >
                      Assigner un employé
                    </v-btn>
                  </template>
                  
                  <template #item.is_active="{ item }">
                    <StatusChip :status="item.is_active" />
                  </template>
                  
                  <template #item.created_at="{ item }">
                    {{ formatDate(item.created_at) }}
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      :to="`/dashboard/admin/users/${item.id}`"
                      @click.stop
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="unassignEmployeeFromSite(item.id)"
                    >
                      <v-icon>mdi-account-remove</v-icon>
                      <v-tooltip activator="parent">Retirer du site</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Pointages -->
              <v-window-item value="pointages">
                <DataTable
                  title="Pointages"
                  :headers="pointagesHeaders"
                  :items="timesheets"
                  :no-data-text="'Aucun pointage trouvé'"
                  @row-click="(item: TableItem) => showTimesheetDetails(item)"
                >
                  <template #item.entry_type="{ item }">
                    <v-chip
                      :color="item.entry_type === 'ARRIVAL' ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ item.entry_type === 'ARRIVAL' ? 'Arrivée' : 'Départ' }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="item.status"
                      type="timesheet"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showTimesheetDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Plannings -->
              <v-window-item value="plannings">
                <DataTable
                  title="Plannings"
                  :headers="schedulesHeaders"
                  :items="item.schedules || []"
                  :no-data-text="'Aucun planning trouvé'"
                  :detail-route="'/dashboard/sites/:id/schedules/:id'"
                  :edit-route="'/dashboard/sites/:id/schedules/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('schedules', item)"
                  @delete="(item: TableItem) => handleDelete('schedules', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/sites/${itemId}/schedules/${item.id}`)"
                >
                  <template #item.schedule_type="{ item }">
                    <v-chip
                      :color="(item as ScheduleItem).schedule_type === 'FIXED' ? 'primary' : 'warning'"
                      size="small"
                    >
                      {{ (item as ScheduleItem).schedule_type === 'FIXED' ? 'Fixe' : 'Fréquence' }}
                    </v-chip>
                  </template>

                  <template #item.site="{ item }">
                    {{ (item as ScheduleWithSite).site_name }}
                  </template>

                  <template #item.details="{ item }">
                    <div v-for="detail in (item as ScheduleWithSite).details" :key="detail.id" class="mb-1">
                      <strong>{{ getDayName(detail.day_of_week) }}:</strong>
                      <template v-if="(item as ScheduleWithSite).schedule_type === 'FIXED'">
                        <template v-if="detail.day_type === 'FULL'">
                          {{ detail.start_time_1 }}-{{ detail.end_time_1 }} / {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                        </template>
                        <template v-else-if="detail.day_type === 'AM'">
                          {{ detail.start_time_1 }}-{{ detail.end_time_1 }}
                        </template>
                        <template v-else-if="detail.day_type === 'PM'">
                          {{ detail.start_time_2 }}-{{ detail.end_time_2 }}
                        </template>
                      </template>
                      <template v-else>
                        {{ detail.frequency_duration }} minutes
                      </template>
                    </div>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Anomalies -->
              <v-window-item value="anomalies">
                <DataTable
                  title="Anomalies"
                  :headers="anomaliesHeaders"
                  :items="anomalies"
                  :no-data-text="'Aucune anomalie trouvée'"
                  @row-click="(item: TableItem) => showAnomalyDetails(item)"
                >
                  <template #item.type="{ item }">
                    <v-chip
                      :color="getAnomalyTypeColor(item.anomaly_type_display)"
                      size="small"
                    >
                      {{ item.anomaly_type_display }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="item.status_display"
                      type="anomaly"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      v-if="item.status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="success"
                      @click.stop="handleResolveAnomaly(item)"
                    >
                      <v-icon>mdi-check</v-icon>
                      <v-tooltip activator="parent">Résoudre</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="item.status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="warning"
                      @click.stop="handleIgnoreAnomaly(item)"
                    >
                      <v-icon>mdi-eye-off</v-icon>
                      <v-tooltip activator="parent">Ignorer</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showAnomalyDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Rapports -->
              <v-window-item value="reports">
                <DataTable
                  title="Rapports"
                  :headers="reportsHeaders"
                  :items="reports as TableItem[]"
                  :no-data-text="'Aucun rapport trouvé'"
                  @row-click="(item: TableItem) => showReportDetails(item as ReportItem)"
                >
                  <template #item.type="{ item }">
                    <v-chip
                      :color="getReportTypeColor((item as ReportItem).report_type_display)"
                      size="small"
                    >
                      {{ (item as ReportItem).report_type_display }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="(item as ReportItem).status_display"
                      type="report"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="success"
                      @click.stop="handleApproveReport(item as ReportItem)"
                    >
                      <v-icon>mdi-check</v-icon>
                      <v-tooltip activator="parent">Approuver</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="handleRejectReport(item as ReportItem)"
                    >
                      <v-icon>mdi-close</v-icon>
                      <v-tooltip activator="parent">Rejeter</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showReportDetails(item as ReportItem)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </template>

      <!-- Vue détaillée de l'organisation avec onglets -->
      <template v-else-if="props.type === 'organization'">
        <v-card>
          <v-tabs v-model="activeTab" color="#00346E">
            <v-tab value="details">Informations</v-tab>
            <v-tab value="sites">Sites</v-tab>
            <v-tab value="employees">Employés</v-tab>
            <v-tab value="reports">Rapports</v-tab>
          </v-tabs>

          <v-card-text>
            <v-window v-model="activeTab" :reverse="reverse">
              <!-- Onglet Informations -->
              <v-window-item value="details">
                <v-card class="elevation-1">
                  <v-toolbar flat>
                    <v-toolbar-title>Informations</v-toolbar-title>
                    <v-spacer></v-spacer>
                  </v-toolbar>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-list>
                          <template v-for="(field) in displayFields" :key="field.key || index">
                            <v-list-item>
                              <template #prepend>
                                <v-icon>{{ field.icon }}</v-icon>
                              </template>
                              <v-list-item-title>{{ field.label }}</v-list-item-title>
                              <v-list-item-subtitle>
                                <template v-if="field.type === 'address' && isAddressField(field)">
                                  <AddressWithMap
                                    :address="item[field.address]"
                                    :postal-code="item[field.postalCode]"
                                    :city="item[field.city]"
                                    :country="item[field.country]"
                                  />
                                </template>
                                <template v-else-if="field.type === 'status'">
                                  <StatusChip
                                    :status="item[field.key]"
                                    :active-label="field.activeLabel"
                                    :inactive-label="field.inactiveLabel"
                                  />
                                </template>
                                <template v-else>
                                  {{ formatFieldValue(field, item[field.key]) }}
                                </template>
                              </v-list-item-subtitle>
                            </v-list-item>
                          </template>
                        </v-list>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-card v-if="item.logo" class="mb-4">
                          <v-card-title>Logo</v-card-title>
                          <v-card-text class="text-center">
                            <v-img
                              :src="item.logo"
                              :alt="item.name"
                              max-width="200"
                              class="mx-auto"
                            ></v-img>
                          </v-card-text>
                        </v-card>
                        <v-card class="mb-4">
                          <v-card-title>Statistiques</v-card-title>
                          <v-card-text>
                            <v-row>
                              <template v-for="(stat) in statistics" :key="stat.label">
                                <v-col :cols="12 / statistics.length" class="text-center">
                                  <div class="text-h4">{{ stat.value }}</div>
                                  <div class="text-subtitle-1">{{ stat.label }}</div>
                                </v-col>
                              </template>
                            </v-row>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- Onglet Sites -->
              <v-window-item value="sites">
                <DataTable
                  title="Sites"
                  :headers="sitesHeaders"
                  :items="sites"
                  :no-data-text="'Aucun site trouvé'"
                  :detail-route="'/dashboard/sites/:id'"
                  :edit-route="'/dashboard/sites/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('sites', item)"
                  @delete="(item: TableItem) => handleDelete('sites', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/sites/${item.id}`)"
                >
                  <template #item.address="{ item }">
                    <AddressWithMap
                      :address="item.address"
                      :postal-code="item.postal_code"
                      :city="item.city"
                      :country="item.country"
                    />
                  </template>
                  
                  <template #item.is_active="{ item }">
                    <StatusChip :status="item.is_active" />
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Employés -->
              <v-window-item value="employees">
                <DataTable
                  title="Employés"
                  :headers="employeesHeaders"
                  :items="employees"
                  :no-data-text="'Aucun employé trouvé'"
                  :detail-route="'/dashboard/admin/users/:id'"
                  :edit-route="'/dashboard/admin/users/:id/edit'"
                  @toggle-status="(item: TableItem) => handleToggleStatus('employees', item)"
                  @delete="(item: TableItem) => handleDelete('employees', item)"
                  @row-click="(item: TableItem) => router.push(`/dashboard/admin/users/${item.id}`)"
                >
                  <template #toolbar-actions>
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-account-plus"
                      @click="openAssignEmployeesDialog"
                    >
                      Assigner un employé
                    </v-btn>
                  </template>
                  
                  <template #item.is_active="{ item }">
                    <StatusChip :status="item.is_active" />
                  </template>
                  
                  <template #item.created_at="{ item }">
                    {{ formatDate(item.created_at) }}
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      :to="`/dashboard/admin/users/${item.id}`"
                      @click.stop
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="unassignEmployeeFromSite(item.id)"
                    >
                      <v-icon>mdi-account-remove</v-icon>
                      <v-tooltip activator="parent">Retirer du site</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>

              <!-- Onglet Rapports -->
              <v-window-item value="reports">
                <DataTable
                  title="Rapports"
                  :headers="reportsHeaders"
                  :items="reports as TableItem[]"
                  :no-data-text="'Aucun rapport trouvé'"
                  @row-click="(item: TableItem) => showReportDetails(item as ReportItem)"
                >
                  <template #item.type="{ item }">
                    <v-chip
                      :color="getReportTypeColor((item as ReportItem).report_type_display)"
                      size="small"
                    >
                      {{ (item as ReportItem).report_type_display }}
                    </v-chip>
                  </template>
                  
                  <template #item.status="{ item }">
                    <StatusChip
                      :status="(item as ReportItem).status_display"
                      type="report"
                    />
                  </template>
                  
                  <template #item.actions="{ item }">
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="success"
                      @click.stop="handleApproveReport(item as ReportItem)"
                    >
                      <v-icon>mdi-check</v-icon>
                      <v-tooltip activator="parent">Approuver</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="(item as ReportItem).status === 'PENDING'"
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="handleRejectReport(item as ReportItem)"
                    >
                      <v-icon>mdi-close</v-icon>
                      <v-tooltip activator="parent">Rejeter</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click.stop="showReportDetails(item as ReportItem)"
                    >
                      <v-icon>mdi-eye</v-icon>
                      <v-tooltip activator="parent">Voir les détails</v-tooltip>
                    </v-btn>
                  </template>
                </DataTable>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </template>

      <!-- Vue détaillée standard pour les autres types -->
      <template v-else>
        <v-row>
          <!-- Informations principales -->
          <v-col cols="12" md="6">
            <v-card>
              <v-card-title>Informations générales</v-card-title>
              <v-card-text>
                <v-list>
                  <template v-for="(field) in displayFields" :key="field.key || index">
                    <v-list-item>
                      <template #prepend>
                        <v-icon>{{ field.icon }}</v-icon>
                      </template>
                      <v-list-item-title>{{ field.label }}</v-list-item-title>
                      <v-list-item-subtitle>
                        <!-- Adresse avec carte -->
                        <template v-if="field.type === 'address' && isAddressField(field)">
                          <AddressWithMap
                            :address="item[field.address]"
                            :postal-code="item[field.postalCode]"
                            :city="item[field.city]"
                            :country="item[field.country]"
                          />
                        </template>
                        
                        <!-- Statut avec puce -->
                        <template v-else-if="field.type === 'status'">
                          <StatusChip
                            :status="item[field.key]"
                            :active-label="field.activeLabel"
                            :inactive-label="field.inactiveLabel"
                          />
                        </template>

                        <!-- Rôle avec puce -->
                        <template v-else-if="field.type === 'role'">
                          <v-chip
                            :color="item[field.key] === 'MANAGER' ? 'primary' : 'success'"
                            size="small"
                          >
                            {{ item[field.key] === 'MANAGER' ? 'Manager' : 'Employé' }}
                          </v-chip>
                        </template>

                        <!-- Valeur par défaut -->
                        <template v-else>
                          {{ formatFieldValue(field, item[field.key]) }}
                        </template>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Statistiques et informations complémentaires -->
          <v-col cols="12" md="6">
            <!-- Statistiques -->
            <v-card class="mb-4">
              <v-card-title>Statistiques</v-card-title>
              <v-card-text>
                <v-row>
                  <template v-for="(stat) in statistics" :key="stat.label">
                    <v-col :cols="12 / statistics.length" class="text-center">
                      <div class="text-h4">{{ stat.value }}</div>
                      <div class="text-subtitle-1">{{ stat.label }}</div>
                    </v-col>
                  </template>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Logo (pour les organisations) -->
            <v-card v-if="item.logo" class="mb-4">
              <v-card-title>Logo</v-card-title>
              <v-card-text class="text-center">
                <v-img
                  :src="item.logo"
                  :alt="item.name"
                  max-width="200"
                  class="mx-auto"
                ></v-img>
              </v-card-text>
            </v-card>

            <!-- QR Code (uniquement pour les sites) -->
            <v-card v-if="props.type === 'site' && item.qr_code" class="qr-code-card mb-4" variant="outlined">
              <v-card-title class="d-flex align-center">
                <v-icon icon="mdi-qrcode" class="mr-2"></v-icon>
                QR Code du site
              </v-card-title>
              <v-card-text class="text-center">
                <div class="qr-code-container">
                  <v-img
                    :src="item.qr_code"
                    width="200"
                    height="200"
                    class="mx-auto mb-4"
                  ></v-img>
                  <div class="d-flex gap-2">
                    <v-btn
                      color="#00346E"
                      prepend-icon="mdi-download"
                      size="small"
                      @click="downloadQRCode"
                    >
                      Télécharger
                    </v-btn>
                    <v-btn
                      color="#F78C48"
                      prepend-icon="mdi-refresh"
                      size="small"
                      @click="generateQRCode"
                    >
                      Régénérer
                    </v-btn>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, markRaw, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Title } from '@/components/typography'
import AddressWithMap from '@/components/common/AddressWithMap.vue'
import AssignDialog from '@/components/common/AssignDialog.vue'
import { formatPhoneNumber } from '@/utils/formatters'
import { generateStyledQRCode } from '@/utils/qrcode'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { useAuthStore } from '@/stores/auth'
import { RoleEnum } from '@/types/api'
import { 
  sitesApi, 
  usersApi, 
  organizationsApi,
  timesheetsApi,
  reportsApi,
  type Site,
  type Schedule
} from '@/services/api'
import StatusChip from '@/components/common/StatusChip.vue'
import DataTable, { type TableItem } from '@/components/common/DataTable.vue'


interface ApiSiteEmployee {
  id: number;
  site: number;
  employee: number;
  employee_name: string;
  schedule: number | null;
  created_at: string;
  is_active: boolean;
}

interface SiteEmployee {
  id: number;
  site: number;
  employee: number;
  employee_name: string;
  schedule: number | null;
  created_at: string;
  is_active: boolean;
}

interface ScheduleWithSite extends Schedule {
  site_name: string;
}

// Types
interface Field {
  key: string;
  label: string;
  icon: string;
  type?: 'address' | 'status' | 'role' | 'default' | 'date';
  activeLabel?: string;
  inactiveLabel?: string;
  format?: 'phone' | 'date' | 'role' | 'scan_preference';
  dateFormat?: string;
  suffix?: string;
}

interface User {
  id: number;
  role: string;
  first_name: string;
  last_name: string;
  organization?: any;
  [key: string]: any;
}

interface AddressField extends Field {
  type: 'address';
  address: string;
  postalCode: string;
  city: string;
  country: string;
}

interface StatusField extends Field {
  type: 'status';
  activeLabel: string;
  inactiveLabel: string;
}

interface RoleField extends Field {
  type: 'role';
}

type DisplayField = Field | AddressField | StatusField | RoleField;

interface TableHeader {
  title: string;
  key: string;
  align?: 'start' | 'center' | 'end';
  sortable?: boolean;
}

interface TableSlot {
  key: string;
  component: any;
  props: any;
}

interface RelatedTable {
  key: string;
  title: string;
  items: TableItem[];
  headers: TableHeader[];
  addRoute?: string;
  addLabel?: string;
  noDataText?: string;
  slots?: TableSlot[];
  addAction?: () => void;
}

// Extended Site with additional properties needed for UI
interface ExtendedSite extends Omit<Site, 'schedules' | 'organization_name' | 'manager_name'> {
  schedules?: Schedule[];
  qr_code?: string;
  download_qr_code?: string;
  manager_name: string;
  organization_name: string;
}

// Type guard to ensure schedule data is properly typed

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value: string) => ['user', 'site', 'organization'].includes(value)
  },
  showBackButton: {
    type: Boolean,
    default: true
  },
  allowDelete: {
    type: Boolean,
    default: true
  }
})

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const deleting = ref(false)
const showDeleteDialog = ref(false)
const item = ref<any>({})
const statistics = ref<Array<{ label: string; value: number }>>([])
const relatedTables = ref<RelatedTable[]>([])
const auth = useAuthStore()
const showEditDialog = ref(false)
const showDeleteConfirmDialog = ref(false)
const dialogItem = ref<any>(null)
const dialogType = ref<string>('')
const unassignedEmployees = ref<any[]>([])
const unassignedSites = ref<any[]>([])
const loadingEmployees = ref(false)
const loadingSites = ref(false)
const assigningEmployee = ref(false)
const assigningSite = ref(false)
const showAssignEmployeesDialog = ref(false)
const showAssignSitesDialog = ref(false)

// Déclarer ces variables avant qu'elles ne soient utilisées dans resetState
const page = ref(1)
const activeTab = ref('details')
const previousTab = ref('details')
const reverse = ref(false)

const tabOrder = ['details', 'sites', 'plannings', 'pointages', 'anomalies', 'reports']

watch(activeTab, (newTab, oldTab) => {
  if (!oldTab || !newTab) return
  
  const oldIndex = tabOrder.indexOf(oldTab)
  const newIndex = tabOrder.indexOf(newTab)
  
  reverse.value = newIndex < oldIndex
  previousTab.value = oldTab
})
const timesheets = ref<Timesheet[]>([])
const anomalies = ref<Anomaly[]>([])
const reports = ref<Report[]>([])

// Ajout du snackbar
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Fonctions de notification
const showSuccess = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'success'
  }
}

const showError = (text: string) => {
  snackbar.value = {
    show: true,
    text,
    color: 'error'
  }
}

// Ajout des rôles
const roles = [
  { label: 'Super Admin', value: RoleEnum.SUPER_ADMIN },
  { label: 'Manager', value: RoleEnum.MANAGER },
  { label: 'Employé', value: RoleEnum.EMPLOYEE }
]

// Ajout des fonctions utilitaires
const getRoleColor = (role: RoleEnum | undefined) => {
  if (!role) return 'grey'
  switch (role) {
    case RoleEnum.SUPER_ADMIN:
      return 'error'
    case RoleEnum.MANAGER:
      return 'warning'
    case RoleEnum.EMPLOYEE:
      return 'success'
    default:
      return 'grey'
  }
}

const getRoleLabel = (role: RoleEnum | undefined) => {
  if (!role) return ''
  const found = roles.find(r => r.value === role)
  return found ? found.label : role
}

// Computed properties
const itemId = computed(() => Number(route.params.id))
const itemTypeLabel = computed(() => {
  switch (props.type) {
    case 'user': return "l'utilisateur"
    case 'site': return 'le site'
    case 'organization': return "l'organisation"
    default: return "l'élément"
  }
})

const title = computed(() => {
  switch (props.type) {
    case 'user': return "Détails de l'utilisateur"
    case 'site': return 'Détails du site'
    case 'organization': return "Détails de l'organisation"
    default: return 'Détails'
  }
})

const backRoute = computed(() => {
  switch (props.type) {
    case 'user': return '/dashboard/admin/users'
    case 'site': return '/dashboard/sites'
    case 'organization': return '/dashboard/organizations'
    default: return '/'
  }
})

// Configuration des champs à afficher selon le type
const roleLabels: Record<string, string> = {
  'SUPER_ADMIN': 'Super Administrateur',
  'ADMIN': 'Administrateur',
  'MANAGER': 'Manager',
  'EMPLOYEE': 'Employé'
}

const scanPreferenceLabels: Record<string, string> = {
  'BOTH': 'QR Code et NFC',
  'QR_CODE': 'QR Code uniquement',
  'NFC': 'NFC uniquement'
}

const displayFields = computed((): DisplayField[] => {
  switch (props.type) {
    case 'user': {
      const fields: DisplayField[] = [
        { key: 'first_name', label: 'Prénom', icon: 'mdi-account', type: 'default' },
        { key: 'last_name', label: 'Nom', icon: 'mdi-account-box', type: 'default' },
        { key: 'email', label: 'Email', icon: 'mdi-email', type: 'default' },
        { key: 'phone_number', label: 'Téléphone', icon: 'mdi-phone', type: 'default', format: 'phone' },
        { key: 'role', label: 'Rôle', icon: 'mdi-badge-account', type: 'default', format: 'role' }
      ]

      // Ajouter employee_id seulement s'il existe et n'est pas vide
      if (item.value?.employee_id) {
        fields.push({ key: 'employee_id', label: 'ID Employé', icon: 'mdi-card-account-details', type: 'default' })
      }

      return [
        ...fields,
        { key: 'scan_preference', label: 'Préférence de scan', icon: 'mdi-qrcode-scan', type: 'default', format: 'scan_preference' },
        { key: 'simplified_mobile_view', label: 'Vue mobile simplifiée', icon: 'mdi-cellphone',
          type: 'status',
          activeLabel: 'Activée',
          inactiveLabel: 'Désactivée'
        },
        { key: 'date_joined', label: 'Date d\'inscription', icon: 'mdi-calendar', type: 'default', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Actif',
          inactiveLabel: 'Inactif'
        }
      ]
    }
    case 'site': {
      return [
        { key: 'name', label: 'Nom', icon: 'mdi-domain' },
        { 
          type: 'address',
          label: 'Adresse',
          icon: 'mdi-map-marker',
          address: 'address',
          postalCode: 'postal_code',
          city: 'city',
          country: 'country',
          key: 'address'
        },
        { key: 'nfc_id', label: 'ID', icon: 'mdi-nfc' },
        { key: 'organization_name', label: 'Organisation', icon: 'mdi-domain' },
        { key: 'manager_name', label: 'Manager', icon: 'mdi-account-tie' },
        { key: 'late_margin', label: 'Marge de retard', icon: 'mdi-clock-alert', suffix: ' minutes' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Actif',
          inactiveLabel: 'Inactif'
        }
      ]
    }
    case 'organization': {
      return [
        { key: 'name', label: 'Nom', icon: 'mdi-domain' },
        { key: 'org_id', label: 'ID Organisation', icon: 'mdi-identifier' },
        {
          type: 'address',
          label: 'Adresse',
          icon: 'mdi-map-marker',
          address: 'address',
          postalCode: 'postal_code',
          city: 'city',
          country: 'country',
          key: 'address'
        },
        { key: 'phone', label: 'Téléphone', icon: 'mdi-phone', format: 'phone' },
        { key: 'contact_email', label: 'Email de contact', icon: 'mdi-email-outline' },
        { key: 'siret', label: 'SIRET', icon: 'mdi-card-account-details' },
        { key: 'notes', label: 'Notes', icon: 'mdi-note-text' },
        { key: 'created_at', label: 'Date de création', icon: 'mdi-calendar-plus', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { key: 'updated_at', label: 'Dernière modification', icon: 'mdi-calendar-clock', format: 'date', dateFormat: 'dd/MM/yyyy HH:mm' },
        { 
          key: 'is_active',
          label: 'Statut',
          icon: 'mdi-check-circle',
          type: 'status',
          activeLabel: 'Active',
          inactiveLabel: 'Inactive'
        }
      ]
    }
    default:
      return []
  }
})

// Type guard pour vérifier si un champ est de type adresse
const isAddressField = (field: DisplayField): field is AddressField => {
  return field.type === 'address'
}


// Méthodes
const loadData = async () => {
  loading.value = true
  try {
    switch (props.type) {
      case 'user': {
        const response = await usersApi.getUser(itemId.value);
        item.value = response.data;
        const stats = await usersApi.getUserStatistics(itemId.value);
        statistics.value = [
          { label: 'Heures totales', value: stats.data.total_hours || 0 },
          { label: 'Anomalies', value: stats.data.anomalies || 0 }
        ];
        break;
      }
      case 'site': {
        const siteResponse = await sitesApi.getSite(itemId.value)
        item.value = siteResponse.data
        const siteStats = await sitesApi.getSiteStatistics(itemId.value)
        statistics.value = [
          { label: 'Employés', value: siteStats.data.total_employees || 0 },
          { label: 'Heures totales', value: siteStats.data.total_hours || 0 },
          { label: 'Anomalies', value: siteStats.data.anomalies || 0 }
        ]
        // Charger les employés et les plannings pour les tableaux associés
        const [employeesResponse, schedulesResponse] = await Promise.all([
          sitesApi.getSiteEmployees(itemId.value),
          sitesApi.getSchedulesBySite(itemId.value)
        ])
        
        // Mettre à jour la liste des employés pour l'onglet Employés
        employees.value = (employeesResponse.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
          id: employee.id,
          site: employee.site,
          employee: employee.employee,
          employee_name: employee.employee_name,
          schedule: employee.schedule,
          created_at: employee.created_at,
          is_active: employee.is_active
        }))
        
        relatedTables.value = [
          {
            key: 'employees',
            title: 'Employés',
            items: (employeesResponse.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
              id: employee.id,
              site: employee.site,
              employee: employee.employee,
              employee_name: employee.employee_name,
              schedule: employee.schedule,
              created_at: employee.created_at,
              is_active: employee.is_active
            })),
            headers: [
              { title: 'ID', key: 'id' },
              { title: 'Nom', key: 'employee_name' },
              { title: 'Date d\'ajout', key: 'created_at' },
              { title: 'Statut', key: 'is_active' },
              { title: 'Actions', key: 'actions', sortable: false }
            ],
            addRoute: undefined,
            addLabel: 'Assigner un employé',
            addAction: openAssignEmployeesDialog,
            noDataText: 'Aucun employé trouvé',
            slots: [
              {
                key: 'role',
                component: 'v-chip',
                props: (item: any) => ({
                  color: getRoleColor(item.role),
                  size: 'small',
                  text: getRoleLabel(item.role)
                })
              }
            ]
          },
          {
            key: 'schedules',
            title: 'Plannings',
            items: schedulesResponse.data.results,
            headers: [
              { title: 'Nom', key: 'name' },
              { title: 'Type', key: 'schedule_type' },
              { title: 'Début', key: 'start_time' },
              { title: 'Fin', key: 'end_time' },
              { title: 'Actions', key: 'actions' }
            ],
            addRoute: `/dashboard/sites/${itemId.value}/schedules/new`,
            addLabel: 'Ajouter un planning',
            slots: [
              {
                key: 'schedule_type',
                component: 'v-chip',
                props: (item: any) => ({
                  color: item.schedule_type === 'FIXED' ? 'primary' : 'warning',
                  size: 'small',
                  text: item.schedule_type === 'FIXED' ? 'Fixe' : 'Variable'
                })
              },
              {
                key: 'start_time',
                component: 'span',
                props: (item: any) => ({
                  text: format(new Date(item.start_time), 'HH:mm', { locale: fr })
                })
              },
              {
                key: 'end_time',
                component: 'span',
                props: (item: any) => ({
                  text: format(new Date(item.end_time), 'HH:mm', { locale: fr })
                })
              }
            ]
          }
        ]
        break
      }
      case 'organization': {
        const orgResponse = await organizationsApi.getOrganization(itemId.value)
        item.value = orgResponse.data
        const orgStats = await organizationsApi.getOrganizationStatistics(itemId.value)
        statistics.value = [
          { label: 'Sites', value: orgStats.data.total_sites || 0 },
          { label: 'Employés', value: orgStats.data.total_employees || 0 },
          { label: 'Sites actifs', value: orgStats.data.active_sites || 0 }
        ]
        // Charger les sites et les employés pour les tableaux associés
        const [sitesResponse, orgEmployeesResponse] = await Promise.all([
          organizationsApi.getOrganizationSites(itemId.value, 1, 10),
          organizationsApi.getOrganizationUsers(itemId.value)
        ])
        relatedTables.value = [
          {
            key: 'sites',
            title: 'Sites',
            items: sitesResponse.data.results,
            headers: [
              { title: 'ID', key: 'id' },
              { title: 'Nom', key: 'name' },
              { title: 'Adresse', key: 'address' },
              { title: 'Ville', key: 'city' },
              { title: 'Statut', key: 'is_active' },
              { title: 'Actions', key: 'actions', sortable: false }
            ],
            addRoute: undefined,
            addLabel: 'Assigner un site',
            addAction: openAssignSitesDialog,
            noDataText: 'Aucun site trouvé',
            slots: [
              {
                key: 'address',
                component: markRaw(AddressWithMap),
                props: (item: any) => ({
                  address: item.address,
                  postal_code: item.postal_code,
                  city: item.city,
                  country: item.country
                })
              },
              {
                key: 'is_active',
                component: 'v-chip',
                props: (item: any) => ({
                  color: item.is_active ? 'success' : 'error',
                  size: 'small',
                  text: item.is_active ? 'Actif' : 'Inactif'
                })
              }
            ]
          },
          {
            key: 'employees',
            title: 'Employés',
            items: orgEmployeesResponse.data.results.map((employee: ApiSiteEmployee) => ({
              id: employee.id,
              site: employee.site,
              employee: employee.employee,
              employee_name: employee.employee_name,
              schedule: employee.schedule,
              created_at: employee.created_at,
              is_active: employee.is_active
            })),
            headers: [
              { title: 'ID', key: 'id' },
              { title: 'Nom', key: 'employee_name' },
              { title: 'Date d\'ajout', key: 'created_at' },
              { title: 'Statut', key: 'is_active' },
              { title: 'Actions', key: 'actions', sortable: false }
            ],
            addRoute: undefined,
            addLabel: 'Assigner un employé',
            addAction: openAssignEmployeesDialog,
            noDataText: 'Aucun employé trouvé',
            slots: [
              {
                key: 'role',
                component: 'v-chip',
                props: (item: any) => ({
                  color: getRoleColor(item.role),
                  size: 'small',
                  text: getRoleLabel(item.role)
                })
              }
            ]
          }
        ]
        break
      }
    }
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error)
  } finally {
    loading.value = false
  }
}

const formatFieldValue = (field: Field, value: any) => {
  if (!value) return ''
  if (field.format === 'phone') return formatPhoneNumber(value)
  if (field.format === 'date') {
    try {
      const date = new Date(value)
      return format(date, field.dateFormat || 'dd/MM/yyyy', { locale: fr })
    } catch (error) {
      console.error('Erreur lors du formatage de la date:', error)
      return value
    }
  }
  if (field.format === 'role') return roleLabels[value] || value
  if (field.format === 'scan_preference') return scanPreferenceLabels[value] || value
  if (field.suffix) return `${value}${field.suffix}`
  return value
}

const editItem = () => {
  if (isOwnProfile.value) {
    return
  }
  
  type RouteKey = 'user' | 'site' | 'organization'
  const editRoutes: Record<RouteKey, string> = {
    user: `/dashboard/admin/users/${itemId.value}/edit`,
    site: `/dashboard/sites/${itemId.value}/edit`,
    organization: `/dashboard/organizations/${itemId.value}/edit`
  }
  
  const editRoute = editRoutes[props.type as RouteKey]
  if (editRoute) {
    router.push(editRoute).catch(error => {
      console.error('[DetailView][Edit] Erreur lors de la redirection:', error)
    })
  } else {
    console.error('[DetailView][Edit] Route non trouvée pour le type:', props.type)
  }
}

const confirmDelete = () => {
  if (isOwnProfile.value) {
    return
  }
  showDeleteDialog.value = true
}

const deleteItem = async () => {
  
  deleting.value = true
  try {
    switch (props.type) {
      case 'user':
        await usersApi.deleteUser(itemId.value)
        await router.push('/dashboard/admin/users')
        break
      case 'site':
        await sitesApi.deleteSite(itemId.value)
        await router.push('/dashboard/sites')
        break
      case 'organization':
        await organizationsApi.deleteOrganization(itemId.value)
        await router.push('/dashboard/organizations')
        break
    }
  } catch (error) {
    console.error('[DetailView][Delete] Erreur lors de la suppression:', error)
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
  }
}


const formatDetailRoute = (tableKey: string, rowItem: TableItem): string => {
  const routes: Record<string, string> = {
    employees: `/dashboard/admin/users/${rowItem.id}`,
    sites: `/dashboard/sites/${rowItem.id}`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${rowItem.id}`
  }
  return routes[tableKey] || ''
}

const loadSiteDetails = async () => {
  try {
    loading.value = true
    const siteId = route.params.id
    
    // Charger les détails du site, les plannings et les employés en parallèle
    const [siteResponse, schedulesResponse, employeesResponse] = await Promise.all([
      sitesApi.getSite(Number(siteId)),
      sitesApi.getSchedulesBySite(Number(siteId)),
      sitesApi.getSiteEmployees(Number(siteId))
    ])

    // Mettre à jour la liste des employés
    employees.value = (employeesResponse.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
      id: employee.id,
      site: employee.site,
      employee: employee.employee,
      employee_name: employee.employee_name,
      schedule: employee.schedule,
      created_at: employee.created_at,
      is_active: employee.is_active
    }))

    // Fusionner les données du site avec les plannings
    item.value = {
      ...siteResponse.data,
      schedules: schedulesResponse.data.results || [],
      download_qr_code: '',
      manager_name: siteResponse.data.manager_name || '',
      organization_name: siteResponse.data.organization_name || ''
    } as ExtendedSite

    // Générer le QR code immédiatement après le chargement du site
    try {
      const previewQRCode = await generateStyledQRCode(item.value, {
        width: 500,
        height: 500,
        qrSize: 500,
        showFrame: false
      })
      
      const downloadQRCode = await generateStyledQRCode(item.value, {
        width: 500,
        height: 700,
        qrSize: 400,
        showFrame: true,
        radius: 20
      })
      
      item.value.qr_code = previewQRCode
      item.value.download_qr_code = downloadQRCode
    } catch (qrError) {
      console.error('[DetailView][LoadSite] Erreur lors de la génération du QR code:', qrError)
      showError('Erreur lors de la génération du QR code')
    }
    
    // Charger les statistiques et les tableaux associés
    try {
      // Charger les statistiques
      const siteStats = await sitesApi.getSiteStatistics(Number(siteId))
      statistics.value = [
        { label: 'Employés', value: siteStats.data.total_employees || 0 },
        { label: 'Heures totales', value: siteStats.data.total_hours || 0 },
        { label: 'Anomalies', value: siteStats.data.anomalies || 0 }
      ]
      
      // Charger les employés pour les tableaux associés
      const employeesResponse = await sitesApi.getSiteEmployees(Number(siteId))
      
      relatedTables.value = [
        {
          key: 'employees',
          title: 'Employés',
          items: (employeesResponse.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
            id: employee.id,
            site: employee.site,
            employee: employee.employee,
            employee_name: employee.employee_name,
            schedule: employee.schedule,
            created_at: employee.created_at,
            is_active: employee.is_active
          })),
          headers: [
            { title: 'ID', key: 'id' },
            { title: 'Nom', key: 'employee_name' },
            { title: 'Date d\'ajout', key: 'created_at' },
            { title: 'Statut', key: 'is_active' },
            { title: 'Actions', key: 'actions', sortable: false }
          ],
          addRoute: undefined,
          addLabel: 'Assigner un employé',
          addAction: openAssignEmployeesDialog,
          noDataText: 'Aucun employé trouvé',
          slots: [
            {
              key: 'role',
              component: 'v-chip',
              props: (item: any) => ({
                color: getRoleColor(item.role),
                size: 'small',
                text: getRoleLabel(item.role)
              })
            }
          ]
        }
      ]
    } catch (statsError) {
      console.error('[DetailView][LoadSite] Erreur lors du chargement des statistiques:', statsError)
      showError('Erreur lors du chargement des statistiques et des employés associés')
    }
    
  } catch (error) {
    console.error('[DetailView][LoadSite] Erreur lors du chargement des détails du site:', error)
    showError('Erreur lors du chargement des détails du site')
  } finally {
    loading.value = false
  }
}

const generateQRCode = async () => {
  if (!item.value) {
    showError('Impossible de générer le QR code : site non défini')
    return
  }

  try {
    const previewQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 500,
      qrSize: 500,
      showFrame: false
    })
    
    const downloadQRCode = await generateStyledQRCode(item.value, {
      width: 500,
      height: 700,
      qrSize: 400,
      showFrame: true,
      radius: 20
    })
    
    item.value.qr_code = previewQRCode
    item.value.download_qr_code = downloadQRCode
  } catch (error) {
    console.error('[DetailView][GenerateQRCode] Erreur lors de la génération du QR code:', error)
    showError('Erreur lors de la génération du QR code')
  }
}

const downloadQRCode = async () => {
  if (!item.value?.qr_code) {
    showError('QR code non disponible pour le téléchargement')
    return
  }

  try {
    const link = document.createElement('a')
    link.href = item.value.download_qr_code || item.value.qr_code
    const fileName = `qr-code-${item.value.name.toLowerCase().replace(/\s+/g, '-')}.png`
    link.download = fileName
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    showSuccess('Téléchargement du QR code initié')
  } catch (error) {
    console.error('[DetailView][DownloadQRCode] Erreur lors du téléchargement du QR code:', error)
    showError('Erreur lors du téléchargement du QR code')
  }
}



// Computed pour vérifier si c'est le profil de l'utilisateur connecté
const isOwnProfile = computed(() => {
  return props.type === 'user' && (auth.user as User)?.id === itemId.value
})

// Ajout des dialogues


const handleToggleStatus = async (tableKey: string, item: any) => {
  try {
    if (tableKey === 'sites') {
      await sitesApi.updateSite(item.id, { ...item, is_active: !item.is_active })
    } else if (tableKey === 'employees') {
      await usersApi.toggleUserStatus(item.id, !item.is_active)
    }
    await loadData()
  } catch (error) {
    console.error('[DetailView][ToggleStatus] Erreur lors du changement de statut:', error)
  }
}

const handleDelete = async (tableKey: string, item: any) => {
  if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
    return
  }

  try {
    if (tableKey === 'sites') {
      await sitesApi.deleteSite(item.id)
    } else if (tableKey === 'employees') {
      await usersApi.deleteUser(item.id)
    }
    await loadData()
  } catch (error) {
    console.error('[DetailView][Delete] Erreur lors de la suppression:', error)
  }
}

const saveDialogItem = async () => {
  try {
    if (dialogType.value === 'sites') {
      await sitesApi.updateSite(dialogItem.value.id, dialogItem.value)
    } else {
      await usersApi.updateUser(dialogItem.value.id, dialogItem.value)
    }
    showEditDialog.value = false
    await loadData()
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  }
}

const confirmDeleteDialogItem = async () => {
  try {
    if (dialogType.value === 'sites') {
      await sitesApi.deleteSite(dialogItem.value.id)
    } else {
      await usersApi.deleteUser(dialogItem.value.id)
    }
    showDeleteConfirmDialog.value = false
    await loadData()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const handleAssignEmployee = async (employee: any) => {
  assigningEmployee.value = true
  try {
    await sitesApi.assignEmployee(itemId.value, employee.id)
    
    // Recharger la liste des employés
    const response = await sitesApi.getSiteEmployees(itemId.value)
    employees.value = (response.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
      id: employee.id,
      site: employee.site,
      employee: employee.employee,
      employee_name: employee.employee_name,
      schedule: employee.schedule,
      created_at: employee.created_at,
      is_active: employee.is_active
    }))
    
    await loadData()
    showAssignEmployeesDialog.value = false
    showSuccess('Employé assigné avec succès')
  } catch (error) {
    console.error('[DetailView][AssignEmployee] Erreur lors de l\'assignation de l\'employé:', error)
    showError('Erreur lors de l\'assignation de l\'employé')
  } finally {
    assigningEmployee.value = false
  }
}

const handleAssignSite = async (site: any) => {
  assigningSite.value = true
  try {
    await organizationsApi.assignSite(itemId.value, site.id)
    await loadData()
    showAssignSitesDialog.value = false
  } catch (error) {
    console.error('[DetailView][AssignSite] Erreur lors de l\'assignation du site:', error)
  } finally {
    assigningSite.value = false
  }
}

const loadUnassignedEmployees = async () => {
  loadingEmployees.value = true
  try {
    // Si c'est un site, utiliser l'API des sites pour charger les employés non assignés
    if (props.type === 'site') {
      const response = await sitesApi.getUnassignedEmployees(itemId.value)
      unassignedEmployees.value = response.data.results || []
    } else {
      // Sinon, c'est une organisation
      const response = await organizationsApi.getUnassignedEmployees(itemId.value)
      unassignedEmployees.value = response.data.results || []
    }
  } catch (error) {
    console.error('[DetailView][LoadEmployees] Erreur lors du chargement des employés:', error)
    unassignedEmployees.value = []
  } finally {
    loadingEmployees.value = false
  }
}

const loadUnassignedSites = async () => {
  loadingSites.value = true
  try {
    const response = await organizationsApi.getUnassignedSites(itemId.value)
    unassignedSites.value = response.data.results || []
  } catch (error) {
    console.error('[DetailView][LoadSites] Erreur lors du chargement des sites:', error)
    unassignedSites.value = []
  } finally {
    loadingSites.value = false
  }
}

// Ouvrir le dialogue d'assignation des employés
const openAssignEmployeesDialog = async () => { 
  try {
    await loadUnassignedEmployees()
    showAssignEmployeesDialog.value = true
  } catch (error) {
    console.error('[DetailView][OpenDialog] Erreur lors de l\'ouverture du dialogue:', error)
  }
}

// Ouvrir le dialogue d'assignation des sites  
const openAssignSitesDialog = async () => {
  await loadUnassignedSites()
  showAssignSitesDialog.value = true
}

const formatEditRoute = (tableKey: string, item: TableItem): string => {
  const routes: Record<string, string> = {
    employees: `/dashboard/admin/users/${item.id}/edit`,
    sites: `/dashboard/sites/${item.id}/edit`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${item.id}/edit`
  }
  return routes[tableKey] || ''
}

// Nouvelle fonction navigateToDetail améliorée
const navigateToDetail = async (tableKey: string, rowData: any) => {
  const item = rowData.item?.raw || rowData.item?.value || rowData.item || rowData
  if (!item || !item.id) {
    return
  }

  const routes: Record<string, string> = {
    employees: `/dashboard/admin/users/${item.id}`,
    sites: `/dashboard/sites/${item.id}`,
    schedules: `/dashboard/sites/${route.params.id}/schedules/${item.id}`
  }
  
  const targetRoute = routes[tableKey]
  if (targetRoute) {
    await router.push(targetRoute)
  }
}

const resetState = () => {
  item.value = {}
  statistics.value = []
  relatedTables.value = []
  timesheets.value = []
  anomalies.value = []
  reports.value = []
  page.value = 1
  activeTab.value = 'details'
  showDeleteDialog.value = false
  showEditDialog.value = false
  showDeleteConfirmDialog.value = false
  showAssignEmployeesDialog.value = false
  showAssignSitesDialog.value = false
}

// Ajout des watchers pour la route et l'ID
watch(
  [() => route.params.id, () => props.type],
  async ([newId, newType], [oldId, oldType]) => {
    
    if (newId !== oldId || newType !== oldType) {
      resetState()
      
      loading.value = true
      try {
        if (props.type === 'site') {
          await loadSiteDetails()
        } else {
          await loadData()
        }
      } catch (error) {
        console.error('[DetailView][Watch] Erreur lors du rechargement des données:', error)
        showError('Erreur lors du chargement des données')
      } finally {
        loading.value = false
      }
    }
  },
  { immediate: true }
)

onMounted(async () => {
  if (props.type === 'site') {
    await loadSiteDetails()
  } else {
    await loadData()
  }
})

// Headers pour le tableau des plannings
const schedulesHeaders = ref([
  { title: 'Type', key: 'schedule_type', align: 'start' as const },
  { title: 'Site', key: 'site_name', align: 'start' as const },
  { title: 'Détails', key: 'details', align: 'start' as const },
  { title: 'Actions', key: 'actions', align: 'end' as const, sortable: false }
])

interface Timesheet {
  id: number;
  employee: string;
  entry_type: 'ARRIVAL' | 'DEPARTURE';
  timestamp: string;
  status: 'PENDING' | 'VALIDATED' | 'REJECTED';
  status_display: string;
}

interface Anomaly {
  id: number;
  employee: string;
  anomaly_type: string;
  anomaly_type_display: string;
  description: string;
  status: 'PENDING' | 'RESOLVED' | 'IGNORED';
  status_display: string;
  created_at: string;
}

interface Report {
  id: number;
  name: string;
  type: string;
  created_at: string;
  file_url: string;
}




const getAnomalyTypeColor = (type: string) => {
  switch (type.toLowerCase()) {
    case 'retard':
      return 'warning'
    case 'absence':
      return 'error'
    default:
      return 'info'
  }
}


// Fonction pour obtenir le nom du jour
const getDayName = (dayOfWeek: number): string => {
  const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
  return days[dayOfWeek]
}

// Ajout des refs pour les tableaux de données
const sites = ref<Site[]>([])
const employees = ref<SiteEmployee[]>([])

// Headers pour les tableaux
type TableAlignment = 'start' | 'center' | 'end';

const employeesHeaders = ref([
  { title: 'ID', key: 'employee', align: 'start' as TableAlignment },
  { title: 'Nom', key: 'employee_name', align: 'start' as TableAlignment },
  { title: 'Date d\'ajout', key: 'created_at', align: 'start' as TableAlignment },
  { title: 'Statut', key: 'is_active', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

const sitesHeaders = ref([
  { title: 'ID', key: 'id', align: 'start' as TableAlignment },
  { title: 'Nom', key: 'name', align: 'start' as TableAlignment },
  { title: 'Adresse', key: 'address', align: 'start' as TableAlignment },
  { title: 'Statut', key: 'is_active', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

const planningsHeaders = ref([
  { title: 'Type', key: 'schedule_type', align: 'start' as TableAlignment },
  { title: 'Site', key: 'site_name', align: 'start' as TableAlignment },
  { title: 'Détails', key: 'details', align: 'start' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

const pointagesHeaders = ref([
  { title: 'Date', key: 'timestamp', align: 'start' as TableAlignment },
  { title: 'Employé', key: 'employee', align: 'start' as TableAlignment },
  { title: 'Type', key: 'entry_type', align: 'center' as TableAlignment },
  { title: 'Statut', key: 'status', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

const anomaliesHeaders = ref([
  { title: 'Date', key: 'created_at', align: 'start' as TableAlignment },
  { title: 'Employé', key: 'employee', align: 'start' as TableAlignment },
  { title: 'Type', key: 'type', align: 'center' as TableAlignment },
  { title: 'Description', key: 'description', align: 'start' as TableAlignment },
  { title: 'Statut', key: 'status', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

const reportsHeaders = ref([
  { title: 'Date', key: 'created_at', align: 'start' as TableAlignment },
  { title: 'Nom', key: 'name', align: 'start' as TableAlignment },
  { title: 'Type', key: 'type', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

// Ajout de la fonction unassignEmployeeFromSite
const unassignEmployeeFromSite = async (employeeId: number) => {
  try {
    await sitesApi.unassignEmployee(itemId.value, employeeId)
    showSuccess('Employé retiré du site avec succès')
    
    // Recharger la liste des employés
    const response = await sitesApi.getSiteEmployees(itemId.value)
    employees.value = (response.data.results as unknown as ApiSiteEmployee[]).map(employee => ({
      id: employee.id,
      site: employee.site,
      employee: employee.employee,
      employee_name: employee.employee_name,
      schedule: employee.schedule,
      created_at: employee.created_at,
      is_active: employee.is_active
    }))
  } catch (error) {
    console.error('[DetailView][UnassignEmployee] Erreur lors du retrait de l\'employé:', error)
    showError('Erreur lors du retrait de l\'employé')
  }
}

const formatDate = (dateString: string): string => {
  return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: fr })
}

const timesheetsHeaders = ref([
  { title: 'Date', key: 'date', align: 'start' as TableAlignment },
  { title: 'Employé', key: 'employee', align: 'start' as TableAlignment },
  { title: 'Type', key: 'entry_type', align: 'center' as TableAlignment },
  { title: 'Statut', key: 'status', align: 'center' as TableAlignment },
  { title: 'Actions', key: 'actions', align: 'end' as TableAlignment, sortable: false }
])

interface ScheduleItem {
  schedule_type: 'FIXED' | 'FREQUENCY';
}

// Fonctions pour les timesheets
const showTimesheetDetails = async (timesheet: any) => {
  try {
    const response = await timesheetsApi.getTimesheetDetails(timesheet.id)
    console.log('[Timesheets][Details] Détails du timesheet:', response.data)
    // TODO: Implémenter l'affichage des détails dans une modal ou un dialogue
    // showTimesheetDialog(response.data)
  } catch (error) {
    console.error('[Timesheets][Error] Erreur lors de la récupération des détails:', error)
  }
}

// Fonctions pour les anomalies
const handleResolveAnomaly = async (anomaly: any) => {
  try {
    const response = await timesheetsApi.resolveAnomaly(anomaly.id)
    console.log('[Anomalies][Resolve] Anomalie résolue:', response.data)
    // Rafraîchir la liste des anomalies
    await loadAnomalies()
  } catch (error) {
    console.error('[Anomalies][Error] Erreur lors de la résolution:', error)
  }
}

const handleIgnoreAnomaly = async (anomaly: any) => {
  try {
    const response = await timesheetsApi.ignoreAnomaly(anomaly.id)
    console.log('[Anomalies][Ignore] Anomalie ignorée:', response.data)
    // Rafraîchir la liste des anomalies
    await loadAnomalies()
  } catch (error) {
    console.error('[Anomalies][Error] Erreur lors de l\'ignorance:', error)
  }
}

const showAnomalyDetails = async (anomaly: any) => {
  try {
    const response = await timesheetsApi.getAnomalyDetails(anomaly.id)
    console.log('[Anomalies][Details] Détails de l\'anomalie:', response.data)
    // TODO: Implémenter l'affichage des détails dans une modal ou un dialogue
    // showAnomalyDialog(response.data)
  } catch (error) {
    console.error('[Anomalies][Error] Erreur lors de la récupération des détails:', error)
  }
}

// Fonction pour les rapports
const handleDownloadReport = async (report: any) => {
  try {
    const response = await reportsApi.downloadReport(report.id)
    console.log('[Reports][Download] Rapport téléchargé:', report.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `rapport_${report.id}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('[Reports][Error] Erreur lors du téléchargement:', error)
  }
}

// Fonction pour charger les anomalies
const loadAnomalies = async () => {
  try {
    const response = await timesheetsApi.getAnomalies({ site: itemId.value })
    anomalies.value = response.data.results
    console.log('[Anomalies][Load] Anomalies chargées:', response.data.count)
  } catch (error) {
    console.error('[Anomalies][Error] Erreur lors du chargement:', error)
  }
}

interface ReportItem extends TableItem {
  report_type_display: string;
  status_display: string;
  status: string;
}

const getReportTypeColor = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'hebdomadaire':
      return 'primary'
    case 'mensuel':
      return 'success'
    case 'annuel':
      return 'warning'
    default:
      return 'grey'
  }
}

const showReportDetails = (item: ReportItem) => {
  // TODO: Implémenter l'affichage des détails du rapport
  console.log('Afficher les détails du rapport:', item)
}

const handleApproveReport = async (item: ReportItem) => {
  try {
    // TODO: Implémenter l'approbation du rapport
    console.log('Approuver le rapport:', item)
  } catch (error) {
    console.error('Erreur lors de l\'approbation du rapport:', error)
  }
}

const handleRejectReport = async (item: ReportItem) => {
  try {
    // TODO: Implémenter le rejet du rapport
    console.log('Rejeter le rapport:', item)
  } catch (error) {
    console.error('Erreur lors du rejet du rapport:', error)
  }
}
</script>

<style scoped>
.white-space-pre-wrap {
  white-space: pre-wrap;
}

/* Style des icônes dans la liste */
:deep(.v-list-item) {
  padding: 12px 16px;
}

:deep(.v-list-item .v-icon) {
  color: #00346E !important;
  margin-right: 12px;
  font-size: 20px;
}

:deep(.v-list-item-title) {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
  margin-bottom: 4px;
}

:deep(.v-list-item-subtitle) {
  font-size: 1rem;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 400;
}

/* Style du bouton retour */
:deep(.v-btn.mr-4) {
  color: #00346E !important;
  border: 1px solid #00346E !important;
  margin-right: 16px !important;
  transition: all 0.3s ease;
}

:deep(.v-btn.mr-4 .v-icon) {
  color: #00346E !important;
  opacity: 1 !important;
}

:deep(.v-btn.mr-4:hover) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn.mr-4:hover .v-icon) {
  color: white !important;
}

/* Style des onglets */
:deep(.v-tabs) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

:deep(.v-tab) {
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: normal !important;
}

:deep(.v-tab--selected) {
  color: #00346E !important;
}

:deep(.v-tab:hover) {
  color: #00346E !important;
  opacity: 0.8;
}

/* Style du QR code */
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

/* Style des boutons normaux */
:deep(.v-btn[color="primary"]) {
  background-color: #00346E !important;
  color: white !important;
}

:deep(.v-btn[color="error"]) {
  background-color: #F78C48 !important;
  color: white !important;
}

:deep(.v-btn[color="grey"]) {
  background-color: #999999 !important;
  color: white !important;
  opacity: 0.5 !important;
  cursor: default !important;
  pointer-events: none !important;
}

/* Style des puces */
:deep(.v-chip) {
  font-size: 0.875rem !important;
  font-weight: 500 !important;
}

:deep(.v-chip.v-chip--size-small) {
  font-size: 0.75rem !important;
}

/* Style des cartes */
:deep(.v-card-title) {
  font-size: 1.25rem !important;
  font-weight: 500 !important;
  padding: 16px !important;
}

:deep(.v-card-text) {
  padding: 16px !important;
}

/* Style des listes */
:deep(.v-list) {
  padding: 8px 0;
  background-color: transparent;
}

:deep(.v-list-item) {
  margin-bottom: 8px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

:deep(.v-list-item:hover) {
  background-color: rgba(0, 52, 110, 0.04);
}

:deep(.v-list-item:last-child) {
  margin-bottom: 0;
}
</style> 