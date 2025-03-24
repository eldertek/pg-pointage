import axios from "axios"

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
        url: config.url,
        method: config.method,
        baseURL: config.baseURL,
        fullURL: config.baseURL + config.url,
        token: token.substring(0, 10) + "..."
      })

      // Ajouter des logs pour les données envoyées
      if (config.data) {
        console.log("Données envoyées dans la requête:", {
          url: config.url,
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

      // If the error is due to an expired token (401), try to refresh it
      if (error.response.status === 401 && error.config && !error.config.__isRetryRequest) {
        try {
          const refreshToken = localStorage.getItem("refreshToken")
          if (refreshToken) {
            const response = await api.post("/users/token/refresh/", {
              refresh: refreshToken
            })
            const newToken = response.data.access
            localStorage.setItem("token", newToken)
            
            // Retry the original request with the new token
            error.config.headers.Authorization = `Bearer ${newToken}`
            error.config.__isRetryRequest = true
            return api(error.config)
          }
        } catch (refreshError) {
          // If refresh token fails, clear tokens and redirect to login
          localStorage.removeItem("token")
          localStorage.removeItem("refreshToken")
          window.location.href = "/login"
          return Promise.reject(refreshError)
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
  if (Array.isArray(obj)) {
    return obj.map(v => convertKeysToSnakeCase(v));
  } else if (obj !== null && obj.constructor === Object) {
    return Object.keys(obj).reduce((result: any, key) => {
      const snakeKey = toSnakeCase(key);
      result[snakeKey] = convertKeysToSnakeCase(obj[key]);
      return result;
    }, {});
  }
  return obj;
}

// Sites API methods
const sitesApi = {
  // Get all sites with pagination
  getAllSites: (page = 1, perPage = 10) => 
    api.get('/sites/', { 
      params: { 
        page,
        page_size: perPage 
      }
    }),
  
  // Get a single site by ID
  getSite: (id: number) => api.get(`/sites/${id}/`),
  
  // Create a new site
  createSite: (data: any) => api.post('/sites/', convertKeysToSnakeCase(data)),
  
  // Update a site
  updateSite: (id: number, data: any) => api.put(`/sites/${id}/`, convertKeysToSnakeCase(data)),
  
  // Delete a site
  deleteSite: (id: number) => api.delete(`/sites/${id}/`),
  
  // Schedule methods
  createSchedule: (siteId: number, data: any) => 
    api.post(`/sites/${siteId}/schedules/`, convertKeysToSnakeCase(data)),
  
  updateSchedule: (siteId: number, scheduleId: number, data: any) => 
    api.put(`/sites/${siteId}/schedules/${scheduleId}/`, convertKeysToSnakeCase(data)),
  
  deleteSchedule: (siteId: number, scheduleId: number) => 
    api.delete(`/sites/${siteId}/schedules/${scheduleId}/`),
  
  // Schedule details methods
  createScheduleDetails: (siteId: number, scheduleId: number, data: any) => 
    api.post(`/sites/${siteId}/schedules/${scheduleId}/details/`, convertKeysToSnakeCase(data)),
  
  // Employee assignment methods
  assignEmployee: (siteId: number, data: any) => 
    api.post(`/sites/${siteId}/employees/`, convertKeysToSnakeCase(data)),
  
  unassignEmployee: (siteId: number, employeeId: number) => 
    api.delete(`/sites/${siteId}/employees/${employeeId}/`),
  
  updateEmployeeAssignment: (siteId: number, employeeId: number, data: any) => 
    api.put(`/sites/${siteId}/employees/${employeeId}/`, convertKeysToSnakeCase(data))
}

// Schedules API methods
const schedulesApi = {
  // Get all schedules with pagination
  getAllSchedules: (page = 1, perPage = 10) => 
    api.get('/schedules/', { 
      params: { 
        page,
        page_size: perPage 
      }
    }),
  
  // Get a single schedule by ID
  getSchedule: (id: number) => api.get(`/schedules/${id}/`),
  
  // Create a new schedule
  createSchedule: (data: any) => api.post('/schedules/', convertKeysToSnakeCase(data)),
  
  // Update a schedule
  updateSchedule: (id: number, data: any) => api.put(`/schedules/${id}/`, convertKeysToSnakeCase(data)),
  
  // Delete a schedule
  deleteSchedule: (id: number) => api.delete(`/schedules/${id}/`),
  
  // Get schedule details
  getScheduleDetails: (scheduleId: number) => api.get(`/schedules/${scheduleId}/details/`),
  
  // Create schedule detail
  createScheduleDetail: (scheduleId: number, data: any) => 
    api.post(`/schedules/${scheduleId}/details/`, convertKeysToSnakeCase(data)),
  
  // Update schedule detail
  updateScheduleDetail: (scheduleId: number, detailId: number, data: any) => 
    api.put(`/schedules/${scheduleId}/details/${detailId}/`, convertKeysToSnakeCase(data)),
  
  // Delete schedule detail
  deleteScheduleDetail: (scheduleId: number, detailId: number) => 
    api.delete(`/schedules/${scheduleId}/details/${detailId}/`),
  
  // Get employees assigned to a schedule
  getScheduleEmployees: (scheduleId: number) => api.get(`/schedules/${scheduleId}/employees/`),
  
  // Assign employee to schedule
  assignEmployee: (scheduleId: number, data: any) => 
    api.post(`/schedules/${scheduleId}/employees/`, convertKeysToSnakeCase(data)),
  
  // Unassign employee from schedule
  unassignEmployee: (scheduleId: number, employeeId: number) => 
    api.delete(`/schedules/${scheduleId}/employees/${employeeId}/`)
}

export { sitesApi, schedulesApi }
export default api

