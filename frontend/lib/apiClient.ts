import axios from "axios";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});

export interface SubmitQuestionnaireResponse {
  submissionId: string;
}

export interface SubmissionStatusResponse {
  status: "pending" | "processing" | "done" | "failed";
  reportId?: string;
  error_message?: string;
}

