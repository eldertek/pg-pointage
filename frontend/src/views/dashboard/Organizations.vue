<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <h1 class="text-h4">Organisations</h1>
      <v-btn color="primary" prepend-icon="mdi-plus" to="/dashboard/organizations/new">
        Ajouter une organisation
      </v-btn>
    </div>
    
    <v-card>
      <v-card-title>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Rechercher"
          single-line
          hide-details
          variant="outlined"
          density="compact"
        ></v-text-field>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="organizations"
        :loading="loading"
        :items-per-page="10"
        :search="search"
        :no-data-text="'Aucune organisation trouvée'"
        :loading-text="'Chargement des organisations...'"
        :items-per-page-text="'Lignes par page'"
        :page-text="'{0}-{1} sur {2}'"
        :items-per-page-options="[
          { title: '5', value: 5 },
          { title: '10', value: 10 },
          { title: '15', value: 15 },
          { title: 'Tout', value: -1 }
        ]"
        class="elevation-1"
      >
        <template #[`item.status`]="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'error'"
            size="small"
          >
            {{ item.is_active ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>

        <template #[`item.actions`]="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            :to="`/dashboard/organizations/${item.id}`"
            :title="'Voir les détails de ' + item.name"
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="primary"
            @click="editOrganization(item)"
            :title="'Modifier ' + item.name"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click="confirmDelete(item)"
            :title="'Supprimer ' + item.name"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Dialog de confirmation de suppression -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>Confirmer la suppression</v-card-title>
        <v-card-text>
          Êtes-vous sûr de vouloir supprimer l'organisation "{{ organizationToDelete?.name }}" ?
          Cette action est irréversible.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showDeleteDialog = false">Annuler</v-btn>
          <v-btn 
            color="error" 
            variant="text" 
            @click="deleteOrganization"
            :loading="deleting"
          >
            Supprimer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog d'édition -->
    <v-dialog v-model="showEditDialog" max-width="800">
      <v-card>
        <v-card-title>Modifier l'organisation</v-card-title>
        <v-card-text>
          <v-form ref="form">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedOrganization.name"
                  label="Nom de l'organisation"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedOrganization.email"
                  label="Email principal"
                  type="email"
                  required
                  :rules="[rules.required, rules.email]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedOrganization.contact_email"
                  label="Email de contact"
                  type="email"
                  required
                  :rules="[rules.required, rules.email]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedOrganization.phone"
                  label="Téléphone"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editedOrganization.siret"
                  label="SIRET"
                  required
                  :rules="[
                    rules.required,
                    v => /^\d{14}$/.test(v) || 'Le SIRET doit contenir 14 chiffres'
                  ]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-file-input
                  v-model="editedOrganization.logo"
                  label="Logo"
                  accept="image/*"
                  prepend-icon="mdi-camera"
                  :show-size="true"
                  :rules="[
                    v => !v || v.size < 2000000 || 'Le logo doit faire moins de 2MB'
                  ]"
                ></v-file-input>
              </v-col>

              <v-col cols="12">
                <v-text-field
                  v-model="editedOrganization.address"
                  label="Adresse"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editedOrganization.postal_code"
                  label="Code postal"
                  required
                  :rules="[
                    rules.required,
                    v => /^\d{5}$/.test(v) || 'Le code postal doit contenir 5 chiffres'
                  ]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editedOrganization.city"
                  label="Ville"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="4">
                <v-text-field
                  v-model="editedOrganization.country"
                  label="Pays"
                  required
                  :rules="[rules.required]"
                ></v-text-field>
              </v-col>

              <v-col cols="12">
                <v-textarea
                  v-model="editedOrganization.notes"
                  label="Notes"
                  rows="3"
                ></v-textarea>
              </v-col>

              <v-col cols="12">
                <v-switch
                  v-model="editedOrganization.is_active"
                  label="Organisation active"
                  color="success"
                ></v-switch>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showEditDialog = false">Annuler</v-btn>
          <v-btn 
            color="primary" 
            @click="saveOrganization"
            :loading="saving"
          >
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar pour les notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import type { Ref } from 'vue'
import api from '@/services/api'
import type { Organization, OrganizationFormData, SnackbarState, TableHeaders } from '@/types/organization'

export default defineComponent({
  name: 'OrganizationsView',
  setup() {
    const loading = ref<boolean>(false)
    const search = ref<string>('')
    const organizations = ref<Organization[]>([])
    const showDeleteDialog = ref<boolean>(false)
    const showEditDialog = ref<boolean>(false)
    const organizationToDelete = ref<Organization | null>(null)
    const editedOrganization = ref<OrganizationFormData>({
      name: '',
      address: '',
      phone: '',
      email: '',
      contact_email: '',
      logo: null,
      siret: '',
      postal_code: '',
      city: '',
      country: 'France',
      notes: '',
      is_active: true
    })
    const deleting = ref<boolean>(false)
    const saving = ref<boolean>(false)
    const form = ref<any>(null)

    const headers = ref<TableHeaders[]>([
      { title: 'Nom', align: 'start', key: 'name' },
      { title: 'Adresse', align: 'start', key: 'address' },
      { title: 'Email', align: 'start', key: 'email' },
      { title: 'Téléphone', align: 'start', key: 'phone' },
      { title: 'Statut', align: 'center', key: 'status', sortable: false },
      { title: 'Actions', align: 'end', key: 'actions', sortable: false }
    ])

    const rules = {
      required: (v: any) => !!v || 'Ce champ est requis',
      email: (v: string) => /.+@.+\..+/.test(v) || 'Veuillez entrer une adresse email valide'
    }

    const snackbar = ref<SnackbarState>({
      show: false,
      text: '',
      color: 'success'
    })

    const fetchOrganizations = async (): Promise<void> => {
      loading.value = true
      try {
        const response = await api.get('/organizations/')
        console.log('Données des organisations reçues:', response.data)
        organizations.value = response.data.results || []
      } catch (error) {
        console.error('Erreur lors du chargement des organisations:', error)
        showError('Erreur lors du chargement des organisations')
      } finally {
        loading.value = false
      }
    }

    const confirmDelete = (organization: Organization): void => {
      organizationToDelete.value = organization
      showDeleteDialog.value = true
    }

    const deleteOrganization = async (): Promise<void> => {
      if (!organizationToDelete.value) return

      deleting.value = true
      try {
        await api.delete(`/organizations/${organizationToDelete.value.id}/`)
        await fetchOrganizations()
        showSuccess('Organisation supprimée avec succès')
        showDeleteDialog.value = false
      } catch (error) {
        console.error('Erreur lors de la suppression:', error)
        showError('Erreur lors de la suppression de l\'organisation')
      } finally {
        deleting.value = false
      }
    }

    const editOrganization = (organization: Organization): void => {
      editedOrganization.value = {
        name: organization.name,
        address: organization.address,
        phone: organization.phone,
        email: organization.email,
        contact_email: organization.contact_email,
        logo: null,
        siret: organization.siret,
        postal_code: organization.postal_code,
        city: organization.city,
        country: organization.country,
        notes: organization.notes,
        is_active: organization.is_active
      }
      showEditDialog.value = true
    }

    const saveOrganization = async (): Promise<void> => {
      const { valid } = await form.value.validate()
      if (!valid) {
        showError('Veuillez remplir tous les champs requis')
        return
      }

      saving.value = true
      try {
        const formData = new FormData()
        Object.entries(editedOrganization.value).forEach(([key, value]) => {
          if (key === 'logo' && value instanceof File) {
            formData.append('logo', value)
          } else if (value !== null && value !== undefined) {
            formData.append(key, value.toString())
          }
        })

        const response = await api.put(
          `/organizations/${organizationToDelete.value?.id}/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        console.log('Réponse de mise à jour:', response.data)
        await fetchOrganizations()
        showSuccess('Organisation mise à jour avec succès')
        showEditDialog.value = false
      } catch (error) {
        console.error('Erreur lors de la mise à jour:', error)
        showError('Erreur lors de la mise à jour de l\'organisation')
      } finally {
        saving.value = false
      }
    }

    const showSuccess = (text: string): void => {
      snackbar.value = {
        show: true,
        text,
        color: 'success'
      }
    }

    const showError = (text: string): void => {
      snackbar.value = {
        show: true,
        text,
        color: 'error'
      }
    }

    onMounted(() => {
      fetchOrganizations()
    })

    return {
      loading,
      search,
      headers,
      organizations,
      showDeleteDialog,
      showEditDialog,
      organizationToDelete,
      editedOrganization,
      deleting,
      saving,
      form,
      rules,
      snackbar,
      editOrganization,
      confirmDelete,
      deleteOrganization,
      saveOrganization
    }
  }
})
</script>

