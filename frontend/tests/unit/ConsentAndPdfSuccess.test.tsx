import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QuestionnaireForm } from "@/components/QuestionnaireForm";
import { PdfDownloadButton } from "@/components/PdfDownloadButton";
import * as fetchPdfModule from "@/lib/fetchPdf";

describe("QuestionnaireForm consent", () => {
  it("requires consent_self_reported before completing", async () => {
    const onComplete = jest.fn();
    render(<QuestionnaireForm onComplete={onComplete} />);

    // Try to advance without ticking consent: trigger validation on first step
    const nextButton = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextButton);

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
    const spy = jest
      .spyOn(fetchPdfModule, "fetchPdf")
      .mockResolvedValueOnce(undefined);

    render(<PdfDownloadButton reportId="success-report" />);

    const button = screen.getByRole("button", { name: /download.*pdf/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith("success-report");
    });
    expect(
      screen.queryByText(/unable to download pdf/i),
    ).not.toBeInTheDocument();
  });
});
