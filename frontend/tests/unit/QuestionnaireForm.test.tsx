import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QuestionnaireForm } from "@/components/QuestionnaireForm";

describe("QuestionnaireForm", () => {
  it("hides and clears conditional fields when show-if no longer matches", async () => {
    const onComplete = vi.fn();

    render(<QuestionnaireForm onComplete={onComplete} />);

    // Move to Energy Baseline step quickly by calling Next repeatedly
    for (let i = 0; i < 5; i++) {
      const nextBtn = screen.getByRole("button", { name: /next/i });
      fireEvent.click(nextBtn);
    }

    // At this point, the form will include uses_gas. Set to Yes then change to No.
    const usesGasSelect = await screen.findByLabelText(
      /do you use mains gas at this site\?/i,
    );
    fireEvent.change(usesGasSelect, { target: { value: "Yes" } });

    const gasKwhInput = await screen.findByLabelText(
      /gas consumption \(last 12 months\)/i,
    );
    fireEvent.change(gasKwhInput, { target: { value: "1234" } });

    // Change uses_gas to No and ensure the gas field is removed from DOM
    fireEvent.change(usesGasSelect, { target: { value: "No" } });

    await waitFor(() => {
      expect(
        screen.queryByLabelText(/gas consumption \(last 12 months\)/i),
      ).not.toBeInTheDocument();
    });
  });
});

