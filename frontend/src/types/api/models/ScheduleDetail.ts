/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DayOfWeekEnum } from './DayOfWeekEnum';
import type { DayTypeEnum } from './DayTypeEnum';
/**
 * Serializer pour les détails de planning
 */
export type ScheduleDetail = {
    readonly id: number;
    day_of_week: DayOfWeekEnum;
    day_type?: DayTypeEnum;
    start_time_1?: string | null;
    end_time_1?: string | null;
    start_time_2?: string | null;
    end_time_2?: string | null;
    /**
     * Pour les plannings de type fréquence uniquement
     */
    frequency_duration?: number | null;
    readonly day_name: string;
};

