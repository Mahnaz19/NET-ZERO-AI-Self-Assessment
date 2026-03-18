import { z } from "zod";
import type { Questionnaire } from "./questionnaire";

export const questionnaireSchema = z
  .object({
    consent_self_reported: z
      .boolean()
      .refine((v) => v, "You must provide consent to continue."),
    primary_contact_name: z
      .string()
      .min(2, "Name must be at least 2 characters.")
      .max(80, "Name must be at most 80 characters."),
    primary_contact_email: z
      .string()
      .email("Please enter a valid email address."),
    primary_contact_phone: z
      .string()
      .min(10, "Phone number seems too short.")
      .max(15, "Phone number seems too long."),
    business_name: z
      .string()
      .min(2, "Business name must be at least 2 characters.")
      .max(120, "Business name must be at most 120 characters."),
    site_address_line1: z.string().min(1, "Address is required."),
    site_postcode: z.string().min(1, "Postcode is required."),
    sector: z.string().min(1, "Sector is required."),
    employees_on_site: z
      .number({ invalid_type_error: "Please enter a number." })
      .min(0)
      .max(5000),
    days_open_per_week: z.string().min(1, "Days open per week is required."),
    weekly_operational_hours: z
      .number({ invalid_type_error: "Please enter a number." })
      .min(1)
      .max(168),
    ownership_status: z.string().min(1, "Occupancy status is required."),
    building_type: z.string().min(1, "Building type is required."),
    floor_area_band: z.string().min(1, "Floor area band is required."),
    building_age_band: z.string().min(1, "Building age band is required."),
    insulation_level: z.string().min(1, "Insulation level is required."),
    glazing_type: z.string().min(1, "Glazing type is required."),
    epc_known: z.string().min(1, "Please indicate whether you know the EPC."),
    epc_rating: z.string().optional(),
    electricity_kwh_annual: z
      .number({ invalid_type_error: "Please enter a number." })
      .gt(0),
    electricity_cost_annual_ex_vat: z
      .number({ invalid_type_error: "Please enter a number." })
      .gt(0),
    uses_gas: z.string().min(1, "Please indicate gas usage."),
    gas_kwh_annual: z
      .number({ invalid_type_error: "Please enter a number." })
      .gt(0)
      .optional(),
    gas_cost_annual_ex_vat: z
      .number({ invalid_type_error: "Please enter a number." })
      .gt(0)
      .optional(),
    gas_usage_purpose: z.string().optional(),
    other_fuels: z.string().min(1, "Please indicate other fuels usage."),
    other_fuels_spend_annual: z
      .number({ invalid_type_error: "Please enter a number." })
      .min(0)
      .optional(),
    has_lighting: z.string().min(1, "This field is required."),
    has_space_heating: z.string().min(1, "This field is required."),
    has_boiler: z.string().min(1, "This field is required."),
    has_heat_pump: z.string().min(1, "This field is required."),
    uses_electric_heaters: z.string().min(1, "This field is required."),
    has_cooling: z.string().min(1, "This field is required."),
    has_ventilation: z.string().min(1, "This field is required."),
    has_refrigeration: z.string().min(1, "This field is required."),
    has_process_loads: z.string().min(1, "This field is required."),
    consider_solar_pv: z.string().min(1, "This field is required."),
    lighting_type: z.string().optional(),
    lighting_controls: z.array(z.string()).optional(),
    low_occupancy_areas_left_on: z.string().optional(),
    heating_main_type: z.string().optional(),
    heating_controls: z.array(z.string()).optional(),
    heating_age_band: z.string().optional(),
    heating_common_issues: z.string().optional(),
    boiler_fuel: z.string().optional(),
    boiler_age_band: z.string().optional(),
    boiler_controls: z.string().optional(),
    electric_heaters_type: z.string().optional(),
    electric_heaters_frequency: z.string().optional(),
    cooling_type: z.string().optional(),
    cooling_usage: z.string().optional(),
    cooling_age_band: z.string().optional(),
    ventilation_schedule: z.string().optional(),
    ventilation_controls: z.string().optional(),
    heat_recovery_present: z.string().optional(),
    refrigeration_types: z.array(z.string()).optional(),
    refrigeration_count_band: z.string().optional(),
    refrigeration_24_7: z.string().optional(),
    process_load_types: z.array(z.string()).optional(),
    process_load_intensity: z.string().optional(),
    roof_control_permission: z.string().optional(),
    roof_type: z.string().optional(),
    roof_area_band: z.string().optional(),
    roof_shading: z.string().optional(),
    primary_priority: z.string().min(1, "Primary priority is required."),
    budget_band: z.string().min(1, "Budget band is required."),
    implementation_timeframe: z
      .string()
      .min(1, "Implementation timeframe is required."),
    other_major_energy_users: z
      .string()
      .min(1, "Please indicate whether there are other major users."),
    other_major_energy_users_desc: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.epc_known === "Yes" && !data.epc_rating) {
      ctx.addIssue({
        path: ["epc_rating"],
        code: z.ZodIssueCode.custom,
        message: "Please provide an EPC rating.",
      });
    }
    if (data.uses_gas === "Yes") {
      if (data.gas_kwh_annual == null) {
        ctx.addIssue({
          path: ["gas_kwh_annual"],
          code: z.ZodIssueCode.custom,
          message: "Please provide gas consumption.",
        });
      }
      if (data.gas_cost_annual_ex_vat == null) {
        ctx.addIssue({
          path: ["gas_cost_annual_ex_vat"],
          code: z.ZodIssueCode.custom,
          message: "Please provide gas cost.",
        });
      }
      if (!data.gas_usage_purpose) {
        ctx.addIssue({
          path: ["gas_usage_purpose"],
          code: z.ZodIssueCode.custom,
          message: "Please provide main gas use.",
        });
      }
    }
    if (data.other_fuels === "Yes" && data.other_fuels_spend_annual == null) {
      ctx.addIssue({
        path: ["other_fuels_spend_annual"],
        code: z.ZodIssueCode.custom,
        message: "Please provide annual other fuels spend.",
      });
    }
    if (
      ["Yes", "Unsure"].includes(data.has_lighting) &&
      !data.lighting_type
    ) {
      ctx.addIssue({
        path: ["lighting_type"],
        code: z.ZodIssueCode.custom,
        message: "Please provide main lighting type.",
      });
    }
    if (
      ["Yes", "Unsure"].includes(data.other_major_energy_users) &&
      !data.other_major_energy_users_desc
    ) {
      ctx.addIssue({
        path: ["other_major_energy_users_desc"],
        code: z.ZodIssueCode.custom,
        message: "Please describe other major energy users.",
      });
    }
  });

export type QuestionnaireFormValues = z.infer<typeof questionnaireSchema> &
  Questionnaire;

