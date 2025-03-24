import api from './api'

export const employeesService = {
  // Récupérer la liste des employés
  async getEmployees() {
    const response = await api.get('/users/', {
      params: {
        role: 'EMPLOYEE'
      }
    })
    return response.data
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