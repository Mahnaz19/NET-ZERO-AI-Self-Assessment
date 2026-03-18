import axios from "axios";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export interface SubmitQuestionnaireResponse {
  id?: number;
  submissionId?: string;
  status?: string;
}

export interface SubmissionStatusResponse {
  status: "pending" | "processing" | "done" | "failed";
  reportId?: string;
  error_message?: string;
}

