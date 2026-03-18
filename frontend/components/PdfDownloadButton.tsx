"use client";

import { useState } from "react";
import { fetchPdf } from "@/lib/fetchPdf";

interface PdfDownloadButtonProps {
  reportId: string;
}

export function PdfDownloadButton({ reportId }: PdfDownloadButtonProps) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setError(null);
    setDownloading(true);
    try {
      await fetchPdf(reportId);
    } catch (err) {
      setError("Unable to download PDF. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={handleClick}
        disabled={downloading}
        className="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-wait disabled:bg-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900 focus-visible:ring-offset-2"
        aria-label="Download report as PDF"
        aria-busy={downloading || undefined}
      >
        {downloading ? "Downloading…" : "Download PDF"}
      </button>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

