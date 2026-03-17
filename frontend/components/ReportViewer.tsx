"use client";

import { useEffect, useState } from "react";
import { PdfDownloadButton } from "@/components/PdfDownloadButton";

interface Recommendation {
  id: string;
  title: string;
  description: string;
  category?: string;
  estimated_annual_kwh_saved?: number;
  estimated_annual_saving_gbp?: number;
  estimated_implementation_cost_gbp?: number;
  payback_years?: number;
  estimated_annual_co2_saved_tonnes?: number;
}

interface ReportData {
  report_id: string;
  business_name: string;
  site_postcode?: string;
  baseline?: {
    electricity_kwh_annual?: number;
    electricity_cost_annual_ex_vat?: number;
    gas_kwh_annual?: number;
    gas_cost_annual_ex_vat?: number;
    total_co2_tonnes?: number;
  };
  recommendations: Recommendation[];
}

interface ReportViewerProps {
  reportId: string;
}

export function ReportViewer({ reportId }: ReportViewerProps) {
  const [report, setReport] = useState<ReportData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const useMock =
      process.env.NEXT_PUBLIC_USE_MOCK_BACKEND === "true" ||
      (typeof window !== "undefined" &&
        window.localStorage.getItem("USE_MOCK_BACKEND") === "true");

    async function load() {
      try {
        if (useMock) {
          const res = await fetch("/data/mock/report_sample.json");
          if (!res.ok) throw new Error("Failed to load mock report.");
          const json = (await res.json()) as ReportData;
          setReport(json);
          return;
        }
        const baseUrl =
          process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
        const res = await fetch(
          `${baseUrl}/api/reports/${encodeURIComponent(reportId)}`,
        );
        if (!res.ok) {
          throw new Error("Failed to fetch report.");
        }
        const json = (await res.json()) as ReportData;
        setReport(json);
      } catch (err) {
        setError("Unable to load report. Please try again later.");
      }
    }

    load();
  }, [reportId]);

  if (error) {
    return (
      <section className="space-y-2 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Report</h1>
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      </section>
    );
  }

  if (!report) {
    return (
      <section className="space-y-2 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-900">Report</h1>
        <p className="text-sm text-slate-700">Loading report…</p>
      </section>
    );
  }

  return (
    <section className="space-y-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Net Zero AI Self-Assessment
          </p>
          <h1 className="text-2xl font-semibold text-slate-900">
            Recommendations for {report.business_name}
          </h1>
          {report.site_postcode && (
            <p className="text-sm text-slate-600">
              Site postcode: {report.site_postcode}
            </p>
          )}
        </div>
        <PdfDownloadButton reportId={report.report_id ?? reportId} />
      </header>

      {report.baseline && (
        <section aria-label="Energy baseline" className="space-y-2">
          <h2 className="text-lg font-semibold text-slate-900">
            Energy baseline
          </h2>
          <dl className="grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
            {report.baseline.electricity_kwh_annual != null && (
              <div>
                <dt className="font-medium">Electricity use (kWh/year)</dt>
                <dd>{report.baseline.electricity_kwh_annual.toLocaleString()}</dd>
              </div>
            )}
            {report.baseline.electricity_cost_annual_ex_vat != null && (
              <div>
                <dt className="font-medium">
                  Electricity cost (ex VAT, £/year)
                </dt>
                <dd>
                  £
                  {report.baseline.electricity_cost_annual_ex_vat.toLocaleString()}
                </dd>
              </div>
            )}
            {report.baseline.gas_kwh_annual != null && (
              <div>
                <dt className="font-medium">Gas use (kWh/year)</dt>
                <dd>{report.baseline.gas_kwh_annual.toLocaleString()}</dd>
              </div>
            )}
            {report.baseline.gas_cost_annual_ex_vat != null && (
              <div>
                <dt className="font-medium">Gas cost (ex VAT, £/year)</dt>
                <dd>
                  £{report.baseline.gas_cost_annual_ex_vat.toLocaleString()}
                </dd>
              </div>
            )}
            {report.baseline.total_co2_tonnes != null && (
              <div>
                <dt className="font-medium">Total annual CO₂ (tonnes)</dt>
                <dd>{report.baseline.total_co2_tonnes.toLocaleString()}</dd>
              </div>
            )}
          </dl>
        </section>
      )}

      <section aria-label="Recommendations" className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">
          Recommended actions
        </h2>
        {report.recommendations.length === 0 ? (
          <p className="text-sm text-slate-700">
            No recommendations were generated for this report.
          </p>
        ) : (
          <ul className="space-y-3">
            {report.recommendations.map((rec) => (
              <li
                key={rec.id}
                className="rounded-md border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      {rec.title}
                    </h3>
                    {rec.category && (
                      <p className="text-xs text-slate-600">{rec.category}</p>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-sm text-slate-700">
                  {rec.description}
                </p>
                <dl className="mt-3 grid gap-2 text-xs text-slate-700 sm:grid-cols-3">
                  {rec.estimated_annual_kwh_saved != null && (
                    <div>
                      <dt className="font-medium">kWh saved/year</dt>
                      <dd>{rec.estimated_annual_kwh_saved.toLocaleString()}</dd>
                    </div>
                  )}
                  {rec.estimated_annual_saving_gbp != null && (
                    <div>
                      <dt className="font-medium">£ saving/year</dt>
                      <dd>
                        £{rec.estimated_annual_saving_gbp.toLocaleString()}
                      </dd>
                    </div>
                  )}
                  {rec.estimated_implementation_cost_gbp != null && (
                    <div>
                      <dt className="font-medium">Implementation cost</dt>
                      <dd>
                        £
                        {rec.estimated_implementation_cost_gbp.toLocaleString()}
                      </dd>
                    </div>
                  )}
                  {rec.payback_years != null && (
                    <div>
                      <dt className="font-medium">Simple payback</dt>
                      <dd>{rec.payback_years.toFixed(1)} years</dd>
                    </div>
                  )}
                  {rec.estimated_annual_co2_saved_tonnes != null && (
                    <div>
                      <dt className="font-medium">CO₂ saved/year</dt>
                      <dd>
                        {rec.estimated_annual_co2_saved_tonnes.toLocaleString()}{" "}
                        tonnes
                      </dd>
                    </div>
                  )}
                </dl>
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}

