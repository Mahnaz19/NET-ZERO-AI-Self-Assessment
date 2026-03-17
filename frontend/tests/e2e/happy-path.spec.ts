import { test, expect } from "@playwright/test";

test("happy path: fill questionnaire, submit, view report, download PDF (mock backend)", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByRole("link", { name: /start questionnaire/i }).click();

  // In mock mode we don't require all fields; this is a smoke-flow skeleton.
  await page.getByLabel(/primary contact full name/i).fill("Test User");
  await page.getByLabel(/primary contact email/i).fill("test@example.com");
  await page.getByLabel(/primary contact phone number/i).fill("01234567890");
  await page.getByLabel(/business name/i).fill("Example Business");

  await page
    .getByRole("checkbox", {
      name: /i agree to the statement above/i,
    })
    .check();

  await page.getByRole("button", { name: /^next$/i }).click();

  // Fast-forward through remaining steps
  for (let i = 0; i < 10; i++) {
    const next = page.getByRole("button", { name: /^next$/i });
    if (await next.isVisible().catch(() => false)) {
      await next.click();
    }
  }

  // Final step: go to confirm screen
  const reviewBtn = page.getByRole("button", { name: /review & confirm/i });
  await reviewBtn.click();

  await expect(
    page.getByRole("heading", { name: /review & submit/i }),
  ).toBeVisible();

  // In mock mode, submission should redirect to mock submission id and then mock report
  const submitBtn = page.getByRole("button", {
    name: /submit questionnaire/i,
  });
  await submitBtn.click();

  await page.waitForURL(/submission\/mock-submission-id/);

  // Polling should send us to a mock report page
  await page.waitForURL(/report\/mock-report-id/);

  await expect(
    page.getByRole("heading", { name: /recommendations for/i }),
  ).toBeVisible();

  // PDF download button present (we do not assert actual file system writes)
  await expect(
    page.getByRole("button", { name: /download pdf/i }),
  ).toBeVisible();
});

