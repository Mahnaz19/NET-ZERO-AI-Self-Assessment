"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const LAST_SUBMISSION_KEY = "netzero-last-submission-id";

export function LastSubmissionLink() {
  const [submissionId, setSubmissionId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const id = window.localStorage.getItem(LAST_SUBMISSION_KEY);
    if (id) setSubmissionId(id);
  }, []);

  if (!submissionId) return null;

  return (
    <p className="text-sm text-slate-600">
      <Link
        href={`/submission/${encodeURIComponent(submissionId)}`}
        className="font-medium text-emerald-600 underline hover:text-emerald-700"
      >
        View your latest submission
      </Link>{" "}
      (ID: {submissionId})
    </p>
  );
}
