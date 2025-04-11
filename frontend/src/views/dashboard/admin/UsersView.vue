<template>
  <DashboardView
    ref="dashboardView"
    title="Utilisateurs"
    :form-title="editedItem?.id ? 'Modifier un utilisateur' : 'Nouvel utilisateur'"
    :saving="saving"
    @save="saveUser"
    @cancel="resetFormState"
  >
    <!-- Filtres -->
    <template #filters>
      <DashboardFilters @reset="resetFilters">
        <v-col cols="12" md="4">
          <v-text-field
            v-model="filters.search"
            label="Rechercher"
            variant="outlined"
            prepend-inner-icon="mdi-magnify"
            clearable
            @update:model-value="loadUsers"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="filters.role"
            :items="roles"
            item-title="label"
            item-value="value"
            label="Rôle"
            variant="outlined"
            prepend-inner-icon="mdi-account-key"
            clearable
            @update:model-value="loadUsers"
          ></v-select>
        </v-col>
      </DashboardFilters>
    </template>

    <!-- Actions -->
    <template #actions>
      <v-btn
        v-if="canCreateDelete"
        color="primary"
        prepend-icon="mdi-plus"
        @click="openDialog()"
      >
        Nouvel utilisateur
      </v-btn>
    </template>

    <!-- Tableau des utilisateurs -->
    <v-data-table
      v-if="canView"
      v-model:page="page"
      :headers="headers"
      :items="filteredUsers"
      :loading="loading"
      :items-per-page="itemsPerPage"
      :items-length="totalItems"
      :no-data-text="'Aucun utilisateur trouvé'"
      :loading-text="'Chargement des utilisateurs...'"
      :items-per-page-text="'Lignes par page'"
      :page-text="'{0}-{1} sur {2}'"
      :items-per-page-options="[
        { title: '5', value: 5 },
        { title: '10', value: 10 },
        { title: '15', value: 15 },
        { title: 'Tout', value: -1 }
      ]"
      :sort-by="[{ key: 'last_name' }, { key: 'first_name' }, { key: 'role' }]"
      class="elevation-1"
      @click:row="handleRowClick"
    >
      <!-- Rôle -->
      <template #item.role="{ item }">
        <v-chip
          :color="getRoleColor(item.role)"
          size="small"
        >
          {{ getRoleLabel(item.role) }}
        </v-chip>
      </template>

      <!-- Sites -->
      <template #item.sites="{ item }">
        <v-chip
          v-for="site in item.sites"
          :key="site.id"
          color="primary"
          size="small"
          class="mr-1"
        >
          {{ site.name }}
        </v-chip>
      </template>

      <!-- Organizations -->
      <template #item.organizations_names="{ item }">
        <template v-if="item.organizations_names && item.organizations_names.length > 0">
          <v-chip
            v-for="orgName in item.organizations_names"
            :key="orgName"
            color="primary"
            size="small"
            class="mr-1"
          >
            {{ orgName }}
          </v-chip>
        </template>
        <span v-else class="text-grey">
          Aucune organisation
        </span>
      </template>

      <!-- Actions -->
      <template #item.actions="{ item }">
        <v-btn
          v-if="canView"
          icon
          variant="text"
          size="small"
          color="primary"
          :to="`/dashboard/admin/users/${(item as ExtendedUser).id}`"
          @click.stop
        >
          <v-icon>mdi-eye</v-icon>
          <v-tooltip activator="parent">Voir les détails</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canEdit && (item as ExtendedUser)?.id !== authStore.user?.id"
          icon
          variant="text"
          size="small"
          color="primary"
          @click.stop="openDialog(item as ExtendedUser)"
        >
          <v-icon>mdi-pencil</v-icon>
          <v-tooltip activator="parent">Modifier</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canCreateDelete && (item as ExtendedUser)?.id !== authStore.user?.id"
          icon
          variant="text"
          size="small"
          color="warning"
          @click.stop="toggleStatus(item as ExtendedUser)"
        >
          <v-icon>{{ (item as ExtendedUser).is_active ? 'mdi-domain' : 'mdi-domain-off' }}</v-icon>
          <v-tooltip activator="parent">{{ (item as ExtendedUser).is_active ? 'Désactiver' : 'Activer' }}</v-tooltip>
        </v-btn>
        <v-btn
          v-if="canCreateDelete && (item as ExtendedUser)?.id !== authStore.user?.id"
          icon
          variant="text"
          size="small"
          color="error"
          @click.stop="confirmDelete(item as ExtendedUser)"
        >
          <v-icon>mdi-delete</v-icon>
          <v-tooltip activator="parent">Supprimer</v-tooltip>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Formulaire -->
    <template #form>
      <DashboardForm ref="form" :errors="formErrors" @submit="saveUser">
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).last_name"
            label="Nom"
            required
            :error-messages="formErrors.last_name"
            autocomplete="family-name"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).first_name"
            label="Prénom"
            required
            :error-messages="formErrors.first_name"
            autocomplete="given-name"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).phone_number"
            label="Téléphone"
            required
            :error-messages="formErrors.phone_number"
            autocomplete="tel"
          ></v-text-field>
        </v-col>
        <v-col v-if="(editedItem as UserFormData).id" cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).employee_id"
            label="ID"
            readonly
            disabled
            persistent-hint
            autocomplete="off"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).email"
            label="Email"
            type="email"
            required
            :error-messages="formErrors.email"
            autocomplete="email"
            @update:model-value="handleEmailChange"
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6">
          <v-select
            v-model="(editedItem as UserFormData).role"
            :items="roles"
            item-title="label"
            item-value="value"
            label="Rôle"
            required
            :error-messages="formErrors.role"
          ></v-select>
        </v-col>
        <!-- Sélection des organisations pour tous les rôles sauf Super Admin -->
        <v-col v-if="(editedItem as UserFormData).role !== RoleEnum.SUPER_ADMIN" cols="12" sm="6">
          <v-select
            v-model="selectedOrganizations"
            :items="organizationItems"
            item-title="name"
            item-value="id"
            label="Organisations"
            multiple
            chips
            required
            :error-messages="formErrors.organizations"
            :rules="[v => (v && v.length > 0) || 'Au moins une organisation est requise']"
            no-data-text="Aucune organisation disponible"
            :return-object="false"
            @update:model-value="(val: number[]) => {
              if (editedItem && Array.isArray(val)) {
                editedItem.organizations = [...val];
                console.log('[Debug][v-select] Nouvelle valeur:', JSON.stringify(val));
                console.log('[Debug][v-select] État de editedItem:', JSON.stringify(editedItem.organizations));
              }
            }"
          >
            <template #chip="{ props: slotProps, item }">
              <v-chip
                v-bind="slotProps"
                :text="organizationsMap.get(item.value) || item.title"
                color="primary"
                size="small"
              ></v-chip>
            </template>
          </v-select>
        </v-col>

        <!-- Mot de passe en mode création -->
        <v-col v-if="!(editedItem as UserFormData).id" cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).password"
            label="Mot de passe"
            :type="showPassword ? 'text' : 'password'"
            required
            :error-messages="formErrors.password"
            :rules="[
              v => !!v || 'Le mot de passe est requis',
              v => !v || v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
            ]"
            autocomplete="new-password"
          >
            <template #append-inner>
              <v-btn
                icon
                variant="text"
                @click="showPassword = !showPassword"
              >
                <v-icon>{{ showPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
              </v-btn>
            </template>
          </v-text-field>
        </v-col>

        <!-- Confirmation mot de passe en mode création -->
        <v-col v-if="!(editedItem as UserFormData).id" cols="12" sm="6">
          <v-text-field
            v-model="confirmPassword"
            label="Confirmer le mot de passe"
            :type="showConfirmPassword ? 'text' : 'password'"
            required
            :error-messages="formErrors.confirm_password"
            :rules="[
              v => !!v || 'La confirmation du mot de passe est requise',
              v => v === (editedItem as UserFormData).password || 'Les mots de passe ne correspondent pas'
            ]"
            autocomplete="new-password"
          >
            <template #append-inner>
              <v-btn
                icon
                variant="text"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <v-icon>{{ showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
              </v-btn>
            </template>
          </v-text-field>
        </v-col>

        <!-- Switch pour la vue mobile simplifiée (pour les employés) -->
        <v-col v-if="(editedItem as UserFormData).role === RoleEnum.EMPLOYEE" cols="12">
          <v-switch
            v-model="(editedItem as UserFormData).simplified_mobile_view"
            label="Vue mobile simplifiée"
            :error-messages="formErrors.simplified_mobile_view"
          ></v-switch>
        </v-col>

        <!-- Section de réinitialisation du mot de passe (uniquement en mode modification) -->
        <v-col v-if="(editedItem as UserFormData).id" cols="12">
          <v-divider class="my-4"></v-divider>
          <v-card-title class="text-subtitle-1 font-weight-medium">
            Réinitialisation du mot de passe
            <v-chip
              color="grey"
              size="small"
              class="ml-2"
            >
              Optionnel
            </v-chip>
          </v-card-title>
          <v-card-text class="text-caption text-grey">
            Vous pouvez réinitialiser le mot de passe de l'utilisateur. Laissez ces champs vides si vous ne souhaitez pas modifier le mot de passe.
          </v-card-text>
        </v-col>

        <!-- Mot de passe en mode modification -->
        <v-col v-if="(editedItem as UserFormData).id && (canCreateDelete || (editedItem as UserFormData).organizations.some(orgId => authStore.user?.organizations.some(userOrg => userOrg.id === orgId)))" cols="12" sm="6">
          <v-text-field
            v-model="(editedItem as UserFormData).password"
            label="Nouveau mot de passe"
            :type="showPassword ? 'text' : 'password'"
            :error-messages="formErrors.password"
            :rules="[
              v => !v || v.length >= 8 || 'Le mot de passe doit contenir au moins 8 caractères'
            ]"
            hint="Laissez vide pour ne pas modifier le mot de passe"
            persistent-hint
            autocomplete="new-password"
          >
            <template #append-inner>
              <v-btn
                icon
                variant="text"
                @click="showPassword = !showPassword"
              >
                <v-icon>{{ showPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
              </v-btn>
            </template>
          </v-text-field>
        </v-col>

        <!-- Confirmation mot de passe en mode modification -->
        <v-col v-if="(editedItem as UserFormData).id && (canCreateDelete || (editedItem as UserFormData).organizations.some(orgId => authStore.user?.organizations.some(userOrg => userOrg.id === orgId)))" cols="12" sm="6">
          <v-text-field
            v-model="confirmPassword"
            label="Confirmer le nouveau mot de passe"
            :type="showConfirmPassword ? 'text' : 'password'"
            :error-messages="formErrors.confirm_password"
            :rules="[
              v => !v || v === (editedItem as UserFormData).password || 'Les mots de passe ne correspondent pas'
            ]"
            hint="Laissez vide pour ne pas modifier le mot de passe"
            persistent-hint
            autocomplete="new-password"
          >
            <template #append-inner>
              <v-btn
                icon
                variant="text"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <v-icon>{{ showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
              </v-btn>
            </template>
          </v-text-field>
        </v-col>
      </DashboardForm>
    </template>
  </DashboardView>
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { usersApi, organizationsApi } from '@/services/api'
import type { Organization } from '@/types/api'
import { RoleEnum, ScanPreferenceEnum } from '@/types/api'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/components/dashboard/DashboardView.vue'
import DashboardFilters from '@/components/dashboard/DashboardFilters.vue'
import DashboardForm from '@/components/dashboard/DashboardForm.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useRouter } from 'vue-router'
import { useConfirmDialog } from '@/utils/dialogs'
import type { DialogState } from '@/utils/dialogs'

// Interface étendue pour les utilisateurs avec les propriétés supplémentaires
interface ExtendedUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  organizations: number[];
  organizations_names: string[];
  phone_number: string;
  scan_preference: string;
  simplified_mobile_view: boolean;
  date_joined?: string;
  employee_id?: string;
  sites?: { id: number; name: string }[];
}

// Interface pour le formulaire utilisateur
interface UserFormData {
  id?: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organizations: number[];
  organizations_names?: string[];
  phone_number: string;
  is_active: boolean;
  scan_preference: string;
  simplified_mobile_view: boolean;
  password?: string;
  employee_id?: string;
}

interface AuthUser {
  id: number;
  role: string;
  organizations: number[];
}

const authStore = useAuthStore()

const props = defineProps({
  editId: {
    type: [String, Number],
    default: null
  }
})

// État
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const itemsPerPage = ref(10)
const totalItems = ref(0)
const editedItem = ref<UserFormData | null>(null)
const form = ref()
const dashboardView = ref()
const formErrors = ref<Record<string, string[]>>({})

// Filtres
const filters = ref({
  search: '',
  role: ''
})

// Données
const users = ref<ExtendedUser[]>([])
const organizations = ref<Organization[]>([])
const organizationsMap = ref<Map<number, string>>(new Map())

// En-têtes des tableaux
const headers = [
  { title: 'ID', key: 'employee_id' },
  { title: 'Nom', key: 'last_name' },
  { title: 'Prénom', key: 'first_name' },
  { title: 'Téléphone', key: 'phone_number' },
  { title: 'Email', key: 'email' },
  { title: 'Rôle', key: 'role' },
  { title: 'Organisations', key: 'organizations_names', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Rôles disponibles
const roles = computed(() => {
  const userRole = authStore.user?.role
  const allRoles = [
    { label: 'Super Admin', value: RoleEnum.SUPER_ADMIN },
    { label: 'Admin', value: RoleEnum.ADMIN },
    { label: 'Manager', value: RoleEnum.MANAGER },
    { label: 'Employé', value: RoleEnum.EMPLOYEE }
  ]

  // Si l'utilisateur est super admin, il peut créer tous les types d'utilisateurs
  if (userRole === RoleEnum.SUPER_ADMIN) {
    return allRoles
  }

  // Si l'utilisateur est admin, il ne peut créer que des managers et des employés
  if (userRole === RoleEnum.ADMIN) {
    return allRoles.filter(role =>
      role.value === RoleEnum.MANAGER || role.value === RoleEnum.EMPLOYEE
    )
  }

  // Si l'utilisateur est manager, il ne peut créer que des employés
  if (userRole === RoleEnum.MANAGER) {
    return allRoles.filter(role => role.value === RoleEnum.EMPLOYEE)
  }

  // Pour les autres rôles, pas de création d'utilisateurs
  return []
})

// Méthodes
const router = useRouter()
const { dialogState } = useConfirmDialog()

// Computed properties pour les permissions
const canCreateDelete = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN
})

const canEdit = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN || role === RoleEnum.MANAGER
})

const canView = computed(() => {
  const role = authStore.user?.role
  return role === RoleEnum.SUPER_ADMIN || role === RoleEnum.ADMIN || role === RoleEnum.MANAGER
})

// Créer des éléments formatés pour le sélecteur d'organisations
const organizationItems = computed(() => {
  console.log('[Debug][organizationItems] Organizations brutes:', organizations.value)
  const items = organizations.value.map(org => ({
    id: org.id,
    name: org.name
  }))
  console.log('[Debug][organizationItems] Items formatés:', items)
  return items
})

// Filtrer les utilisateurs selon les permissions
const filteredUsers = computed(() => {
  const user = authStore.user as AuthUser | null
  if (!user) {
    console.log('[Debug] Pas d\'utilisateur connecté')
    return []
  }

  console.log('[Debug] Utilisateur connecté:', user.role)
  console.log('[Debug] Organisations de l\'utilisateur:', user.organizations)
  console.log('[Debug] Utilisateurs avant filtrage:', users.value)

  // Super Admin voit tout
  if (user.role === RoleEnum.SUPER_ADMIN) {
    return users.value
  }

  // Pour les autres rôles, filtrer selon les organisations
  return users.value.filter(u => {
    if (!u || !u.organizations || !user.organizations) {
      console.log('[Debug] Données manquantes pour', u?.email)
      return false
    }

    // Vérifier si l'utilisateur a accès à au moins une organisation commune
    const userOrgIds = Array.isArray(user.organizations)
      ? user.organizations
      : [user.organizations]

    console.log('[Debug] userOrgIds brut:', JSON.stringify(userOrgIds))
    console.log('[Debug] u.organizations brut:', JSON.stringify(u.organizations))

    const hasCommonOrg = u.organizations.some(orgId => userOrgIds.includes(orgId))

    console.log('[Debug] Vérification accès pour', u.email, ':', {
      userOrgIds: JSON.stringify(userOrgIds),
      userOrgs: JSON.stringify(u.organizations),
      hasAccess: hasCommonOrg
    })

    return hasCommonOrg
  })
})

const handleRowClick = (event: any, { item }: any) => {
  if (item?.id) {
    router.push(`/dashboard/admin/users/${item.id}`)
  }
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await usersApi.getAllUsers({
      page: page.value,
      page_size: itemsPerPage.value,
      search: filters.value.search,
      role: filters.value.role
    })
    users.value = response.data.results || []
    totalItems.value = response.data.count
    
    // Mettre à jour la map des organisations avec les noms depuis les résultats des utilisateurs
    users.value.forEach(user => {
      if (user.organizations && user.organizations_names) {
        user.organizations.forEach((orgId, index) => {
          if (user.organizations_names[index]) {
            organizationsMap.value.set(orgId, user.organizations_names[index])
          }
        })
      }
    })
    
  } catch (error) {
    console.error('Erreur lors du chargement des utilisateurs:', error)
  } finally {
    loading.value = false
  }
}

const loadOrganizations = async () => {
  try {
    const response = await organizationsApi.getAllOrganizations()
    organizations.value = response.data.results || []
    
    // Créer un map des organisations pour la recherche rapide
    organizationsMap.value.clear()
    organizations.value.forEach(org => {
      organizationsMap.value.set(org.id, org.name)
    })
  } catch (error) {
    console.error('Erreur lors du chargement des organisations:', error)
  }
}

const resetFilters = () => {
  filters.value = {
    search: '',
    role: ''
  }
  loadUsers()
}

const generateUsername = (email: string): string => {
  // Prend la partie avant @ de l'email
  let baseUsername = email.split('@')[0]

  // Supprime les caractères spéciaux et les espaces
  baseUsername = baseUsername.replace(/[^a-zA-Z0-9]/g, '')

  // Ajoute un timestamp pour garantir l'unicité
  const timestamp = new Date().getTime().toString().slice(-4)
  return `${baseUsername}${timestamp}`
}

const handleEmailChange = (email: string) => {
  if (!editedItem.value) return
  const userFormData = editedItem.value as UserFormData
  if (!userFormData.id) {
    userFormData.username = generateUsername(email)
  }
}

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const confirmPassword = ref('')

// Modifier le v-select pour utiliser une valeur intermédiaire
const selectedOrganizations = ref<number[]>([]);

// Watcher pour synchroniser les changements
watch(() => editedItem.value?.organizations, (newVal) => {
  console.log('[Debug][Orgs] Watcher déclenché avec:', JSON.stringify(newVal));
  if (newVal) {
    selectedOrganizations.value = [...newVal];
    console.log('[Debug][Orgs] Mise à jour selectedOrganizations:', JSON.stringify(selectedOrganizations.value));
  }
}, { immediate: true });

// Initialisation
onMounted(async () => {
  await Promise.all([
    loadUsers(),
    loadOrganizations()
  ])

  // Si on a un ID d'édition, ouvrir le dialogue
  if (props.editId) {
    try {
      console.log("[Users][EditId] Mode édition pour l'utilisateur:", props.editId);
      const response = await usersApi.getUser(Number(props.editId));
      console.log('[Users][EditMode] Données utilisateur chargées:', JSON.stringify(response.data));

      if (response.data) {
        // Initialiser selectedOrganizations avant d'ouvrir le dialogue
        selectedOrganizations.value = Array.isArray(response.data.organizations) 
          ? [...response.data.organizations] 
          : [];
        
        console.log('[Debug][Orgs] selectedOrganizations initialisé avec:', JSON.stringify(selectedOrganizations.value));
        
        // Ensuite ouvrir le dialogue
        openDialog(response.data);
      }
    } catch (error) {
      console.error('[Users][Error] Erreur lors du chargement des données:', error);
    }
  }
});

const openDialog = (item?: ExtendedUser) => {
  // Réinitialiser complètement l'état du formulaire
  resetFormState();
  
  if (item) {
    console.log('[Users][OpenDialog] Item organizations:', JSON.stringify(item.organizations));
    console.log('[Users][OpenDialog] Item organizations_names:', JSON.stringify(item.organizations_names));

    // S'assurer que les organisations sont un tableau valide
    const orgs = Array.isArray(item.organizations) ? [...item.organizations] : [];
    console.log('[Users][OpenDialog] Organisations formatées:', JSON.stringify(orgs));

    // Créer une copie profonde de l'objet pour éviter les problèmes de réactivité
    const formData = {
      id: item.id,
      username: item.username,
      email: item.email,
      first_name: item.first_name,
      last_name: item.last_name,
      role: item.role,
      organizations: orgs,
      organizations_names: item.organizations_names ? [...item.organizations_names] : [],
      phone_number: item.phone_number,
      is_active: item.is_active,
      scan_preference: item.scan_preference,
      simplified_mobile_view: item.simplified_mobile_view,
      employee_id: item.employee_id
    };

    console.log('[Debug][Orgs] FormData avant affectation:', JSON.stringify(formData.organizations));
    
    // Mettre à jour selectedOrganizations si ce n'est pas déjà fait
    if (!props.editId) {
      selectedOrganizations.value = [...orgs];
      console.log('[Debug][Orgs] selectedOrganizations mis à jour dans openDialog:', JSON.stringify(selectedOrganizations.value));
    }

    // Affecter les données
    editedItem.value = formData;
    console.log('[Debug][Orgs] editedItem après affectation:', JSON.stringify(editedItem.value?.organizations));
    
    // Mettre à jour le organizationsMap
    if (item.organizations && item.organizations_names) {
      item.organizations.forEach((orgId, index) => {
        if (item.organizations_names && item.organizations_names[index]) {
          organizationsMap.value.set(orgId, item.organizations_names[index]);
          console.log(`[Debug][Orgs] Mise à jour map: ${orgId} -> ${item.organizations_names[index]}`);
        }
      });
    }
  } else {
    // Réinitialiser pour un nouvel utilisateur
    selectedOrganizations.value = [];
    editedItem.value = {
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: RoleEnum.EMPLOYEE,
      organizations: [],
      organizations_names: [],
      phone_number: '',
      is_active: true,
      scan_preference: ScanPreferenceEnum.BOTH,
      simplified_mobile_view: false,
      password: ''
    };
  }

  // Afficher le formulaire
  nextTick(() => {
    dashboardView.value.showForm = true;
    console.log('[Debug][Orgs] État final:', {
      editedItem: JSON.stringify(editedItem.value?.organizations),
      selectedOrganizations: JSON.stringify(selectedOrganizations.value)
    });
  });
};

const saveUser = async () => {
  if (!form.value?.validate()) return

  saving.value = true
  formErrors.value = {}

  try {
    if (editedItem.value) {
      const userData = editedItem.value as UserFormData
      console.log('[Users][Save] Données utilisateur:', JSON.stringify(userData))

      // Vérifier la correspondance des mots de passe
      if (!userData.id && userData.password !== confirmPassword.value) {
        formErrors.value.confirm_password = ['Les mots de passe ne correspondent pas']
        saving.value = false
        return
      }

      // Utiliser les organisations sélectionnées dans le v-select
      const organizations = Array.isArray(selectedOrganizations.value) ? [...selectedOrganizations.value] : [];
      console.log('[Users][Save] Organisations à envoyer:', JSON.stringify(organizations))

      // S'assurer que editedItem.organizations est à jour avec selectedOrganizations
      if (editedItem.value) {
        editedItem.value.organizations = organizations;
      }

      // Générer les noms d'organisations basés sur les IDs sélectionnés
      userData.organizations_names = organizations.map(orgId => 
        organizationsMap.value.get(orgId) || '?'
      )

      if (userData.id) {
        await usersApi.updateUser(userData.id, {
          ...userData,
          organizations: organizations
        })
      } else {
        await usersApi.createUser({
          ...userData,
          organizations: organizations
        })
      }
      await loadUsers()
      dashboardView.value.showForm = false
      
      // Réinitialiser complètement l'état du formulaire après sauvegarde réussie
      resetFormState();
    }
  } catch (error: any) {
    console.error('[Users][Error] Erreur lors de la sauvegarde:', error)
    if (error.response?.data) {
      const processedErrors: Record<string, string[]> = {}
      Object.entries(error.response.data).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          processedErrors[field] = messages.map(message => {
            switch (message) {
              case "Ce champ ne peut être vide.":
              case "Ce champ est obligatoire.":
                return "Ce champ est obligatoire."
              case "Un utilisateur avec ce nom d'utilisateur existe déjà.":
                return "Ce nom d'utilisateur est déjà utilisé. Veuillez réessayer."
              default:
                return message
            }
          })
        } else {
          processedErrors[field] = [messages as string]
        }
      })
      formErrors.value = processedErrors
    }
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item: ExtendedUser) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de suppression'
  state.message = 'Êtes-vous sûr de vouloir supprimer cet utilisateur ?'
  state.confirmText = 'Supprimer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'error'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    await deleteUser(item)
    state.show = false
    state.loading = false
  }
}

const deleteUser = async (item: ExtendedUser) => {
  try {
    await usersApi.deleteUser(item.id)
    await loadUsers()
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
  }
}

const getRoleColor = (role: string): string => {
  switch (role) {
    case RoleEnum.SUPER_ADMIN:
      return 'error'
    case RoleEnum.ADMIN:
      return 'primary'
    case RoleEnum.MANAGER:
      return 'warning'
    case RoleEnum.EMPLOYEE:
      return 'success'
    default:
      return 'grey'
  }
}

const getRoleLabel = (role: string): string => {
  if (!role) return ''
  const found = roles.value.find(r => r.value === role)
  return found ? found.label : role
}

const toggleStatus = async (item: ExtendedUser) => {
  const state = dialogState.value as DialogState
  state.show = true
  state.title = 'Confirmation de changement de statut'
  state.message = `Êtes-vous sûr de vouloir ${item.is_active ? 'désactiver' : 'activer'} cet utilisateur ?`
  state.confirmText = item.is_active ? 'Désactiver' : 'Activer'
  state.cancelText = 'Annuler'
  state.confirmColor = 'warning'
  state.loading = false
  state.onConfirm = async () => {
    state.loading = true
    try {
      const newStatus = !item.is_active;
      await usersApi.toggleUserStatus(item.id, newStatus);
      await loadUsers();
    } catch (error) {
      console.error('[Users][Error] Erreur lors du changement de statut:', error);
    } finally {
      state.show = false
      state.loading = false
    }
  }
}

// Fonction pour réinitialiser complètement l'état du formulaire
const resetFormState = () => {
  // Réinitialiser les erreurs
  formErrors.value = {};
  
  // Réinitialiser le mot de passe et sa confirmation
  confirmPassword.value = '';
  showPassword.value = false;
  showConfirmPassword.value = false;
  
  // Réinitialiser la sélection des organisations
  selectedOrganizations.value = [];
  
  // Réinitialiser l'item édité
  editedItem.value = null;
  
  // Si le formulaire existe, réinitialiser sa validation
  if (form.value?.resetValidation) {
    form.value.resetValidation();
  }
}
</script>

<style scoped>
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

/* Style pour le bouton désactivé */
:deep(.disabled-button) {
  opacity: 0.5 !important;
  color: #999 !important;
  cursor: not-allowed !important;
}

:deep(.disabled-button .v-icon) {
  color: #999 !important;
}
</style>