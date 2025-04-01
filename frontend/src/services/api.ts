import axios from "axios"
import type { AxiosResponse } from "axios"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

// Intercepteur pour ajouter le token aux requêtes
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`

      // Ajouter des logs pour les données envoyées
      if (config.data) {
        console.log("Données envoyées dans la requête:", {
          url: config.url || '',
          method: config.method,
          data: config.data
        })
      }
    }
    return config
  },
  (error) => {
    console.error("Erreur dans l'intercepteur de requête:", error)
    return Promise.reject(error)
  }
)

// Intercepteur pour gérer les réponses
api.interceptors.response.use(
  (response) => {
    // Ajouter des logs pour la réponse
    console.log("Réponse reçue:", {
      url: response.config.url,
      method: response.config.method,
      status: response.status,
      data: response.data
    })
    return response
  },
  async (error) => {
    if (error.response) {
      console.error("Erreur de réponse:", {
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers
      })

      // If the error is due to an expired token (401)
      if (error.response.status === 401) {
        // Prevent infinite loop of refresh attempts
        if (error.config.url?.includes('/token/refresh/')) {
          // If refresh token request fails, clear everything and redirect to login
          localStorage.clear();
          // Clear all cookies
          document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
          });
          window.location.href = "/login";
          return Promise.reject(error);
        }

        // Only try to refresh if we haven't already tried
        if (!error.config.__isRetryRequest) {
          try {
            const refreshToken = localStorage.getItem("refreshToken")
            if (!refreshToken) {
              throw new Error("No refresh token available");
            }

            const response = await api.post("/users/token/refresh/", {
              refresh: refreshToken
            })
            const newToken = response.data.access
            localStorage.setItem("token", newToken)
            
            // Retry the original request with the new token
            error.config.headers.Authorization = `Bearer ${newToken}`
            error.config.__isRetryRequest = true
            return api(error.config)
          } catch (refreshError) {
            // If refresh fails, clear everything and redirect
            localStorage.clear();
            // Clear all cookies
            document.cookie.split(";").forEach(function(c) { 
              document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
            });
            window.location.href = "/login";
            return Promise.reject(refreshError)
          }
        }
      }
    }
    return Promise.reject(error)
  }
)

// Fonction utilitaire pour convertir camelCase en snake_case
const toSnakeCase = (str: string): string => {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

// Fonction pour convertir les clés d'un objet de camelCase à snake_case
const convertKeysToSnakeCase = (obj: any): any => {
  if (!obj) return obj;
  if (Array.isArray(obj)) {
    return obj.map(v => convertKeysToSnakeCase(v));
  } else if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((result: any, key) => {
      const value = obj[key];
      if (value !== undefined) {  // Ne pas inclure les valeurs undefined
        const snakeKey = toSnakeCase(key);
        result[snakeKey] = convertKeysToSnakeCase(value);
      }
      return result;
    }, {});
  }
  return obj;
}

// Types pour les réponses API
interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface Site {
  id: number;
  name: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  nfc_id: string;  // Format: S0001 à S9999
  organization: number;
  organization_name?: string;
  manager?: number | null;
  manager_name?: string;
  late_margin: number;
  early_departure_margin: number;
  ambiguous_margin: number;
  alert_emails: string;
  require_geolocation: boolean;
  geolocation_radius: number;
  allow_offline_mode: boolean;
  max_offline_duration: number;
  is_active: boolean;
  qr_code?: string;
  download_qr_code?: string;
  created_at: string;
  updated_at: string;
  schedules?: Schedule[];
}

interface SiteStatistics {
  total_employees: number;
  total_hours: number;
  anomalies: number;
}

interface Schedule {
  id: number;
  site: number;
  site_name: string;
  schedule_type: 'FIXED' | 'FREQUENCY';
  details: ScheduleDetail[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
  assigned_employees: Array<{
    id: any
    employee_name: any
    employee: number
  }>
}

interface ScheduleDetail {
  id?: number;
  day_of_week: number;
  frequency_duration?: number;
  start_time_1?: string;
  end_time_1?: string;
  start_time_2?: string;
  end_time_2?: string;
  day_type?: 'FULL' | 'AM' | 'PM';
}

interface Employee {
  id: number;
  employee_name: string;
  first_name: string;
  last_name: string;
  email: string;
  organization: number;
  employee?: number;
}

interface Organization {
  id: number;
  name: string;
  org_id: string;
  address?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  phone?: string;
  contact_email?: string;
  siret?: string;
  logo?: string | null;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_active?: boolean;
}

// Utilitaires pour la validation des IDs de sites
const validateSiteId = (siteId: string): boolean => {
  if (!siteId || siteId.length !== 5) return false;
  if (!siteId.startsWith('S')) return false;
  try {
    const number = parseInt(siteId.slice(1));
    return number > 0 && number < 10000;
  } catch {
    return false;
  }
};

// Sites API methods
const sitesApi = {
  // Get all sites with pagination
  getAllSites: (page = 1, perPage = 10, params: { organization?: number, organizations?: number[] } = {}): Promise<AxiosResponse<ApiResponse<Site>>> => {
    const queryParams: Record<string, any> = {
      page,
      page_size: perPage,
      expand: 'schedules',
      ...params
    }
    
    // Si organizations est fourni, le convertir en chaîne de caractères
    if (params.organizations?.length) {
      queryParams.organizations = params.organizations.join(',')
    }
    
    return api.get('/sites/', { params: queryParams })
  },
  
  // Get a single site by ID
  getSite: (id: number): Promise<AxiosResponse<Site>> => api.get(`/sites/${id}/`),
  
  // Get site statistics
  getSiteStatistics: (id: number): Promise<AxiosResponse<SiteStatistics>> => 
    api.get(`/sites/${id}/statistics/`),
  
  // Create a new site
  createSite: (data: Partial<Site>): Promise<AxiosResponse<Site>> => {
    // Supprime le nfc_id s'il est fourni car il est généré côté serveur
    const { nfc_id, ...siteData } = convertKeysToSnakeCase(data);
    return api.post('/sites/', siteData);
  },
  
  // Update a site
  updateSite: (id: number, data: Partial<Site>): Promise<AxiosResponse<Site>> => {
    // Supprime le nfc_id s'il est fourni car il ne doit pas être modifié
    const { nfc_id, ...siteData } = convertKeysToSnakeCase(data);
    return api.patch(`/sites/${id}/`, siteData);
  },
  
  // Delete a site
  deleteSite: (id: number): Promise<AxiosResponse<void>> => api.delete(`/sites/${id}/`),
  
  // Schedule methods
  createSchedule: (siteId: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.post(`/sites/${siteId}/schedules/`, convertKeysToSnakeCase(data)),
  
  updateSchedule: (siteId: number, scheduleId: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.put(`/sites/${siteId}/schedules/${scheduleId}/`, convertKeysToSnakeCase(data)),
  
  deleteSchedule: (siteId: number, scheduleId: number): Promise<AxiosResponse<void>> => 
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/`),
  
  // Schedule details methods
  getScheduleDetails: (siteId: number, scheduleId: number): Promise<AxiosResponse<Schedule>> =>
    api.get(`/sites/${siteId}/schedules/${scheduleId}/`),

  createScheduleDetail: (siteId: number, scheduleId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> => 
    api.post(`/sites/${siteId}/schedules/${scheduleId}/details/`, convertKeysToSnakeCase(data)),

  updateScheduleDetail: (siteId: number, scheduleId: number, detailId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> =>
    api.put(`/sites/${siteId}/schedules/${scheduleId}/details/${detailId}/`, convertKeysToSnakeCase(data)),

  deleteScheduleDetail: (siteId: number, scheduleId: number, detailId: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/details/${detailId}/`),

  getScheduleEmployees: (siteId: number, scheduleId: number): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/${siteId}/schedules/${scheduleId}/employees/`),

  getSiteEmployees: (siteId: number, params?: { role?: string }): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/${siteId}/employees/`, { params }),

  // Get schedules by site
  getSchedulesBySite: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> => 
    api.get(`/sites/${siteId}/schedules/`),

  // Obtenir les employés qui ne sont pas encore assignés au site
  getUnassignedEmployees: (siteId: number): Promise<AxiosResponse<ApiResponse<Employee>>> => 
    api.get(`/sites/${siteId}/unassigned-employees/`),

  // Assigner un employé à un site
  assignEmployee: (siteId: number, employeeId: number): Promise<AxiosResponse<void>> => 
    api.post(`/sites/${siteId}/employees/`, { employee: employeeId }),

  // Désassigner un employé d'un site
  unassignEmployee: (siteId: number, employeeId: number): Promise<AxiosResponse<void>> => 
    api.delete(`/sites/${siteId}/employees/${employeeId}/`),
}

// Schedules API methods
const schedulesApi = {
  // Get all schedules with pagination
  getAllSchedules: (params: {
    page?: number;
    page_size?: number;
    site?: number;
    schedule_type?: string;
  }): Promise<AxiosResponse<ApiResponse<Schedule>>> => 
    api.get('/sites/schedules/', { params }),
  
  // Get schedules by site
  getSchedulesBySite: (siteId: number): Promise<AxiosResponse<Schedule[]>> => 
    api.get(`/sites/${siteId}/schedules/`),
  
  // Get a single schedule by ID
  getSchedule: (id: number): Promise<AxiosResponse<Schedule>> => api.get(`/sites/schedules/${id}/`),
  
  // Create a new schedule
  createSchedule: (data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.post('/sites/schedules/', convertKeysToSnakeCase(data)),
  
  // Update a schedule
  updateSchedule: (id: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.put(`/sites/schedules/${id}/`, convertKeysToSnakeCase(data)),
  
  // Delete a schedule
  deleteSchedule: (id: number): Promise<AxiosResponse<void>> => api.delete(`/sites/schedules/${id}/`),
  
  // Get schedule details
  getScheduleDetails: (scheduleId: number): Promise<AxiosResponse<Schedule>> => 
    api.get(`/sites/schedules/${scheduleId}/details/`),
  
  // Create schedule detail
  createScheduleDetail: (scheduleId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> => 
    api.post(`/sites/schedules/${scheduleId}/details/`, convertKeysToSnakeCase(data)),
  
  // Update schedule detail
  updateScheduleDetail: (scheduleId: number, detailId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> => 
    api.put(`/sites/schedules/${scheduleId}/details/${detailId}/`, convertKeysToSnakeCase(data)),
  
  // Delete schedule detail
  deleteScheduleDetail: (scheduleId: number, detailId: number): Promise<AxiosResponse<void>> => 
    api.delete(`/sites/schedules/${scheduleId}/details/${detailId}/`),

  // Employee management
  getAvailableEmployees: (): Promise<AxiosResponse<ApiResponse<Employee>>> => api.get('/users/', {
    params: {
      role: 'EMPLOYEE',
      is_active: true
    }
  }),

  assignEmployee: (siteId: number, scheduleId: number, employeeId: number): Promise<AxiosResponse<void>> => 
    api.post(`/sites/${siteId}/schedules/${scheduleId}/employees/`, { 
      site: siteId,
      employee: employeeId,
      schedule: scheduleId
    }),

  unassignEmployee: (siteId: number, scheduleId: number, employeeId: number): Promise<AxiosResponse<void>> => 
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/employees/${employeeId}/`),

  getScheduleEmployees: (siteId: number, scheduleId: number): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/${siteId}/schedules/${scheduleId}/employees/`),

  // Assigner plusieurs employés à un planning
  assignMultipleEmployees: (siteId: number, scheduleId: number, employeeIds: number[]): Promise<AxiosResponse<void>> => 
    api.post(`/sites/${siteId}/schedules/${scheduleId}/employees/batch/`, { 
      site: siteId,
      employees: employeeIds,
      schedule: scheduleId
    }),
}

// Users API methods
const usersApi = {
  // Get user profile
  getProfile: () => api.get('/users/profile/'),
  
  // Get all users with filters
  getAllUsers: (params: any = {}) => api.get('/users/', { params }),
  
  // Get a single user by ID
  getUser: (id: number) => api.get(`/users/${id}/`),
  
  // Create a new user
  createUser: (data: any) => {
    const userData = {
      ...convertKeysToSnakeCase(data),
      organizations: data.organizations
    }
    return api.post('/users/register/', userData)
  },
  
  // Update a user
  updateUser: (id: number, data: any) => {
    const userData = {
      ...convertKeysToSnakeCase(data),
      organizations: data.organizations
    }
    return api.patch(`/users/${id}/`, userData)
  },
  
  // Delete a user
  deleteUser: (id: number) => api.delete(`/users/${id}/`),
  
  // Get user statistics
  getUserStatistics: (id: number) => api.get(`/users/${id}/statistics/`),
  
  // Update user profile
  updateProfile: (data: any) => {
    interface ProfileData {
      first_name: string;
      last_name: string;
      email: string;
      phone_number: string;
      username: string;
      scan_preference?: string;
      simplified_mobile_view?: boolean;
    }
    
    const profileData: ProfileData = {
      first_name: data.firstName,
      last_name: data.lastName,
      email: data.email,
      phone_number: data.phone,
      username: data.username,
    }
    
    // Ajouter scan_preference et simplified_mobile_view uniquement pour les employés
    if (data.role === 'EMPLOYEE') {
      profileData.scan_preference = data.scanPreference
      profileData.simplified_mobile_view = data.simplifiedMobileView
    }
    
    return api.put('/users/profile/', convertKeysToSnakeCase(profileData))
  },
  
  // Update user preferences
  updatePreferences: (data: { simplifiedMobileView: boolean }) => {
    return api.patch('/users/profile/', convertKeysToSnakeCase({
      simplified_mobile_view: data.simplifiedMobileView
    }))
  },
  
  // Change password
  changePassword: (data: any) => api.post('/users/change-password/', {
    old_password: data.currentPassword,
    new_password: data.newPassword
  }),

  // Search users
  searchUsers: (query: string) => api.get('/users/', {
    params: {
      search: query,
      role: 'EMPLOYEE',
      is_active: true
    }
  }),

  // Activer/désactiver un utilisateur
  toggleUserStatus: (id: number, isActive: boolean) => 
    api.patch(`/users/${id}/`, { is_active: isActive }),
}

// Organizations API methods
const organizationsApi = {
  // Get all organizations with pagination
  getAllOrganizations: (params: {
    page?: number;
    page_size?: number;
    search?: string;
  } = {}) => api.get('/organizations/', { params }),
  
  // Get a single organization by ID
  getOrganization: (id: number) => api.get(`/organizations/${id}/`),
  
  // Create a new organization
  createOrganization: (data: Partial<Organization>) => 
    api.post('/organizations/', convertKeysToSnakeCase(data)),
  
  // Update an organization
  updateOrganization: (id: number, data: Partial<Organization>) => 
    api.patch(`/organizations/${id}/`, convertKeysToSnakeCase(data)),
  
  // Delete an organization
  deleteOrganization: (id: number) => 
    api.delete(`/organizations/${id}/`),
  
  // Get organization users
  getOrganizationUsers: (id: number) => 
    api.get(`/organizations/${id}/users/`),
  
  // Get organization statistics
  getOrganizationStatistics: (id: number) => 
    api.get(`/organizations/${id}/statistics/`),

  // Get organization sites
  getOrganizationSites: (id: number, page = 1, perPage = 10) => 
    api.get(`/organizations/${id}/sites/`, {
      params: {
        page,
        page_size: perPage
      }
    }),

  // Activer/désactiver une organisation
  toggleOrganizationStatus: (id: number, isActive: boolean) => 
    api.patch(`/organizations/${id}/`, { is_active: isActive }),
    
  // Obtenir les employés qui ne sont pas encore assignés à l'organisation
  getUnassignedEmployees: (id: number) => 
    api.get(`/organizations/${id}/unassigned-employees/`, {
      params: {
        role: ['EMPLOYEE', 'MANAGER']  // Filtrer pour ne montrer que les employés et managers
      }
    }),
    
  // Obtenir les sites qui ne sont pas encore assignés à l'organisation
  getUnassignedSites: (id: number) => 
    api.get(`/organizations/${id}/unassigned-sites/`),
    
  // Assigner un employé à une organisation
  assignEmployee: (organizationId: number, employeeId: number) => 
    api.post(`/organizations/${organizationId}/assign-employee/`, { employee_id: employeeId }),
    
  // Assigner un site à une organisation
  assignSite: (organizationId: number, siteId: number) => 
    api.post(`/organizations/${organizationId}/assign-site/`, { site_id: siteId }),
}

// Timesheets API methods
const timesheetsApi = {
  // Get all timesheets with filters and pagination
  getTimesheets: (params: any = {}) => {
    const queryParams = convertKeysToSnakeCase(params);
    return api.get('/timesheets/', { params: queryParams });
  },

  // Get a single timesheet by ID
  getTimesheet: (id: number) => api.get(`/timesheets/${id}/`),

  // Update a timesheet
  updateTimesheet: (id: number, data: any) => 
    api.put(`/timesheets/${id}/`, convertKeysToSnakeCase(data)),

  // Delete a timesheet
  deleteTimesheet: (id: number) => 
    api.delete(`/timesheets/${id}/`),

  // Get anomalies
  getAnomalies: (params: any = {}) => {
    const queryParams = convertKeysToSnakeCase(params);
    return api.get('/timesheets/anomalies/', { params: queryParams });
  },

  // Update anomaly
  updateAnomaly: (id: number, data: any) =>
    api.patch(`/timesheets/anomalies/${id}/`, convertKeysToSnakeCase(data)),

  // Scan for anomalies
  scanAnomalies: (params: any = {}) => {
    const queryParams = convertKeysToSnakeCase(params);
    return api.post('/timesheets/scan-anomalies/', { params: queryParams });
  },

  // Get timesheets for a specific site
  getSiteTimesheets: (siteId: number, params: any = {}) => {
    const queryParams = convertKeysToSnakeCase({
      site: siteId,
      ...params
    });
    return api.get('/timesheets/', { params: queryParams });
  },

  // Get user statistics
  getUserStats: () => api.get('/timesheets/reports/'),

  // Report an anomaly
  reportAnomaly: (data: any) => 
    api.post('/timesheets/anomalies/', convertKeysToSnakeCase(data)),

  // Get dashboard statistics
  getDashboardStats: async () => {
    const today = new Date().toISOString().split('T')[0];
    const [sitesResponse, employeesResponse, timesheetsResponse] = await Promise.all([
      sitesApi.getAllSites(),
      usersApi.searchUsers(''),
      timesheetsApi.getTimesheets({
        start_date: today,
        end_date: today
      })
    ]);

    return {
      sitesCount: sitesResponse.data?.count || sitesResponse.data?.results?.length || 0,
      employeesCount: employeesResponse.data?.count || employeesResponse.data?.results?.length || 0,
      timesheetsCount: timesheetsResponse.data?.count || timesheetsResponse.data?.results?.length || 0
    };
  },

  // Build query parameters for anomalies
  buildAnomalyQueryParams: (filters: any, currentSiteId?: number) => {
    const params: any = {};
    
    if (filters.employee) {
      params.employee = filters.employee;
    }
    if (currentSiteId) {
      params.site = currentSiteId;
    } else if (filters.site) {
      params.site = filters.site;
    }
    if (filters.type) {
      params.anomaly_type = filters.type;
    }
    if (filters.status) {
      params.status = filters.status;
    }
    if (filters.startDate) {
      params.start_date = filters.startDate;
    }
    if (filters.endDate) {
      params.end_date = filters.endDate;
    }
    
    return params;
  },

  // Get timesheet details
  getTimesheetDetails: (id: number) => 
    api.get(`/timesheets/${id}/details/`),

  // Get anomaly details
  getAnomalyDetails: (id: number) => 
    api.get(`/timesheets/anomalies/${id}/`),

  // Resolve anomaly
  resolveAnomaly: (id: number) => 
    api.patch(`/timesheets/anomalies/${id}/`, { status: 'RESOLVED' }),

  // Ignore anomaly
  ignoreAnomaly: (id: number) => 
    api.patch(`/timesheets/anomalies/${id}/`, { status: 'IGNORED' }),
}

// Anomalies API methods
const anomaliesApi = {
  getAnomaliesBySite: (siteId: number) => 
    api.get(`/timesheets/anomalies/`, { params: { site: siteId } }),
  
  updateAnomaly: (id: number, data: any) => 
    api.patch(`/timesheets/anomalies/${id}/`, convertKeysToSnakeCase(data))
}

// Reports API methods
const reportsApi = {
  getReportsBySite: (siteId: number) => 
    api.get(`/reports/`, { params: { site: siteId } }),

  // Get reports for a specific site
  getSiteReports: (siteId: number) => 
    api.get(`/reports/`, { params: { site: siteId } }),

  // Download report
  downloadReport: (reportId: number) => 
    api.get(`/reports/${reportId}/download/`, { 
      responseType: 'blob',
      headers: {
        'Accept': 'application/pdf'
      }
    }),
}

// Plannings API methods
const planningsApi = {
  // Get all plannings with pagination
  getAllPlannings: (params: { 
    page?: number;
    page_size?: number;
    site?: number;
    schedule_type?: string;
  }): Promise<AxiosResponse<ApiResponse<Schedule>>> => 
    api.get('/sites/schedules/', { params }),
  
  // Get a single planning by ID
  getPlanning: (id: number): Promise<AxiosResponse<Schedule>> => 
    api.get(`/sites/schedules/${id}/`),
  
  // Create a new planning
  createPlanning: (data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.post('/sites/schedules/', convertKeysToSnakeCase(data)),
  
  // Update a planning
  updatePlanning: (id: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => 
    api.put(`/sites/schedules/${id}/`, convertKeysToSnakeCase(data)),
  
  // Delete a planning
  deletePlanning: (id: number): Promise<AxiosResponse<void>> => 
    api.delete(`/sites/schedules/${id}/`),

  // Get plannings by site
  getPlanningsBySite: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> => 
    api.get(`/sites/${siteId}/schedules/`),
}

// Access Management API methods
const accessManagementApi = {
  // Get all access rights
  getAllAccessRights: (page = 1, perPage = 10): Promise<AxiosResponse<ApiResponse<any>>> => 
    api.get('/access-rights/', {
      params: {
        page,
        page_size: perPage
      }
    }),

  // Get access rights for a specific user
  getUserAccessRights: (userId: number): Promise<AxiosResponse<any>> => 
    api.get(`/users/${userId}/access-rights/`),

  // Update user access rights
  updateUserAccessRights: (userId: number, data: any): Promise<AxiosResponse<any>> => 
    api.put(`/users/${userId}/access-rights/`, convertKeysToSnakeCase(data)),

  // Get access rights for a specific site
  getSiteAccessRights: (siteId: number): Promise<AxiosResponse<any>> => 
    api.get(`/sites/${siteId}/access-rights/`),

  // Update site access rights
  updateSiteAccessRights: (siteId: number, data: any): Promise<AxiosResponse<any>> => 
    api.put(`/sites/${siteId}/access-rights/`, convertKeysToSnakeCase(data)),
}

// Export all types and APIs
export type { 
  Site, 
  Schedule, 
  Employee, 
  Organization, 
  ScheduleDetail,
  ApiResponse,
  SiteStatistics
}

export { 
  sitesApi, 
  schedulesApi, 
  usersApi, 
  timesheetsApi, 
  organizationsApi,
  anomaliesApi,
  reportsApi,
  planningsApi,
  accessManagementApi
}

export default api

