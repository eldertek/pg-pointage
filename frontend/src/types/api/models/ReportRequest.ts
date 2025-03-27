/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReportFormatEnum } from './ReportFormatEnum';
import type { ReportTypeEnum } from './ReportTypeEnum';
/**
 * Serializer pour les rapports
 */
export type ReportRequest = {
    organization: number;
    site?: number | null;
    report_type: ReportTypeEnum;
    report_format?: ReportFormatEnum;
    start_date: string;
    end_date: string;
};

