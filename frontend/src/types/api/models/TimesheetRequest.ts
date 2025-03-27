/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EntryTypeEnum } from './EntryTypeEnum';
/**
 * Serializer pour les pointages
 */
export type TimesheetRequest = {
    employee: number;
    site: number;
    timestamp?: string;
    entry_type: EntryTypeEnum;
};

