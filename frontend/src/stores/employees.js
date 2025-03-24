import { defineStore } from 'pinia'
import { employeesService } from '@/services/employees'

export const useEmployeesStore = defineStore('employees', {
  state: () => ({
    employees: [],
    totalEmployees: 0,
    loading: false,
    error: null,
    selectedEmployee: null,
    currentPage: 1,
    itemsPerPage: 10
  }),

  getters: {
    activeEmployees: (state) => state.employees.filter(emp => emp.is_active),
    inactiveEmployees: (state) => state.employees.filter(emp => !emp.is_active),
    getEmployeeById: (state) => (id) => state.employees.find(emp => emp.id === id)
  },

  actions: {
    async fetchEmployees() {
      this.loading = true
      this.error = null
      try {
        const response = await employeesService.getEmployees(this.currentPage, this.itemsPerPage)
        this.employees = response.results
        this.totalEmployees = response.total
      } catch (error) {
        this.error = error.message || 'Erreur lors de la récupération des employés'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchEmployee(id) {
      this.loading = true
      this.error = null
      try {
        const employee = await employeesService.getEmployee(id)
        this.selectedEmployee = employee
        // Mettre à jour l'employé dans la liste si présent
        const index = this.employees.findIndex(emp => emp.id === id)
        if (index !== -1) {
          this.employees[index] = employee
        }
      } catch (error) {
        this.error = error.message || 'Erreur lors de la récupération de l\'employé'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createEmployee(employeeData) {
      this.loading = true
      this.error = null
      try {
        const newEmployee = await employeesService.createEmployee(employeeData)
        this.employees.push(newEmployee)
        return newEmployee
      } catch (error) {
        this.error = error.message || 'Erreur lors de la création de l\'employé'
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateEmployee(id, employeeData) {
      this.loading = true
      this.error = null
      try {
        const updatedEmployee = await employeesService.updateEmployee(id, employeeData)
        const index = this.employees.findIndex(emp => emp.id === id)
        if (index !== -1) {
          this.employees[index] = updatedEmployee
        }
        if (this.selectedEmployee?.id === id) {
          this.selectedEmployee = updatedEmployee
        }
        return updatedEmployee
      } catch (error) {
        this.error = error.message || 'Erreur lors de la mise à jour de l\'employé'
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteEmployee(id) {
      this.loading = true
      this.error = null
      try {
        await employeesService.deleteEmployee(id)
        this.employees = this.employees.filter(emp => emp.id !== id)
        if (this.selectedEmployee?.id === id) {
          this.selectedEmployee = null
        }
      } catch (error) {
        this.error = error.message || 'Erreur lors de la suppression de l\'employé'
        throw error
      } finally {
        this.loading = false
      }
    },

    async toggleEmployeeStatus(id, isActive) {
      this.loading = true
      this.error = null
      try {
        const updatedEmployee = await employeesService.toggleEmployeeStatus(id, isActive)
        const index = this.employees.findIndex(emp => emp.id === id)
        if (index !== -1) {
          this.employees[index] = updatedEmployee
        }
        if (this.selectedEmployee?.id === id) {
          this.selectedEmployee = updatedEmployee
        }
        return updatedEmployee
      } catch (error) {
        this.error = error.message || 'Erreur lors du changement de statut de l\'employé'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 