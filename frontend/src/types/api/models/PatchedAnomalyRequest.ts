/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AnomalyStatusEnum } from './AnomalyStatusEnum';
import type { AnomalyTypeEnum } from './AnomalyTypeEnum';
/**
 * Serializer pour les anomalies
 */
export type PatchedAnomalyRequest = {
    employee?: number;
    site?: number;
    anomaly_type?: AnomalyTypeEnum;
    status?: AnomalyStatusEnum;
};

