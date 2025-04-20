import api from '../api'
import type { User } from '@/types/api'
import type { UserRequest } from '@/types/api/models/UserRequest'

interface UserResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

interface UserStatistics {
  total_sites: number;
  total_schedules: number;
  total_timesheets: number;
  total_reports: number;
  total_hours: number;
  anomalies: number;
}

interface UserSite {
  id: number;
  name: string;
  address: string;
  is_active: boolean;
}

interface UserSchedule {
  id: number;
  site_name: string;
  schedule_type: string;
  is_active: boolean;
}

interface UserReport {
  id: number;
  name: string;
  created_at: string;
  report_type: string;
}

export const usersApi = {
  getAllUsers: (params?: any) => {
    return api.get<UserResponse>('/users/', { params })
  },

  getUser: (id: number) => {
    return api.get<User>(`/users/${id}/`)
  },

  createUser: (data: UserRequest) => {
    return api.post<User>('/users/', data)
  },

  updateUser: (id: number, data: UserRequest) => {
    return api.patch<User>(`/users/${id}/`, data)
  },

  deleteUser: (id: number) => {
    return api.delete(`/users/${id}/`)
  },

  toggleUserStatus: (id: number, isActive: boolean) => {
    return api.patch<User>(`/users/${id}/`, { is_active: isActive })
  },

  getUserStatistics: (id: number) => {
    return api.get<UserStatistics>(`/users/${id}/statistics/`)
  },

  getUserSites: (id: number) => {
    return api.get<UserSite[]>(`/users/${id}/sites/`)
  },

  getUserSchedules: (id: number) => {
    return api.get<UserSchedule[]>(`/users/${id}/schedules/`)
  },

  getUserReports: (id: number) => {
    return api.get<UserReport[]>(`/users/${id}/reports/`)
  }
} 