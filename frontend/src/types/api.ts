export enum RoleEnum {
  SUPER_ADMIN = 'SUPER_ADMIN',
  ADMIN = 'ADMIN',
  MANAGER = 'MANAGER',
  EMPLOYEE = 'EMPLOYEE'
}

export enum ScanPreferenceEnum {
  BOTH = 'BOTH',
  NFC_ONLY = 'NFC_ONLY',
  QR_ONLY = 'QR_ONLY'
}

export interface Organization {
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

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: RoleEnum;
  is_active: boolean;
  activation_start_date?: string;
  activation_end_date?: string;
  organizations: number[];
  organizations_names?: string[];
  phone_number: string;
  scan_preference: ScanPreferenceEnum;
  simplified_mobile_view: boolean;
  date_joined?: string;
  employee_id?: string;
  sites?: { id: number; name: string }[];
}

export interface UserCreate extends User {
  password: string;
}

export interface UserUpdate extends Partial<User> {
  password?: string;
} 