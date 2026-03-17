export type FieldType =
  | "text"
  | "email"
  | "number"
  | "checkbox"
  | "dropdown"
  | "multiselect";

export interface ShowIfRule {
  field: string;
  equals?: string;
  in?: string[];
}

export interface QuestionnaireField {
  section: string;
  name: string;
  label: string;
  type: FieldType;
  required: boolean;
  options?: string[];
  validation?: string | null;
  showIf?: ShowIfRule | null;
  helpText?: string | null;
}

export interface Questionnaire {
  consent_self_reported: boolean;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone: string;
  business_name: string;
  site_address_line1: string;
  site_postcode: string;
  sector: string;
  employees_on_site: number;
  days_open_per_week: string;
  weekly_operational_hours: number;
  ownership_status: string;
  building_type: string;
  floor_area_band: string;
  building_age_band: string;
  insulation_level: string;
  glazing_type: string;
  epc_known: string;
  epc_rating?: string;
  electricity_kwh_annual: number;
  electricity_cost_annual_ex_vat: number;
  uses_gas: string;
  gas_kwh_annual?: number;
  gas_cost_annual_ex_vat?: number;
  gas_usage_purpose?: string;
  other_fuels: string;
  other_fuels_spend_annual?: number;
  has_lighting: string;
  has_space_heating: string;
  has_boiler: string;
  has_heat_pump: string;
  uses_electric_heaters: string;
  has_cooling: string;
  has_ventilation: string;
  has_refrigeration: string;
  has_process_loads: string;
  consider_solar_pv: string;
  lighting_type?: string;
  lighting_controls?: string[];
  low_occupancy_areas_left_on?: string;
  heating_main_type?: string;
  heating_controls?: string[];
  heating_age_band?: string;
  heating_common_issues?: string;
  boiler_fuel?: string;
  boiler_age_band?: string;
  boiler_controls?: string;
  electric_heaters_type?: string;
  electric_heaters_frequency?: string;
  cooling_type?: string;
  cooling_usage?: string;
  cooling_age_band?: string;
  ventilation_schedule?: string;
  ventilation_controls?: string;
  heat_recovery_present?: string;
  refrigeration_types?: string[];
  refrigeration_count_band?: string;
  refrigeration_24_7?: string;
  process_load_types?: string[];
  process_load_intensity?: string;
  roof_control_permission?: string;
  roof_type?: string;
  roof_area_band?: string;
  roof_shading?: string;
  primary_priority: string;
  budget_band: string;
  implementation_timeframe: string;
  other_major_energy_users: string;
  other_major_energy_users_desc?: string;
}

export const questionnaireFields: QuestionnaireField[] = [
  // 0. Consent & Contact
  {
    section: "0. Consent & Contact",
    name: "consent_self_reported",
    label:
      "Consent: I confirm info is accurate and recommendations are based on self‑reported data",
    type: "checkbox",
    required: true,
    options: ["Checked"],
    validation: "Must be checked",
    showIf: null,
    helpText: null,
  },
  {
    section: "0. Consent & Contact",
    name: "primary_contact_name",
    label: "Primary contact full name",
    type: "text",
    required: true,
    validation: "2–80 chars",
    showIf: null,
    helpText: null,
  },
  {
    section: "0. Consent & Contact",
    name: "primary_contact_email",
    label: "Primary contact email",
    type: "email",
    required: true,
    validation: "Valid email",
    showIf: null,
    helpText: null,
  },
  {
    section: "0. Consent & Contact",
    name: "primary_contact_phone",
    label: "Primary contact phone number",
    type: "text",
    required: true,
    validation: "UK phone format (len 10–15)",
    showIf: null,
    helpText: null,
  },
  // 1. Business Profile
  {
    section: "1. Business Profile",
    name: "business_name",
    label: "Business name",
    type: "text",
    required: true,
    validation: "2–120 chars",
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "site_address_line1",
    label: "Site address line 1",
    type: "text",
    required: true,
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "site_postcode",
    label: "Postcode",
    type: "text",
    required: true,
    validation: "UK postcode",
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "sector",
    label: "Sector / business activity",
    type: "dropdown",
    required: true,
    options: [
      "Catering/Food prep",
      "Retail",
      "Office",
      "Hospitality",
      "Warehouse/Logistics",
      "Light industrial",
      "Healthcare",
      "Education",
      "Other",
    ],
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "employees_on_site",
    label: "Typical number of employees on site",
    type: "number",
    required: true,
    validation: "0–5000",
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "days_open_per_week",
    label: "Days open per week",
    type: "dropdown",
    required: true,
    options: ["1", "2", "3", "4", "5", "6", "7"],
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "weekly_operational_hours",
    label: "Weekly operational hours (total)",
    type: "number",
    required: true,
    validation: "1–168",
    showIf: null,
    helpText: null,
  },
  {
    section: "1. Business Profile",
    name: "ownership_status",
    label: "Occupancy/ownership status",
    type: "dropdown",
    required: true,
    options: ["Owner‑occupier", "Tenant/lease", "Shared", "Unsure"],
    showIf: null,
    helpText: null,
  },
  // 2. Building Basics
  {
    section: "2. Building Basics",
    name: "building_type",
    label: "Building type",
    type: "dropdown",
    required: true,
    options: [
      "Industrial unit",
      "Office",
      "Retail unit",
      "Warehouse",
      "Mixed‑use",
      "Other",
    ],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "floor_area_band",
    label: "Approximate floor area band (m²)",
    type: "dropdown",
    required: true,
    options: [
      "<100",
      "100–250",
      "250–500",
      "500–1,000",
      "1,000–2,000",
      ">2,000",
      "Unsure",
    ],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "building_age_band",
    label: "Building age band (best guess)",
    type: "dropdown",
    required: true,
    options: ["Pre‑1980", "1980–2000", "2001–2015", "2016+", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "insulation_level",
    label: "Insulation level (best guess)",
    type: "dropdown",
    required: true,
    options: ["Poor", "Average", "Good", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "glazing_type",
    label: "Window/glazing type (best guess)",
    type: "dropdown",
    required: true,
    options: ["Single", "Double", "Triple", "Mixed", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "epc_known",
    label: "Do you know your EPC rating?",
    type: "dropdown",
    required: true,
    options: ["Yes", "No"],
    showIf: null,
    helpText: null,
  },
  {
    section: "2. Building Basics",
    name: "epc_rating",
    label: "EPC rating",
    type: "dropdown",
    required: true,
    options: ["A", "B", "C", "D", "E", "F", "G", "Unknown"],
    showIf: { field: "epc_known", equals: "Yes" },
    helpText: null,
  },
  // 3. Energy Baseline
  {
    section: "3. Energy Baseline",
    name: "electricity_kwh_annual",
    label: "Electricity consumption (last 12 months)",
    type: "number",
    required: true,
    validation: "kWh/year; >0",
    showIf: null,
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "electricity_cost_annual_ex_vat",
    label: "Electricity cost (last 12 months, excl. VAT)",
    type: "number",
    required: true,
    validation: "£/year; >0",
    showIf: null,
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "uses_gas",
    label: "Do you use mains gas at this site?",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "gas_kwh_annual",
    label: "Gas consumption (last 12 months)",
    type: "number",
    required: true,
    validation: "kWh/year; >0",
    showIf: { field: "uses_gas", equals: "Yes" },
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "gas_cost_annual_ex_vat",
    label: "Gas cost (last 12 months, excl. VAT)",
    type: "number",
    required: true,
    validation: "£/year; >0",
    showIf: { field: "uses_gas", equals: "Yes" },
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "gas_usage_purpose",
    label: "Main gas use",
    type: "dropdown",
    required: true,
    options: [
      "Space heating",
      "Hot water",
      "Cooking/process",
      "Mixed",
      "Unsure",
    ],
    showIf: { field: "uses_gas", equals: "Yes" },
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "other_fuels",
    label: "Do you use any other fuels onsite (LPG/oil/biomass)?",
    type: "dropdown",
    required: true,
    options: ["No", "Yes", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "3. Energy Baseline",
    name: "other_fuels_spend_annual",
    label: "If yes: Total annual spend on other fuels (approx.)",
    type: "number",
    required: true,
    validation: "£/year; >=0",
    showIf: { field: "other_fuels", equals: "Yes" },
    helpText: null,
  },
  // 4. Systems Inventory
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_lighting",
    label: "Lighting installed (all sites)",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    validation: "Default: Yes",
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_space_heating",
    label: "Space heating present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_boiler",
    label: "Boiler present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_heat_pump",
    label: "Heat pump present (existing)",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "uses_electric_heaters",
    label: "Electric heaters used (portable or fixed)",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_cooling",
    label: "Cooling / air conditioning present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_ventilation",
    label: "Mechanical ventilation / extraction present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_refrigeration",
    label: "Refrigeration/freezers/cold rooms present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "has_process_loads",
    label:
      "Major process loads (e.g., catering equipment, compressors)",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "4. Systems Inventory (Yes/No/Unsure)",
    name: "consider_solar_pv",
    label: "Consider rooftop solar PV for this site",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: null,
    helpText: null,
  },
  // 5. Lighting Details
  {
    section: "5. Lighting Details",
    name: "lighting_type",
    label: "Main lighting type",
    type: "dropdown",
    required: true,
    options: [
      "Mostly LED",
      "Mostly fluorescent",
      "Mostly halogen",
      "Mixed",
      "Unsure",
    ],
    showIf: { field: "has_lighting", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "5. Lighting Details",
    name: "lighting_controls",
    label: "Lighting controls present",
    type: "multiselect",
    required: true,
    options: [
      "Manual switches only",
      "Timers",
      "Occupancy sensors (PIR)",
      "Daylight sensors",
      "Central/BMS control",
      "Unsure",
    ],
    showIf: { field: "has_lighting", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "5. Lighting Details",
    name: "low_occupancy_areas_left_on",
    label: "Low-occupancy areas where lights are often left on",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: { field: "has_lighting", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 6. Heating Details
  {
    section: "6. Heating Details",
    name: "heating_main_type",
    label: "Main space-heating type",
    type: "dropdown",
    required: true,
    options: [
      "Gas boiler",
      "Electric heaters",
      "Heat pump",
      "Oil/LPG boiler",
      "District heat",
      "None",
      "Unsure",
    ],
    showIf: { field: "has_space_heating", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "6. Heating Details",
    name: "heating_controls",
    label: "Heating controls present",
    type: "multiselect",
    required: true,
    options: [
      "Programmable timer",
      "Thermostats/TRVs",
      "Zoning",
      "Weather compensation",
      "Optimum start/stop",
      "BMS",
      "None/Unsure",
    ],
    showIf: { field: "has_space_heating", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "6. Heating Details",
    name: "heating_age_band",
    label: "Heating system age (best guess)",
    type: "dropdown",
    required: true,
    options: ["<5 years", "5–10", "10–15", "15+", "Unsure"],
    showIf: { field: "has_space_heating", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "6. Heating Details",
    name: "heating_common_issues",
    label: "Common heating issue",
    type: "dropdown",
    required: true,
    options: [
      "Overheating",
      "Underheating",
      "Runs when building is empty",
      "Uneven temperatures",
      "No issues/Unsure",
    ],
    showIf: { field: "has_space_heating", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 7. Boiler Details
  {
    section: "7. Boiler Details",
    name: "boiler_fuel",
    label: "Boiler fuel type",
    type: "dropdown",
    required: true,
    options: ["Natural gas", "LPG", "Oil", "Biomass", "Unsure"],
    showIf: { field: "has_boiler", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "7. Boiler Details",
    name: "boiler_age_band",
    label: "Boiler age band (best guess)",
    type: "dropdown",
    required: true,
    options: ["<5 years", "5–10", "10–15", "15+", "Unsure"],
    showIf: { field: "has_boiler", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "7. Boiler Details",
    name: "boiler_controls",
    label: "Boiler/control sophistication",
    type: "dropdown",
    required: true,
    options: [
      "Modern controls (compensation/zoning)",
      "Basic timer/thermostat",
      "Manual/none",
      "Unsure",
    ],
    showIf: { field: "has_boiler", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 8. Electric Heaters Details
  {
    section: "8. Electric Heaters Details",
    name: "electric_heaters_type",
    label: "Most common electric heater type",
    type: "dropdown",
    required: true,
    options: [
      "Portable plug-in heaters",
      "Fan heaters",
      "Electric radiators",
      "Infrared",
      "Storage heaters",
      "Unsure",
    ],
    showIf: { field: "uses_electric_heaters", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "8. Electric Heaters Details",
    name: "electric_heaters_frequency",
    label: "How often are electric heaters used?",
    type: "dropdown",
    required: true,
    options: ["Occasionally", "Frequently", "Daily", "Unsure"],
    showIf: { field: "uses_electric_heaters", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 9. Cooling Details
  {
    section: "9. Cooling Details",
    name: "cooling_type",
    label: "Cooling type",
    type: "dropdown",
    required: true,
    options: ["Split AC", "VRF/VRV", "Packaged rooftop", "Portable units", "Chiller", "Unsure"],
    showIf: { field: "has_cooling", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "9. Cooling Details",
    name: "cooling_usage",
    label: "Cooling usage pattern (typical)",
    type: "dropdown",
    required: true,
    options: ["Rarely", "Some days", "Most days", "Every day", "Unsure"],
    showIf: { field: "has_cooling", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "9. Cooling Details",
    name: "cooling_age_band",
    label: "Cooling system age (best guess)",
    type: "dropdown",
    required: true,
    options: ["<5 years", "5–10", "10–15", "15+", "Unsure"],
    showIf: { field: "has_cooling", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 10. Ventilation Details
  {
    section: "10. Ventilation Details",
    name: "ventilation_schedule",
    label: "Ventilation/extraction runs",
    type: "dropdown",
    required: true,
    options: ["Only during opening hours", "Extended hours", "24/7", "Intermittent", "Unsure"],
    showIf: { field: "has_ventilation", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "10. Ventilation Details",
    name: "ventilation_controls",
    label: "Ventilation controls",
    type: "dropdown",
    required: true,
    options: ["Manual only", "Timer/scheduled", "Demand-controlled", "Variable speed", "Unsure"],
    showIf: { field: "has_ventilation", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "10. Ventilation Details",
    name: "heat_recovery_present",
    label: "Heat recovery (MVHR/HRU) present",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: { field: "has_ventilation", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 11. Refrigeration Details
  {
    section: "11. Refrigeration Details",
    name: "refrigeration_types",
    label: "Refrigeration types present",
    type: "multiselect",
    required: true,
    options: [
      "Display fridges",
      "Upright fridges",
      "Chest freezers",
      "Walk-in cold room",
      "Walk-in freezer",
      "Ice machine",
      "Mixed/Unsure",
    ],
    showIf: { field: "has_refrigeration", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "11. Refrigeration Details",
    name: "refrigeration_count_band",
    label: "Approx. number of refrigeration units",
    type: "dropdown",
    required: true,
    options: ["1–2", "3–5", "6–10", "11+", "Unsure"],
    showIf: { field: "has_refrigeration", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "11. Refrigeration Details",
    name: "refrigeration_24_7",
    label: "Do any refrigeration units run 24/7?",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: { field: "has_refrigeration", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 12. Process Loads
  {
    section: "12. Process Loads (Misc electricity/Other)",
    name: "process_load_types",
    label: "Major process load types",
    type: "multiselect",
    required: true,
    options: [
      "Catering equipment",
      "Compressed air",
      "Industrial machinery",
      "IT/server room",
      "EV chargers",
      "Other/Unsure",
    ],
    showIf: { field: "has_process_loads", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "12. Process Loads (Misc electricity/Other)",
    name: "process_load_intensity",
    label: "Overall electricity intensity relative to similar businesses",
    type: "dropdown",
    required: true,
    options: ["Low", "Medium", "High", "Unsure"],
    showIf: { field: "has_process_loads", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 13. Solar PV Details
  {
    section: "13. Solar PV Details",
    name: "roof_control_permission",
    label:
      "Do you control the roof / have landlord permission for rooftop works?",
    type: "dropdown",
    required: true,
    options: ["Yes", "No", "Unsure"],
    showIf: { field: "consider_solar_pv", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "13. Solar PV Details",
    name: "roof_type",
    label: "Roof type",
    type: "dropdown",
    required: true,
    options: ["Flat", "Pitched", "Mixed", "Unsure"],
    showIf: { field: "consider_solar_pv", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "13. Solar PV Details",
    name: "roof_area_band",
    label: "Usable roof area band",
    type: "dropdown",
    required: true,
    options: [
      "<50m²",
      "50–150m²",
      "150–300m²",
      "300–600m²",
      ">600m²",
      "Unsure",
    ],
    showIf: { field: "consider_solar_pv", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  {
    section: "13. Solar PV Details",
    name: "roof_shading",
    label: "Roof shading level",
    type: "dropdown",
    required: true,
    options: ["None", "Some", "Heavy", "Unsure"],
    showIf: { field: "consider_solar_pv", in: ["Yes", "Unsure"] },
    helpText: null,
  },
  // 14. Preferences
  {
    section: "14. Preferences",
    name: "primary_priority",
    label: "Primary priority",
    type: "dropdown",
    required: true,
    options: ["Fast payback", "Biggest carbon reduction", "Balanced"],
    showIf: null,
    helpText: null,
  },
  {
    section: "14. Preferences",
    name: "budget_band",
    label: "Investment comfort level (budget band)",
    type: "dropdown",
    required: true,
    options: ["£0–1k", "£1–5k", "£5–25k", "£25k+", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "14. Preferences",
    name: "implementation_timeframe",
    label: "Preferred implementation timeframe",
    type: "dropdown",
    required: true,
    options: ["0–3 months", "3–12 months", "12+ months", "Unsure"],
    showIf: null,
    helpText: null,
  },
  // 15. Final Checks
  {
    section: "15. Final Checks",
    name: "other_major_energy_users",
    label: "Any other major energy users not covered above?",
    type: "dropdown",
    required: true,
    options: ["No", "Yes", "Unsure"],
    showIf: null,
    helpText: null,
  },
  {
    section: "15. Final Checks",
    name: "other_major_energy_users_desc",
    label:
      "If yes/unsure: Describe the other major energy users (short)",
    type: "text",
    required: true,
    validation: "5–200 chars",
    showIf: { field: "other_major_energy_users", in: ["Yes", "Unsure"] },
    helpText: null,
  },
];

