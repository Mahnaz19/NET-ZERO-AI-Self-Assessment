"use client";

import { ReportViewer } from "@/components/ReportViewer";

interface PageProps {
  params: { reportId: string };
}

export default function ReportPage({ params }: PageProps) {
  const { reportId } = params;

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-10">
      <ReportViewer reportId={reportId} />
    </main>
  );
}

