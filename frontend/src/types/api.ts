export type InvoiceSource = 'synthetic' | 'local_upload';

export interface LineItem {
  label: string;
  amount_cop: number;
}

export interface InvoiceOut {
  id: string;
  collection_id: string;
  billing_period: string | null;
  issued_on: string | null;
  due_on: string | null;
  consumption_m3: number | null;
  total_cop: number | null;
  fixed_charge_cop: number | null;
  variable_charge_cop: number | null;
  line_items: LineItem[];
  warnings: string[];
  source: InvoiceSource;
}

export type AnalysisStatus = 'high_variation' | 'significant_decrease' | 'within_threshold' | 'insufficient_data';

export interface AnalysisOut {
  current_consumption_m3: number | null;
  previous_consumption_m3: number | null;
  variation_percentage: number | null;
  historical_average_m3: number | null;
  historical_median_m3?: number | null;
  historical_mad_m3?: number | null;
  status: AnalysisStatus;
  message: string;
}

export interface ChatRequest {
  invoice_id: string;
  question: string;
}

export interface ChatResponse {
  answer: string;
  mode: 'digitalocean' | 'demo';
  evidence: string[];
}

export interface ApiError {
  error: { code: string; message: string };
}
