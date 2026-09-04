export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ClassProbability {
  class_id: number;
  label: string;
  probability: number;
}

export interface DicomMetadata {
  is_dicom: boolean;
  modality: string;
  body_part: string;
  patient_position: string;
  photometric_interpretation: string;
  kvp: string;
  exposure_time: string;
  xray_tube_current: string;
  study_description: string;
  rows: number;
  columns: number;
}

export interface PredictionResult {
  id: number;
  predicted_class: number;
  label: string;
  confidence: number;
  probs: ClassProbability[];
  inference_ms: number;
  image_url: string | null;
  gradcam_image: string | null;
  raw_image_data?: string | null;
  pure_heatmap?: string | null;
  dicom_metadata?: DicomMetadata | null;
  is_ood: boolean;
  ood_similarity: number | null;
  created_at: string;
}

export interface ReportRequest {
  predicted_class: number;
  label: string;
  confidence: number;
  probs?: ClassProbability[];
  model: string;
  dicom_metadata?: DicomMetadata | null;
  override_label?: string | null;
  override_notes?: string | null;
  is_ambiguous?: boolean | null;
}

export interface ReportResponse {
  model_used: string;
  provider: string;
  technique: string;
  findings: string;
  impression: string;
  icd_10: string;
  recommendations: string;
  disclaimer: string;
  generated_at: string;
}

export interface PredictionOut {
  id: number;
  original_filename: string;
  predicted_class: number;
  label: string;
  confidence: number;
  probs: Record<string, number>;
  inference_ms: number;
  created_at: string;
  image_url: string | null;
}

export interface PredictionListOut {
  items: PredictionOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface ClassCount {
  class_id: number;
  label: string;
  count: number;
}

export interface TimePoint {
  date: string;
  count: number;
}

export interface StatsOut {
  total_predictions: number;
  average_confidence: number;
  by_class: ClassCount[];
  over_time: TimePoint[];
}

export const CLASS_LABELS: Record<number, string> = {
  0: "Covid-19",
  1: "Normal",
  2: "Viral pneumonia",
  3: "Bacterial pneumonia",
};

export const CLASS_COLORS: Record<number, string> = {
  0: "#ef4444",
  1: "#22c55e",
  2: "#f59e0b",
  3: "#8b5cf6",
};
