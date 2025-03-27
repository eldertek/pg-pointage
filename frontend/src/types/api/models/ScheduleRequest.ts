/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ScheduleDetailRequest } from './ScheduleDetailRequest';
import type { ScheduleTypeEnum } from './ScheduleTypeEnum';
/**
 * Serializer pour les plannings
 */
export type ScheduleRequest = {
    site: number;
    schedule_type?: ScheduleTypeEnum;
    details?: Array<ScheduleDetailRequest>;
    employee?: number;
    is_active?: boolean;
};

