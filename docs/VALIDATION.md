# LLM recommendation validation

This module validates LLM-generated recommendations against deterministic calculator outputs and
ensures that all numeric values in the final report remain deterministic.

## Flow

1. The pipeline computes **baseline** and **candidate measures** using the deterministic
   calculators in `backend/calculators`.
2. The LLM receives a prompt that includes those deterministic numbers and returns JSON:
   `{"executive_summary": "...", "recommendations": [...]}`.
3. `rag.validation.validate_recommendations` is called with:
   - `baseline` (summary dict),
   - `candidates` (list of deterministic measure dicts),
   - `llm_recs` (raw LLM recommendations).
4. For each recommendation:
   - Deterministic numeric fields (`kwh_saved`, `cost_saved`, `carbon_saved`, `simple_payback`)
     are derived from the candidate data.
   - If the LLM supplied numbers, they are compared to deterministic ones using tolerances.
   - The final recommendation object is normalised and stored in `report_json`.

## Tolerances

Default tolerances (relative error):

- `kwh_saved`: 5%
- `cost_saved`: 5%
- `carbon_saved`: 5%
- `simple_payback`: 10%

They can be overridden via the `tolerance` argument to `validate_recommendations`.

## Confidence and validation notes

For each recommendation:

- **Numbers match within tolerance**
  - `confidence`: `"high"`
  - `validation_notes`: `null`

- **Numbers differ beyond tolerance**
  - `confidence`: `"low"`
  - `validation_notes`: `{"mismatch": {field: {"expected": X, "reported": Y, "delta_pct": Z}}}`

- **LLM omitted numeric fields**
  - Deterministic numbers are filled in from calculators.
  - `confidence`: `"high"`
  - `validation_notes`: `"numbers filled by deterministic calculators"`

## Final recommendation shape

Every validated recommendation has:

- `measure_code`
- `recommendation_text`
- `priority`
- `score` (optional)
- `confidence` (`high` / `medium` / `low`)
- `kwh_saved`
- `cost_saved`
- `carbon_saved`
- `simple_payback`
- `applicability_hint`
- `validation_notes`

The `RecommendationModel` Pydantic model in `rag/validation.py` enforces this shape before the
object is persisted into `report_json`.

