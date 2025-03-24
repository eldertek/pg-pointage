import api from './api'

export const employeesService = {
  // Récupérer la liste des employés
  async getEmployees(page = 1, perPage = 10) {
    const response = await api.get('/users/', {
      params: {
        role: 'EMPLOYEE',
        page,
        page_size: perPage
      }
    })
    return {
      results: response.data.results,
      total: response.data.count
    }
  },

  // Récupérer un employé spécifique
  async getEmployee(id) {
    const response = await api.get(`/users/${id}/`)
    return response.data
  },

  // Créer un nouvel employé
  async createEmployee(employeeData) {
    const response = await api.post('/users/', {
      ...employeeData,
      role: 'EMPLOYEE'
    })
    return response.data
  },

  // Mettre à jour un employé
  async updateEmployee(id, employeeData) {
    const response = await api.patch(`/users/${id}/`, employeeData)
    return response.data
  },

  // Supprimer un employé
  async deleteEmployee(id) {
    await api.delete(`/users/${id}/`)
  },

  // Activer/désactiver un employé
  async toggleEmployeeStatus(id, isActive) {
    const response = await api.patch(`/users/${id}/`, {
      is_active: isActive
    })
    return response.data
  }
}

export default employeesService 