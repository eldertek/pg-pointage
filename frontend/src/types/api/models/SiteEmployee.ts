/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Serializer pour les employés du site
 */
export type SiteEmployee = {
    readonly id: number;
    site: number;
    employee: number;
    readonly employee_name: string;
    readonly employee_organization: number;
    schedule?: number | null;
    readonly created_at: string;
    is_active?: boolean;
};

