import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PdfDownloadButton } from "@/components/PdfDownloadButton";
import * as fetchPdfModule from "@/lib/fetchPdf";

describe("PdfDownloadButton", () => {
  it("calls fetchPdf on click and shows error on failure", async () => {
    const spy = jest
      .spyOn(fetchPdfModule, "fetchPdf")
      .mockRejectedValueOnce(new Error("fail"));

    render(<PdfDownloadButton reportId="test-report" />);

    const button = screen.getByRole("button", { name: /download.*pdf/i });
    fireEvent.click(button);

    await waitFor(() =>
      expect(
        screen.getByText(/unable to download pdf/i),
      ).toBeInTheDocument(),
    );

    expect(spy).toHaveBeenCalledWith("test-report");
  });
});

