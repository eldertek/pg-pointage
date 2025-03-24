export interface Organization {
  id: number;
  name: string;
  address: string;
  phone: string;
  email: string;
  contact_email: string;
  logo?: string | null;
  siret: string;
  postal_code: string;
  city: string;
  country: string;
  notes?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface OrganizationFormData {
  name: string;
  address: string;
  phone: string;
  email: string;
  contact_email: string;
  logo?: File | null;
  siret: string;
  postal_code: string;
  city: string;
  country: string;
  notes?: string;
  is_active: boolean;
}

export interface SnackbarState {
  show: boolean;
  text: string;
  color: string;
}

export interface TableHeaders {
  title: string;
  align?: 'start' | 'center' | 'end';
  key: string;
  sortable?: boolean;
} 