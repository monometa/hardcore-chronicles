# IMPORTANT


you are not allowed to look under auditor_1 and auditor_3 folders so your judjment will be independent!


# Task: Repository Audit

You are an AI auditor. Your goal is to independently review this repository and produce a clear, useful audit report.

The repository should contain enough context for the review. Use the repository contents as the primary source of truth. Do not invent missing details. If important context, data, methodology, assumptions, audience profiles, or expected outcomes are missing, highlight that clearly in your final report.

Your final output must be a file named:

```text
report.md
```

## Main Objective

Audit the project for:

1. Correctness and completeness of the source data.
2. Soundness of the methodology.
3. Correctness and reproducibility of the final results.
4. Quality of the visualization and presentation.
5. Fit for the intended audience, including whether the project is interesting, engaging, informative, and ready to be shared with friends for review.

## Scope of the Audit

Review all relevant repository materials, including but not limited to:

- README files.
- Data files or data references.
- Notebooks.
- Scripts.
- Configuration files.
- Documentation.
- Methodology notes.
- Generated outputs.
- Visualizations.
- Any files describing the target audience, user profiles, personas, or intended reviewers.

If the repository contains multiple possible entry points, identify the most likely project flow and explain your reasoning in the report.

## Audit Requirements

### 1. Source Data Review

Evaluate whether the source data used by the project is appropriate, reliable, and sufficient.

Check:

- What data sources are used.
- Whether the data origin is documented.
- Whether the dataset is complete enough for the stated goal.
- Whether there are obvious missing fields, duplicates, inconsistencies, invalid values, or suspicious outliers.
- Whether filtering, cleaning, or preprocessing steps are documented and reasonable.
- Whether assumptions about the data are explicit.
- Whether data limitations are acknowledged.

In the report, clearly state whether the data is trustworthy enough to support the final output.

### 2. Methodology Review

Evaluate whether the analytical approach is logically sound.

Check:

- Whether the project goal is clearly defined.
- Whether the methodology matches the stated goal.
- Whether calculations, transformations, aggregations, and metrics are correct.
- Whether assumptions are reasonable and visible.
- Whether there are methodological gaps, shortcuts, or unsupported conclusions.
- Whether alternative interpretations should be considered.
- Whether the analysis can be reproduced from the repository.

If the methodology is unclear or incomplete, explain exactly what is missing.

### 3. Results Review

Evaluate whether the final results are correct and supported by the data and methodology.

Check:

- Whether the final conclusions follow from the analysis.
- Whether the numbers, charts, tables, and narrative are internally consistent.
- Whether any results look surprising, misleading, exaggerated, or unsupported.
- Whether the final output can be regenerated.
- Whether there are contradictions between source data, intermediate outputs, and final visualizations.

Separate confirmed issues from possible risks.

### 4. Visualization and Presentation Review

Evaluate the quality of the visual output and overall presentation.

Check:

- Clarity of charts, labels, legends, titles, annotations, and units.
- Whether the visualization tells a coherent story.
- Whether the layout is easy to understand.
- Whether the design supports the message rather than distracting from it.
- Whether the visual hierarchy is clear.
- Whether color, spacing, typography, and formatting are effective.
- Whether the project looks polished enough to share externally.
- Whether the output is accessible to people who did not work on the project.

Call out both strengths and weaknesses.

### 5. Audience Fit Review

The project is intended to be shared with friends for review. Look for any repository context describing the people, audience profiles, personas, or intended reviewers.

Assess whether the project is:

- Interesting.
- Engaging.
- Informative.
- Easy to understand.
- Memorable.
- Visually appealing.
- Worth sharing in its current state.
- Likely to generate useful feedback from friends.

If audience profiles are present, evaluate the visualization against those profiles.

If audience profiles are missing or incomplete, state that clearly and explain what kind of audience information would improve the review.

### 6. Readiness Assessment

Give a final readiness verdict.

Use one of the following statuses:

```text
Ready to share
Mostly ready, minor fixes needed
Not ready, major fixes needed
Cannot determine from repository context
```

Explain the verdict briefly and directly.

## Required Output: report.md

Create a file named `report.md` with the following structure:

```markdown
# Audit Report

## Executive Summary

Briefly summarize the overall state of the project and the final readiness verdict.

## Readiness Verdict

Status: <one of the allowed statuses>

Explain the verdict.

## Repository Context Reviewed

List the main files, folders, notebooks, scripts, data files, and outputs you reviewed.

If important files were expected but not found, mention them here.

## Source Data Audit

Assess the data quality, completeness, provenance, assumptions, and limitations.

## Methodology Audit

Assess whether the methodology is clear, correct, reproducible, and appropriate for the project goal.

## Results Audit

Assess whether the final results are supported by the data and methodology.

## Visualization and Presentation Audit

Assess clarity, structure, design quality, storytelling, and polish.

## Audience Fit

Assess whether the project is interesting, engaging, informative, and suitable for the intended reviewers.

If audience profiles are missing, say so.

## Strengths

List the strongest parts of the project.

## Issues and Risks

List confirmed issues first, then possible risks.

For each issue, include:

- Severity: Critical, High, Medium, or Low.
- Area: Data, Methodology, Results, Visualization, Presentation, Audience Fit, or Reproducibility.
- Description.
- Evidence from the repository.
- Recommended fix.

## Missing Context

List any important missing information that prevented a complete audit.

## Recommended Fixes Before Sharing

Provide a prioritized checklist of changes that should be made before sending the project to friends for review.

## Final Notes

Add any additional observations that would help improve the project.
```

## Evidence Requirements

Whenever possible, reference the specific file path, section, function, notebook cell, chart, or data artifact that supports your observation.

Do not make unsupported claims. If something is uncertain, label it as uncertain.

## Working Rules

- Do not modify the project files, except for creating `report.md`.
- Do not delete, overwrite, or reformat existing files.
- Do not rely on external information unless the repository explicitly requires it.
- Prefer repository evidence over assumptions.
- If code execution is safe and supported by the repository, run the relevant scripts or notebooks needed to verify reproducibility.
- If code execution is not possible, explain why in `report.md`.
- Be direct, practical, and specific.
- Avoid vague feedback such as “improve the design” without explaining what exactly should be improved.
- Separate objective correctness issues from subjective presentation feedback.

## Final Deliverable

At the end of the task, the repository must contain:

```text
report.md
```

The report should be clear enough that the project owner can immediately understand:

1. Whether the project is ready to share.
2. What is already working well.
3. What is wrong or risky.
4. What should be fixed first.
5. What context is missing.
