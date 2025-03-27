<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <Title level="1">Employés</Title>
    </div>

    <!-- Message d'erreur -->
    <v-alert
      v-if="employeesStore.error"
      type="error"
      class="mb-4"
      closable
    >
      {{ employeesStore.error }}
    </v-alert>
    
    <v-card>
      <v-data-table
        :headers="headers"
        :items="employeesStore.employees"
        :loading="employeesStore.loading"
        :items-per-page="employeesStore.itemsPerPage"
        :page="employeesStore.currentPage"
        :total-items="employeesStore.totalEmployees"
        :no-data-text="'Aucun employé trouvé'"
        :loading-text="'Chargement des employés...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        class="elevation-1"
        @update:options="handleTableUpdate"
      >
        <!-- Status column -->
        <template #item.is_active="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            :text="item.is_active ? 'Actif' : 'Inactif'"
            size="small"
          />
        </template>

        <!-- Actions column -->
        <template #item.actions="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            :to="`/dashboard/employees/${item.id}`"
            color="info"
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editEmployee(item)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click="confirmDelete(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog de création/édition -->
    <v-dialog v-model="showDialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ isEditing ? 'Modifier' : 'Ajouter' }} un employé</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="form" v-model="isFormValid">
            <v-container>
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="formData.first_name"
                    label="Prénom"
                    required
                    :rules="[v => !!v || 'Le prénom est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="formData.last_name"
                    label="Nom"
                    required
                    :rules="[v => !!v || 'Le nom est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formData.email"
                    label="Email"
                    type="email"
                    required
                    :rules="[
                      v => !!v || 'L\'email est requis',
                      v => /.+@.+\..+/.test(v) || 'L\'email doit être valide'
                    ]"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formData.phone_number"
                    label="Téléphone"
                    :rules="[v => !v || /^[0-9]{10}$/.test(v.replace(/\D/g, '')) || 'Le numéro de téléphone doit contenir 10 chiffres']"
                    :value="formData.phone_number ? formatPhoneNumber(formData.phone_number) : ''"
                    @input="e => formData.phone_number = e.target.value.replace(/\D/g, '')"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formData.employee_id"
                    label="ID Employé"
                    :rules="[v => !!v || 'L\'ID employé est requis']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12">
                  <v-switch
                    v-model="formData.is_active"
                    label="Actif"
                    color="success"
                  ></v-switch>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            @click="closeDialog"
          >
            Annuler
          </v-btn>
          <v-btn
            color="primary"
            variant="text"
            @click="saveEmployee"
            :loading="employeesStore.loading"
            :disabled="!isFormValid"
          >
            {{ isEditing ? 'Modifier' : 'Ajouter' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="showDeleteDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer cet employé ? Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            @click="showDeleteDialog = false"
          >
            Annuler
          </v-btn>
          <v-btn
            color="error"
            variant="text"
            @click="deleteEmployee"
            :loading="employeesStore.loading"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useEmployeesStore } from '@/stores/employees'
import { formatPhoneNumber } from '@/utils/formatters'
import { Title } from '@/components/typography'

export default {
  name: 'EmployeesView',
  components: {
    Title
  },
  setup() {
    const employeesStore = useEmployeesStore()
    const form = ref(null)
    const isFormValid = ref(false)
    const showDialog = ref(false)
    const showDeleteDialog = ref(false)
    const isEditing = ref(false)
    const selectedEmployeeId = ref(null)

    const headers = ref([
      { title: 'Prénom', align: 'start', key: 'first_name' },
      { title: 'Nom', align: 'start', key: 'last_name' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone_number', format: value => value ? formatPhoneNumber(value) : '-' },
      { title: 'ID Employé', align: 'start', key: 'employee_id' },
      { title: 'Statut', align: 'center', key: 'is_active' },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const formData = ref({
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      employee_id: '',
      is_active: true
    })

    const handleTableUpdate = async (options) => {
      employeesStore.currentPage = options.page
      employeesStore.itemsPerPage = options.itemsPerPage
      await employeesStore.fetchEmployees()
    }

    // Charger les employés au montage du composant
    onMounted(async () => {
      try {
        await employeesStore.fetchEmployees()
      } catch (error) {
        console.error('Erreur lors du chargement des employés:', error)
      }
    })

    const resetForm = () => {
      formData.value = {
        first_name: '',
        last_name: '',
        email: '',
        phone_number: '',
        employee_id: '',
        is_active: true
      }
      if (form.value) {
        form.value.resetValidation()
      }
    }

    const closeDialog = () => {
      showDialog.value = false
      resetForm()
      isEditing.value = false
      selectedEmployeeId.value = null
    }

    const editEmployee = (employee) => {
      isEditing.value = true
      selectedEmployeeId.value = employee.id
      formData.value = { ...employee }
      showDialog.value = true
    }

    const confirmDelete = (employee) => {
      selectedEmployeeId.value = employee.id
      showDeleteDialog.value = true
    }

    const saveEmployee = async () => {
      try {
        if (isEditing.value) {
          await employeesStore.updateEmployee(selectedEmployeeId.value, formData.value)
        } else {
          await employeesStore.createEmployee(formData.value)
        }
        closeDialog()
      } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error)
      }
    }

    const deleteEmployee = async () => {
      try {
        await employeesStore.deleteEmployee(selectedEmployeeId.value)
        showDeleteDialog.value = false
        selectedEmployeeId.value = null
      } catch (error) {
        console.error('Erreur lors de la suppression:', error)
      }
    }

    return {
      employeesStore,
      headers,
      form,
      formData,
      isFormValid,
      showDialog,
      showDeleteDialog,
      isEditing,
      editEmployee,
      confirmDelete,
      saveEmployee,
      deleteEmployee,
      closeDialog,
      handleTableUpdate
    }
  }
}
</script>

<style scoped>
.v-data-table {
  border-radius: 8px;
}
</style>

