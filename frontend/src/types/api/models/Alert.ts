/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AlertStatusEnum } from './AlertStatusEnum';
import type { AlertTypeEnum } from './AlertTypeEnum';
/**
 * Serializer pour les alertes
 */
export type Alert = {
    readonly id: number;
    employee: number;
    readonly employee_name: string;
    site: number;
    readonly site_name: string;
    alert_type: AlertTypeEnum;
    readonly alert_type_display: string;
    status?: AlertStatusEnum;
    readonly status_display: string;
    readonly created_at: string;
    readonly updated_at: string;
};

