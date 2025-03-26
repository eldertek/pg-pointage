export interface EditingTimesheet {
  id: number;
  timestamp: string;
  entry_type: 'ARRIVAL' | 'DEPARTURE';
  correction_note: string;
}

export interface Filters {
  employee: string;
  site: number | null;
  entryType: string;
  status: string;
  startDate: string;
  endDate: string;
}

export interface SiteOption {
  title: string;
  value: number;
}

export interface TableOptions {
  page: number;
  itemsPerPage: number;
}

export interface Timesheet {
  id: number;
  employee: number;
  employee_name: string;
  site: number;
  site_name: string;
  timestamp: string;
  entry_type: 'ARRIVAL' | 'DEPARTURE';
  is_late: boolean;
  is_early_departure: boolean;
  late_minutes?: number;
  early_departure_minutes?: number;
  correction_note?: string;
  latitude?: number | null;
  longitude?: number | null;
  date?: string;
  time?: string;
  raw?: any;
  check_in?: string;
  check_out?: string;
} 