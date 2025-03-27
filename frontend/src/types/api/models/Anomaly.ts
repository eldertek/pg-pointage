/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnomalyStatusEnum } from './AnomalyStatusEnum';
import type { AnomalyTypeEnum } from './AnomalyTypeEnum';
/**
 * Serializer pour les anomalies
 */
export type Anomaly = {
    readonly id: number;
    employee: number;
    readonly employee_name: string;
    site: number;
    readonly site_name: string;
    anomaly_type: AnomalyTypeEnum;
    readonly anomaly_type_display: string;
    status?: AnomalyStatusEnum;
    readonly status_display: string;
    readonly created_at: string;
    readonly updated_at: string;
};

