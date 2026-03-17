"use client";

import { useEffect, useState } from "react";
import type { SubmissionStatusResponse } from "@/lib/apiClient";
import { apiClient } from "@/lib/apiClient";

interface SubmissionStatusProps {
  submissionId: string;
  onDone: (reportId: string) => void;
}

export function SubmissionStatus({ submissionId, onDone }: SubmissionStatusProps) {
  const [status, setStatus] = useState<SubmissionStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const useMock =
      process.env.NEXT_PUBLIC_USE_MOCK_BACKEND === "true" ||
      (typeof window !== "undefined" &&
        window.localStorage.getItem("USE_MOCK_BACKEND") === "true");

    if (useMock) {
      const mock: SubmissionStatusResponse = { status: "done", reportId: "mock-report-id" };
      setStatus(mock);
      onDone("mock-report-id");
      return;
    }

    async function poll() {
      try {
        const res = await apiClient.get<SubmissionStatusResponse>(
          `/api/submissions/${encodeURIComponent(submissionId)}/status`,
        );
        if (cancelled) return;
        setStatus(res.data);
        if (res.data.status === "done" && res.data.reportId) {
          onDone(res.data.reportId);
          return;
        }
        if (res.data.status === "failed") {
          setError(res.data.error_message ?? "Submission failed.");
          return;
        }
        setTimeout(poll, 3000);
      } catch (err) {
        if (cancelled) return;
        setError("Unable to fetch submission status. Please refresh the page.");
      }
    }

    poll();

    return () => {
      cancelled = true;
    };
  }, [submissionId, onDone]);

  return (
    <section
      aria-live="polite"
      aria-busy={status == null || status.status === "pending" || status.status === "processing"}
      className="space-y-2 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h1 className="text-xl font-semibold text-slate-900">Submission status</h1>
      <p className="text-sm text-slate-600">
        Submission ID: <span className="font-mono text-slate-800">{submissionId}</span>
      </p>
      <p className="text-sm text-slate-700">
        Current status:{" "}
        <span className="font-medium">
          {status?.status ?? "Checking…"}
        </span>
      </p>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

