interface SubmitButtonProps {
  label: string;
  disabled?: boolean;
  isSubmitting?: boolean;
}

export function SubmitButton({
  label,
  disabled,
  isSubmitting,
}: SubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={disabled || isSubmitting}
      className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
      aria-busy={isSubmitting || undefined}
    >
      {isSubmitting ? "Submitting…" : label}
    </button>
  );
}

