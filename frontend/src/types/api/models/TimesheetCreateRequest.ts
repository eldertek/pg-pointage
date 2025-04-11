/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EntryTypeEnum } from './EntryTypeEnum';
/**
 * Serializer pour la création de pointages
 */
export type TimesheetCreateRequest = {
    site_id?: string;
    entry_type?: EntryTypeEnum;
    timestamp?: string;
    scan_type?: string;
    employee?: number;
};

