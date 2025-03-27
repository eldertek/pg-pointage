/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour les rapports d'employés
 */
export type EmployeeReport = {
    readonly id: number;
    readonly employee_name: string;
    readonly site_name: string;
    start_date: string;
    end_date: string;
    total_hours?: string;
    late_count?: number;
    total_late_minutes?: number;
    early_departure_count?: number;
    total_early_departure_minutes?: number;
    anomaly_count?: number;
    readonly created_at: string;
    employee: number;
    site: number;
};

