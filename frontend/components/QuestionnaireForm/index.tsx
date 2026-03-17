"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm, FormProvider, useFormContext } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { questionnaireFields, QuestionnaireField } from "@/lib/questionnaire";
import {
  questionnaireSchema,
  type QuestionnaireFormValues,
} from "@/lib/schema";
import { ProgressWizard } from "@/components/ProgressWizard";

const STORAGE_KEY = "netzero-questionnaire-draft";

const stepsOrder = [
  "0. Consent & Contact",
  "1. Business Profile",
  "2. Building Basics",
  "3. Energy Baseline",
  "4. Systems Inventory (Yes/No/Unsure)",
  "5. Lighting Details",
  "6. Heating Details",
  "7. Boiler Details",
  "8. Electric Heaters Details",
  "9. Cooling Details",
  "10. Ventilation Details",
  "11. Refrigeration Details",
  "12. Process Loads (Misc electricity/Other)",
  "13. Solar PV Details",
  "14. Preferences",
  "15. Final Checks",
];

function groupFieldsBySection(fields: QuestionnaireField[]) {
  const map = new Map<string, QuestionnaireField[]>();
  for (const field of fields) {
    if (!map.has(field.section)) {
      map.set(field.section, []);
    }
    map.get(field.section)!.push(field);
  }
  return map;
}

const fieldsBySection = groupFieldsBySection(questionnaireFields);

function useAutosave(values: QuestionnaireFormValues) {
  useEffect(() => {
    const handler = () => {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
    };
    const interval = window.setInterval(handler, 10_000);
    window.addEventListener("beforeunload", handler);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("beforeunload", handler);
    };
  }, [values]);
}

function evaluateShowIf(
  field: QuestionnaireField,
  values: QuestionnaireFormValues,
): boolean {
  if (!field.showIf) return true;
  const target = values[field.showIf.field as keyof QuestionnaireFormValues];
  if (field.showIf.equals != null) {
    return target === field.showIf.equals;
  }
  if (field.showIf.in) {
    return field.showIf.in.includes(String(target));
  }
  return true;
}

function clearHiddenFields(
  values: QuestionnaireFormValues,
  fields: QuestionnaireField[],
): QuestionnaireFormValues {
  const next = { ...values };
  for (const field of fields) {
    const visible = evaluateShowIf(field, values);
    if (!visible) {
      (next as any)[field.name] = undefined;
    }
  }
  return next;
}

function SectionFields({ section }: { section: string }) {
  const { register, formState, watch, setValue } =
    useFormContext<QuestionnaireFormValues>();
  const allValues = watch();
  const sectionFields = fieldsBySection.get(section) ?? [];

  useEffect(() => {
    const cleared = clearHiddenFields(allValues, sectionFields);
    for (const key of Object.keys(cleared) as (keyof QuestionnaireFormValues)[]) {
      if (cleared[key] !== allValues[key]) {
        setValue(key, cleared[key]);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allValues, sectionFields, setValue]);

  return (
    <div className="space-y-4">
      {sectionFields.map((field) => {
        const visible = evaluateShowIf(field, allValues);
        if (!visible) return null;
        const error = formState.errors[field.name as keyof QuestionnaireFormValues];
        const fieldId = `field-${field.name}`;
        const helpId = field.helpText ? `${fieldId}-help` : undefined;
        const errorId = error ? `${fieldId}-error` : undefined;

        const baseProps = {
          id: fieldId,
          "aria-describedby": [helpId, errorId].filter(Boolean).join(" ") || undefined,
          "aria-invalid": !!error || undefined,
        };

        return (
          <div key={field.name} className="space-y-1">
            <label
              htmlFor={fieldId}
              className="block text-sm font-medium text-slate-900"
            >
              {field.label}
              {field.required && <span className="ml-1 text-red-600">*</span>}
            </label>
            {field.type === "text" || field.type === "email" ? (
              <input
                type={field.type === "email" ? "email" : "text"}
                className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                {...baseProps}
                {...register(field.name as any)}
              />
            ) : field.type === "number" ? (
              <input
                type="number"
                className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                {...baseProps}
                {...register(field.name as any, { valueAsNumber: true })}
              />
            ) : field.type === "checkbox" ? (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  {...baseProps}
                  {...register(field.name as any)}
                />
                <span className="text-sm text-slate-700">
                  I agree to the statement above.
                </span>
              </div>
            ) : field.type === "dropdown" ? (
              <select
                className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                {...baseProps}
                {...register(field.name as any)}
              >
                <option value="">Select…</option>
                {field.options?.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            ) : field.type === "multiselect" ? (
              <div className="space-y-1">
                {field.options?.map((opt) => (
                  <label
                    key={opt}
                    className="flex items-center gap-2 text-sm text-slate-700"
                  >
                    <input
                      type="checkbox"
                      value={opt}
                      className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                      {...register(field.name as any)}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            ) : null}

            {field.helpText && (
              <p id={helpId} className="text-xs text-slate-500">
                {field.helpText}
              </p>
            )}
            {error && (
              <p id={errorId} className="text-xs text-red-600" role="alert">
                {(error as any).message}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface QuestionnaireFormProps {
  onComplete: () => void;
}

export function QuestionnaireForm({ onComplete }: QuestionnaireFormProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const defaultValues = useMemo(() => {
    if (typeof window === "undefined") {
      return {} as QuestionnaireFormValues;
    }
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return {} as QuestionnaireFormValues;
    try {
      return JSON.parse(stored) as QuestionnaireFormValues;
    } catch {
      return {} as QuestionnaireFormValues;
    }
  }, []);

  const methods = useForm<QuestionnaireFormValues>({
    resolver: zodResolver(questionnaireSchema),
    defaultValues,
    mode: "onBlur",
  });

  const { handleSubmit, watch } = methods;
  const values = watch();
  useAutosave(values);

  const onNext = async () => {
    const section = stepsOrder[currentStepIndex];
    const sectionFields = fieldsBySection.get(section) ?? [];
    const fieldNames = sectionFields.map((f) => f.name as keyof QuestionnaireFormValues);
    const result = await methods.trigger(fieldNames as any);
    if (!result) return;
    setCurrentStepIndex((idx) => Math.min(idx + 1, stepsOrder.length - 1));
  };

  const onPrev = () => {
    setCurrentStepIndex((idx) => Math.max(idx - 1, 0));
  };

  const onSubmit = handleSubmit(async (data) => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    onComplete();
  });

  const isLastStep = currentStepIndex === stepsOrder.length - 1;

  return (
    <FormProvider {...methods}>
      <form
        onSubmit={onSubmit}
        className="space-y-6"
        aria-label="Net zero energy questionnaire"
      >
        <ProgressWizard steps={stepsOrder} currentStepIndex={currentStepIndex} />

        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">
            {stepsOrder[currentStepIndex]}
          </h2>
          <SectionFields section={stepsOrder[currentStepIndex]} />
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onPrev}
            disabled={currentStepIndex === 0}
            className="inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Previous
          </button>
          {isLastStep ? (
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            >
              Review &amp; confirm
            </button>
          ) : (
            <button
              type="button"
              onClick={onNext}
              className="inline-flex items-center justify-center rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            >
              Next
            </button>
          )}
        </div>
      </form>
    </FormProvider>
  );
}

