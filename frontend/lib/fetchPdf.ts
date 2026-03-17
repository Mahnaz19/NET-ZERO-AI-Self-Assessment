export async function fetchPdf(reportId: string): Promise<void> {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const url = `${baseUrl}/api/reports/generate_pdf?report_id=${encodeURIComponent(
    reportId,
  )}`;

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to generate PDF");
  }

  const blob = await res.blob();
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

