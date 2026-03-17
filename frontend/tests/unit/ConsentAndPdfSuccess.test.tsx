import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QuestionnaireForm } from "@/components/QuestionnaireForm";
import { PdfDownloadButton } from "@/components/PdfDownloadButton";
import * as fetchPdfModule from "@/lib/fetchPdf";

describe("QuestionnaireForm consent", () => {
  it("requires consent_self_reported before completing", async () => {
    const onComplete = vi.fn();
    render(<QuestionnaireForm onComplete={onComplete} />);

    // Try to go to confirm without ticking consent: trigger validation on first step
    const reviewButton = screen.getByRole("button", { name: /review & confirm/i });
    fireEvent.click(reviewButton);

    await waitFor(() => {
      expect(
        screen.getByText(/you must provide consent to continue/i),
      ).toBeInTheDocument();
    });
    expect(onComplete).not.toHaveBeenCalled();
  });
});

describe("PdfDownloadButton success", () => {
  it("invokes fetchPdf and does not show error on success", async () => {
    const spy = vi
      .spyOn(fetchPdfModule, "fetchPdf")
      .mockResolvedValueOnce();

    render(<PdfDownloadButton reportId="success-report" />);

    const button = screen.getByRole("button", { name: /download pdf/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith("success-report");
    });
    expect(
      screen.queryByText(/unable to download pdf/i),
    ).not.toBeInTheDocument();
  });
}

