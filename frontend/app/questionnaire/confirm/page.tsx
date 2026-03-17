"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { questionnaireSchema, type QuestionnaireFormValues } from "@/lib/schema";
import { apiClient, type SubmitQuestionnaireResponse } from "@/lib/apiClient";
import { SubmitButton } from "@/components/SubmitButton";

const STORAGE_KEY = "netzero-questionnaire-draft";

export default function QuestionnaireConfirmPage() {
  const router = useRouter();
  const [values, setValues] = useState<QuestionnaireFormValues | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      setError("No questionnaire draft found. Please complete the form first.");
      return;
    }
    try {
      const parsed = JSON.parse(stored) as QuestionnaireFormValues;
      const validated = questionnaireSchema.parse(parsed);
      setValues(validated);
    } catch (err) {
      setError(
        "Your draft is incomplete or invalid. Please go back and review your answers.",
      );
    }
  }, []);

  const handleSubmit = async () => {
    if (!values) return;
    setSubmitting(true);
    setError(null);
    try {
      const useMock =
        process.env.NEXT_PUBLIC_USE_MOCK_BACKEND === "true" ||
        (typeof window !== "undefined" &&
          window.localStorage.getItem("USE_MOCK_BACKEND") === "true");
      if (useMock) {
        router.push("/submission/mock-submission-id");
        return;
      }
      const res = await apiClient.post<SubmitQuestionnaireResponse>(
        "/api/questionnaire/submit",
        values,
      );
      window.localStorage.removeItem(STORAGE_KEY);
      router.push(`/submission/${encodeURIComponent(res.data.submissionId)}`);
    } catch {
      setError(
        "There was a problem submitting your questionnaire. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !values) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 px-4 py-10">
        <h1 className="text-2xl font-semibold text-slate-900">
          Review &amp; submit
        </h1>
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
        <button
          type="button"
          onClick={() => router.push("/questionnaire")}
          className="inline-flex w-fit items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Back to questionnaire
        </button>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          Net Zero AI Self-Assessment
        </p>
        <h1 className="text-2xl font-semibold text-slate-900">
          Review &amp; submit
        </h1>
        <p className="text-sm text-slate-600">
          Please review your answers. When you&apos;re ready, submit to
          generate your report.
        </p>
      </header>

      {!values ? (
        <p className="text-sm text-slate-700">Loading your answers…</p>
      ) : (
        <>
          <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-6 text-sm shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">
              Key details
            </h2>
            <dl className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="font-medium text-slate-800">
                  Business name
                </dt>
                <dd className="text-slate-700">{values.business_name}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-800">
                  Site postcode
                </dt>
                <dd className="text-slate-700">{values.site_postcode}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-800">
                  Primary contact
                </dt>
                <dd className="text-slate-700">
                  {values.primary_contact_name} ({values.primary_contact_email})
                </dd>
              </div>
            </dl>
          </section>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void handleSubmit();
            }}
            className="space-y-3"
            aria-label="Confirm questionnaire submission"
          >
            {error && (
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            )}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => router.push("/questionnaire")}
                className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
              >
                Back to questionnaire
              </button>
              <SubmitButton
                label="Submit questionnaire"
                disabled={!values}
                isSubmitting={submitting}
              />
            </div>
          </form>
        </>
      )}
    </main>
  );
}

