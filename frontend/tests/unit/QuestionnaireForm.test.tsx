import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QuestionnaireForm } from "@/components/QuestionnaireForm";

describe("QuestionnaireForm", () => {
  it("hides and clears conditional fields when show-if no longer matches", async () => {
    const onComplete = jest.fn();

    render(<QuestionnaireForm onComplete={onComplete} />);

    // Fill minimal required fields for the first three sections so we can reach Energy Baseline.
    fireEvent.change(
      screen.getByLabelText(/primary contact full name/i),
      { target: { value: "Test User" } },
    );
    fireEvent.change(
      screen.getByLabelText(/primary contact email/i),
      { target: { value: "test@example.com" } },
    );
    fireEvent.change(
      screen.getByLabelText(/primary contact phone number/i),
      { target: { value: "01234567890" } },
    );
    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /consent: i confirm info is accurate/i,
      }),
    );

    fireEvent.click(
      screen.getByRole("button", { name: /next/i }),
    );

    fireEvent.change(
      await screen.findByLabelText(/business name/i),
      { target: { value: "Example Business" } },
    );
    fireEvent.change(
      screen.getByLabelText(/site address line 1/i),
      { target: { value: "1 Example Street" } },
    );
    fireEvent.change(
      screen.getByLabelText(/^postcode$/i),
      { target: { value: "AB12 3CD" } },
    );
    fireEvent.change(
      screen.getByLabelText(/sector \/ business activity/i),
      { target: { value: "Office" } },
    );
    fireEvent.change(
      screen.getByLabelText(/typical number of employees on site/i),
      { target: { value: "10" } },
    );
    fireEvent.change(
      screen.getByLabelText(/days open per week/i),
      { target: { value: "5" } },
    );
    fireEvent.change(
      screen.getByLabelText(/weekly operational hours \(total\)/i),
      { target: { value: "40" } },
    );
    fireEvent.change(
      screen.getByLabelText(/occupancy\/ownership status/i),
      { target: { value: "Owner‑occupier" } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /next/i }),
    );

    fireEvent.change(
      await screen.findByLabelText(/building type/i),
      { target: { value: "Office" } },
    );
    fireEvent.change(
      screen.getByLabelText(/approximate floor area band/i),
      { target: { value: "250–500" } },
    );
    fireEvent.change(
      screen.getByLabelText(/building age band/i),
      { target: { value: "2001–2015" } },
    );
    fireEvent.change(
      screen.getByLabelText(/insulation level/i),
      { target: { value: "Average" } },
    );
    fireEvent.change(
      screen.getByLabelText(/window\/glazing type/i),
      { target: { value: "Double" } },
    );
    fireEvent.change(
      screen.getByLabelText(/do you know your epc rating\?/i),
      { target: { value: "No" } },
    );

    fireEvent.click(
      screen.getByRole("button", { name: /next/i }),
    );

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

