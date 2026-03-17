export async function fetchPdf(reportId: string): Promise<void> {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const submissionId = Number(reportId);
  if (Number.isNaN(submissionId)) {
    throw new Error("Invalid report ID");
  }

  const res = await fetch(`${baseUrl}/api/reports/generate_pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ submission_id: submissionId }),
  });
  if (!res.ok) {
    throw new Error("Failed to generate PDF");
  }

  let blob: Blob;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const data = (await res.json()) as { pdf_url?: string };
    if (!data.pdf_url) {
      throw new Error("PDF URL not provided by server");
    }
    const pdfRes = await fetch(data.pdf_url);
    if (!pdfRes.ok) {
      throw new Error("Failed to download PDF from provided URL");
    }
    blob = await pdfRes.blob();
  } else {
    blob = await res.blob();
  }
  const blobUrl = window.URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = `report_${reportId}.pdf`;
  link.setAttribute("aria-label", `Download report ${reportId} as PDF`);
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(blobUrl);
}

