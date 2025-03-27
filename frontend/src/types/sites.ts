import type { Schedule as BaseSchedule, ScheduleDetail, Timesheet as BaseTimesheet } from '@/types/api'
import { EntryTypeEnum } from '@/types/api'

export interface EditingTimesheet {
  id: number;
  timestamp: string;
  entry_type: EntryTypeEnum;
  correction_note: string;
}

export interface Filters {
  employee: string;
  site: number | null;
  entryType: EntryTypeEnum | '';
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

export interface ExtendedTimesheet extends BaseTimesheet {
  date?: string;
  time?: string;
  latitude?: number | null;
  longitude?: number | null;
  is_late?: boolean;
  is_early_departure?: boolean;
  late_minutes?: number;
  early_departure_minutes?: number;
  correction_note?: string;
}

export interface ExtendedSchedule extends BaseSchedule {
  name: string;
  min_daily_hours: number;
  min_weekly_hours: number;
  allow_early_arrival: boolean;
  allow_late_departure: boolean;
  early_arrival_limit: number;
  late_departure_limit: number;
  break_duration: number;
  min_break_start: string;
  max_break_end: string;
  frequency_hours: number;
  frequency_type: 'DAILY' | 'WEEKLY' | 'MONTHLY';
  frequency_count: number;
  time_window: number;
  assigned_employees_count?: number | Array<{ id: number; employee_name: string }>;
} 