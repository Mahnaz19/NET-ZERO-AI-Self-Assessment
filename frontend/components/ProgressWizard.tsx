interface ProgressWizardProps {
  steps: string[];
  currentStepIndex: number;
}

export function ProgressWizard({ steps, currentStepIndex }: ProgressWizardProps) {
  return (
    <nav
      className="mb-6 flex items-center justify-between gap-2 text-sm"
      aria-label="Questionnaire progress"
    >
      {steps.map((label, index) => {
        const isCurrent = index === currentStepIndex;
        const isCompleted = index < currentStepIndex;
        return (
          <div
            key={label}
            className="flex flex-1 flex-col items-start gap-1"
            aria-current={isCurrent ? "step" : undefined}
          >
            <div className="flex items-center gap-2">
              <span
                className={[
                  "flex h-6 w-6 items-center justify-center rounded-full border text-xs font-medium",
                  isCompleted
                    ? "border-emerald-600 bg-emerald-600 text-white"
                    : isCurrent
                    ? "border-emerald-600 text-emerald-700"
                    : "border-slate-300 text-slate-500",
                ].join(" ")}
              >
                {index + 1}
              </span>
              <span
                className={
                  isCurrent
                    ? "font-semibold text-slate-900"
                    : "text-slate-600"
                }
              >
                {label}
              </span>
            </div>
          </div>
        );
      })}
    </nav>
  );
}

