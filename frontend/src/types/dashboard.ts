import type { AnalysisOut, InvoiceOut } from './api';

export interface DashboardSeriesPoint {
  period: string;
  consumption_m3: number | null;
  total_cop: number | null;
}

export interface DashboardOut {
  collection_id: string;
  invoices: InvoiceOut[];
  latest_analysis: AnalysisOut | null;
  series: DashboardSeriesPoint[];
}
