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
      console.log("Ajout du token à la requête:", {
        url: config.url || '',
        method: config.method,
        baseURL: config.baseURL || '',
        fullURL: (config.baseURL || '') + (config.url || ''),
        token: token.substring(0, 10) + "..."
      })

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

interface Schedule {
  id: number;
  site: number;
  site_name: string;
  schedule_type: 'FIXED' | 'FREQUENCY';
  details: ScheduleDetail[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
  assigned_employees: Array<{ employee: number }>;
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
  getAllSites: (page = 1, perPage = 10): Promise<AxiosResponse<ApiResponse<Site>>> => {
    return api.get('/sites/', {
      params: {
        page,
        page_size: perPage,
        expand: 'schedules'
      }
    })
  },
  
  // Get a single site by ID
  getSite: (id: number): Promise<AxiosResponse<Site>> => api.get(`/sites/${id}/`),
  
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

  getSiteEmployees: (siteId: number): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/${siteId}/employees/`),

  // Get schedules by site
  getSchedulesBySite: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> => 
    api.get(`/sites/${siteId}/schedules/`),
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
    api.get(`/sites/${siteId}/schedules/${scheduleId}/employees/`)
}

// Users API methods
const usersApi = {
  // Get user profile
  getProfile: () => api.get('/users/profile/'),
  
  // Get all users with filters
  getAllUsers: (params: any = {}) => api.get('/users/', { params }),
  
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
  })
}

// Organizations API methods
const organizationsApi = {
  // Get all organizations
  getAllOrganizations: () => api.get('/organizations/'),
  
  // Get a single organization by ID
  getOrganization: (id: number) => api.get(`/organizations/${id}/`)
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
  }
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
    api.get(`/reports/`, { params: { site: siteId } })
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
  ApiResponse 
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

