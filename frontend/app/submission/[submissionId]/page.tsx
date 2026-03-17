"use client";

import { useRouter } from "next/navigation";
import { SubmissionStatus } from "@/components/SubmissionStatus";

interface PageProps {
  params: { submissionId: string };
}

export default function SubmissionStatusPage({ params }: PageProps) {
  const router = useRouter();
  const { submissionId } = params;

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-4 py-10">
      <SubmissionStatus
        submissionId={submissionId}
        onDone={(reportId) =>
          router.push(`/report/${encodeURIComponent(reportId)}`)
        }
      />
    </main>
  );
}

