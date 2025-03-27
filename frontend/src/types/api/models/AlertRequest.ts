/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AlertStatusEnum } from './AlertStatusEnum';
import type { AlertTypeEnum } from './AlertTypeEnum';
/**
 * Serializer pour les alertes
 */
export type AlertRequest = {
    employee: number;
    site: number;
    alert_type: AlertTypeEnum;
    status?: AlertStatusEnum;
};

