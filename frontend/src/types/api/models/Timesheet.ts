/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EntryTypeEnum } from './EntryTypeEnum';
/**
 * Serializer pour les pointages
 */
export type Timesheet = {
    readonly id: number;
    employee: number;
    readonly employee_name: string;
    site: number;
    readonly site_name: string;
    timestamp?: string;
    entry_type: EntryTypeEnum;
    readonly created_at: string;
};

