/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReportFormat } from './ReportFormat';
import type { ReportType } from './ReportType';
export type ReportGenerateRequest = {
    report_type: ReportType;
    report_format: ReportFormat;
    start_date: string;
    end_date: string;
    site?: number;
};

