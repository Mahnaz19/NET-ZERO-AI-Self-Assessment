"use client";

import { useRouter } from "next/navigation";
import { QuestionnaireForm } from "@/components/QuestionnaireForm";
import { LastSubmissionLink } from "@/components/LastSubmissionLink";

export default function QuestionnairePage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          Net Zero AI Self-Assessment
        </p>
        <h1 className="text-2xl font-semibold text-slate-900">
          Site questionnaire
        </h1>
        <p className="text-sm text-slate-600">
          Provide details about your business, building, and energy use so we
          can estimate your baseline and identify suitable measures.
        </p>
        <LastSubmissionLink />
      </header>

      <QuestionnaireForm
        onComplete={() => {
          router.push("/questionnaire/confirm");
        }}
      />
    </main>
  );
}

