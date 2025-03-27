/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ScheduleDetail } from './ScheduleDetail';
import type { ScheduleTypeEnum } from './ScheduleTypeEnum';
/**
 * Serializer pour les plannings
 */
export type Schedule = {
    readonly id: number;
    site: number;
    readonly site_name: string;
    schedule_type?: ScheduleTypeEnum;
    details?: Array<ScheduleDetail>;
    readonly created_at: string;
    readonly updated_at: string;
    is_active?: boolean;
};

