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
  name: string;  // required
  address: string;  // required
  postal_code: string;  // required
  city: string;  // required
  country: string;  // optional, default: 'France'
  nfc_id: string;  // read-only
  organization: number;  // required
  organization_name?: string;  // read-only
  manager?: number | null;  // optional
  manager_name?: string;  // read-only
  late_margin: number;  // optional, default: 15
  early_departure_margin: number;  // optional, default: 15
  ambiguous_margin: number;  // optional, default: 20
  alert_emails: string;  // optional
  require_geolocation: boolean;  // optional, default: true
  geolocation_radius: number;  // optional, default: 100
  allow_offline_mode: boolean;  // optional, default: true
  max_offline_duration: number;  // optional, default: 24
  is_active: boolean;  // optional, default: true
  qr_code?: string;  // optional
  download_qr_code?: string;  // optional
  created_at: string;  // read-only
  updated_at: string;  // read-only
  schedules?: Schedule[];  // optional
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
    console.log('[SitesAPI][Create] Données reçues:', data)
    const siteData = convertKeysToSnakeCase(data)
    console.log('[SitesAPI][Create] Données converties:', siteData)
    return api.post('/sites/', siteData)
  },

  // Update a site
  updateSite: (id: number, data: Partial<Site>): Promise<AxiosResponse<Site>> => {
    const siteData = convertKeysToSnakeCase(data);
    return api.patch(`/sites/${id}/`, siteData);
  },

  // Delete a site
  deleteSite: (id: number): Promise<AxiosResponse<void>> => api.delete(`/sites/${id}/`),

  // Get site employees
  getSiteEmployees: (siteId: number, params?: { role?: string }): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/${siteId}/employees/`, { params }),

  // Get site schedules
  getSiteSchedules: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> =>
    api.get(`/sites/${siteId}/schedules/`),

  // Get a single schedule
  getSchedule: (siteId: number, scheduleId: number): Promise<AxiosResponse<Schedule>> =>
    api.get(`/sites/${siteId}/schedules/${scheduleId}/`),

  // Create a new schedule
  createSchedule: (siteId: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> =>
    api.post(`/sites/${siteId}/schedules/`, convertKeysToSnakeCase(data)),

  // Update a schedule
  updateSchedule: (siteId: number, scheduleId: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> =>
    api.patch(`/sites/${siteId}/schedules/${scheduleId}/`, convertKeysToSnakeCase(data)),

  // Delete a schedule
  deleteSchedule: (siteId: number, scheduleId: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/`),

  // Get schedule details
  getScheduleDetails: (siteId: number, scheduleId: number): Promise<AxiosResponse<Schedule>> =>
    api.get(`/sites/${siteId}/schedules/${scheduleId}/details/`),

  // Create schedule detail
  createScheduleDetail: (siteId: number, scheduleId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> =>
    api.post(`/sites/${siteId}/schedules/${scheduleId}/details/`, convertKeysToSnakeCase(data)),

  // Update schedule detail
  updateScheduleDetail: (siteId: number, scheduleId: number, detailId: number, data: Partial<ScheduleDetail>): Promise<AxiosResponse<ScheduleDetail>> =>
    api.put(`/sites/${siteId}/schedules/${scheduleId}/details/${detailId}/`, convertKeysToSnakeCase(data)),

  // Delete schedule detail
  deleteScheduleDetail: (siteId: number, scheduleId: number, detailId: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/details/${detailId}/`),

  // Assign employees to schedule
  assignEmployeesToSchedule: (siteId: number, scheduleId: number, employeeIds: number[]): Promise<AxiosResponse<void>> =>
    api.post(`/sites/${siteId}/schedules/${scheduleId}/employees/batch/`, {
      employees: employeeIds
    }),

  // Get site pointages
  getSitePointages: (siteId: number, params: any = {}) =>
    api.get(`/sites/${siteId}/pointages/`, { params }),

  // Get site anomalies
  getSiteAnomalies: (siteId: number, params: any = {}) =>
    api.get(`/sites/${siteId}/anomalies/`, { params }),

  // Get site reports
  getSiteReports: (siteId: number, params: any = {}) =>
    api.get(`/sites/${siteId}/reports/`, { params }),

  // Download a report
  downloadReport: (siteId: number, reportId: number) =>
    api.get(`/sites/${siteId}/reports/${reportId}/download/`, { responseType: 'blob' }),

  // Unassign employee from site
  unassignEmployee: (siteId: number, employeeId: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/${siteId}/employees/${employeeId}/`),

  // Get site plannings with custom URL
  getSitePlannings: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> =>
    api.get(`/plannings/site/${siteId}/`),
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
  getSchedule: (id: number): Promise<AxiosResponse<Schedule>> =>
    api.get(`/sites/schedules/${id}/`),

  // Get schedule statistics
  getScheduleStatistics: (id: number): Promise<AxiosResponse<any>> =>
    api.get(`/sites/schedules/${id}/statistics/`),

  // Get schedule employees
  getScheduleEmployees: (id: number): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/sites/schedules/${id}/employees/`),

  // Create a new schedule
  createSchedule: (data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => {
    if (!data.site) {
      throw new Error('Le site est requis pour créer un planning')
    }
    return api.post(`/sites/${data.site}/schedules/`, convertKeysToSnakeCase(data))
  },

  // Update a schedule
  updateSchedule: (siteId: number, scheduleId: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> => {
    console.log('[SchedulesAPI][Update] Mise à jour du planning:', {
      siteId,
      scheduleId,
      data: convertKeysToSnakeCase(data)
    })
    // Utiliser l'endpoint direct des plannings au lieu de l'endpoint spécifique au site
    // Cela permet de mettre à jour un planning même s'il n'appartient pas au site spécifié
    return api.patch(`/sites/schedules/${scheduleId}/`, convertKeysToSnakeCase(data))
  },

  // Delete a schedule
  deleteSchedule: (id: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/schedules/${id}/`),

  // Employee management
  assignEmployee: (siteId: number, scheduleId: number, employeeId: number): Promise<AxiosResponse<void>> =>
    api.post(`/sites/${siteId}/schedules/${scheduleId}/employees/`, {
      site: siteId,
      employee: employeeId,
      schedule: scheduleId
    }),

  unassignEmployee: (scheduleId: number, employeeId: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/schedules/${scheduleId}/employees/${employeeId}/`),

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

  // Get user sites
  getUserSites: (id: number, params: any = {}) => api.get(`/users/${id}/sites/`, { params }),

  // Get user schedules
  getUserSchedules: (id: number, params: any = {}) => api.get(`/users/${id}/schedules/`, { params }),

  // Get user reports
  getUserReports: (id: number, params: any = {}) => api.get(`/users/${id}/reports/`, { params }),

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
  changePassword: (data: any) => api.post('/users/auth/change-password/', {
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

  // Get organization timesheets
  getOrganizationTimesheets: (id: number, params: any = {}) =>
    api.get(`/organizations/${id}/timesheets/`, { params }),

  // Get organization anomalies
  getOrganizationAnomalies: (id: number, params: any = {}) =>
    api.get(`/organizations/${id}/anomalies/`, { params }),

  // Get organization reports
  getOrganizationReports: (id: number, params: any = {}) =>
    api.get(`/organizations/${id}/reports/`, { params }),

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

  // Get organization employees
  getOrganizationEmployees: (id: number, params: { role?: string } = {}): Promise<AxiosResponse<ApiResponse<Employee>>> =>
    api.get(`/organizations/${id}/employees/`, { params }),
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
  getAllReports: (params: {
    search?: string;
    type?: string;
    format?: string;
    site?: number;
    page?: number;
    page_size?: number;
  } = {}) => {
    console.log('[ReportsAPI][GetAll] Params:', params)
    return api.get('/reports/', { params: convertKeysToSnakeCase(params) })
  },

  generateReport: (data: {
    name: string;
    type: string;
    format: string;
    start_date: string;
    end_date: string;
    site?: number;
  }) => {
    console.log('[ReportsAPI][Generate] Data:', data)
    const requestData = {
      name: data.name,
      report_type: data.type,
      report_format: data.format,
      start_date: data.start_date,
      end_date: data.end_date,
      site: data.site
    }
    return api.post('/reports/generate/', requestData)
  },

  downloadReport: (id: number) => {
    console.log('[ReportsAPI][Download] ID:', id)
    return api.get(`/reports/${id}/download/`, {
      responseType: 'blob',
      headers: {
        'Accept': '*/*'
      }
    })
  },

  deleteReport: (id: number) => {
    console.log('[ReportsAPI][Delete] ID:', id)
    return api.delete(`/reports/${id}/delete/`)
  }
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

  // Get plannings for a site
  getSitePlannings: (siteId: number): Promise<AxiosResponse<ApiResponse<Schedule>>> =>
    api.get(`/sites/${siteId}/schedules/`),

  // Create a new planning
  createPlanning: (data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> =>
    api.post('/sites/schedules/', convertKeysToSnakeCase(data)),

  // Update a planning
  updatePlanning: (id: number, data: Partial<Schedule>): Promise<AxiosResponse<Schedule>> =>
    api.put(`/sites/schedules/${id}/`, convertKeysToSnakeCase(data)),

  // Delete a planning
  deletePlanning: (id: number): Promise<AxiosResponse<void>> =>
    api.delete(`/sites/schedules/${id}/`),
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

