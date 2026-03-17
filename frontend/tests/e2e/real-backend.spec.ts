import { test, expect } from "@playwright/test";
import { makeSampleQuestionnaire } from "@/lib/testPayload";

test("real backend submission and status polling (optional)", async ({
  request,
}) => {
  if (process.env.REAL_BACKEND_E2E !== "true") {
    test.skip();
  }

  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const payload = makeSampleQuestionnaire();

  const submitRes = await request.post(
    `${base}/api/questionnaire/submit`,
    {
      data: payload,
    },
  );

  expect(submitRes.ok()).toBeTruthy();

  const body = (await submitRes.json()) as any;

  const submissionId: string | undefined =
    body.submissionId ?? body.submission_id;
  let statusUrl: string | undefined = body.status_url;

  if (!statusUrl && submissionId) {
    statusUrl = `${base}/api/submissions/${encodeURIComponent(
      submissionId,
    )}/status`;
  }

  expect(statusUrl).toBeTruthy();

  // Poll submission status until done/failed or timeout
  let finalStatus: any = null;
  for (let i = 0; i < 15; i += 1) {
    const statusRes = await request.get(statusUrl!);
    expect(statusRes.ok()).toBeTruthy();
    const statusBody = (await statusRes.json()) as any;
    finalStatus = statusBody;
    if (statusBody.status === "done" || statusBody.status === "failed") {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  expect(finalStatus).toBeTruthy();
  expect(["done", "failed"]).toContain(finalStatus.status);
});

