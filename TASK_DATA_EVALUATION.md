# Parallel task B: Data, rubric, and evaluation pipeline

Read `CLAUDE.md` completely before working. This task runs in parallel with `TASK_AI_BACKEND.md`. Do not edit `backend/**`, `contracts/**`, or `frontend/**`.

## Objective

Produce the reproducible data and evaluation assets needed to support two separate claims:

1. Problem evidence: information gaps were observed in a carefully matched exploratory sample of Jeonbuk and metropolitan postings.
2. Model evidence: the extraction pipeline can reproduce human labels and exact evidence spans on an untouched holdout.

Do not use model-generated labels as ground truth and do not make causal or population-wide regional claims.

## Phase 1: Source and occupation feasibility scan

Create a source inventory recording:

- source name
- access method
- license/terms status
- date range
- available Jeonbuk count by candidate occupation
- available metropolitan count
- employment-type availability
- whether full text may be redistributed
- blockers such as missing credentials

Use public/open sources or user-provided postings. Do not scrape private recruitment platforms. If an API key is unavailable, document the blocker and build an import template; do not invent postings or statistics.

Choose one occupation only after verifying:

- at least 10 Jeonbuk postings are actually obtainable from the same source and period;
- metropolitan matches are obtainable for the same occupation and employment type; and
- the team can reasonably adjudicate the six fields for that occupation.

Target 20:20 only after the 10:10 minimum is complete.

## Phase 2: Versioned rubric

Create a machine-readable rubric such as `data/rubric.yaml` plus a human-readable explanation.

For each of the six fields define:

- `confirmed` criteria
- `vague` criteria
- `absent` criteria
- positive examples
- boundary examples
- deterministic checks where possible
- rubric version

The controlling principle is:

> Distinguish wording being present from decision-useful information being present.

Do not include an `external_verified` posting status. Decide explicitly how occupation-specific concepts map to `tools_or_skills` and `training_or_mentoring` so irrelevant fields are not accidentally counted as absent.

## Phase 3: Curated matched corpus

Create records with at least:

- stable internal posting ID
- region group
- municipality where available
- occupation
- employment type
- collection date
- source name
- source ID/URL
- redistributable full text or a private/local text reference
- matched-pair ID
- match criteria
- unmatched flag and factual reason such as `no candidate found under recorded query`

Never interpret an unmatched record as proof of regional job scarcity.

If full text redistribution is not permitted, keep it out of the publishable dataset and generate separate synthetic fixtures for repository tests and demos.

## Phase 4: Human annotation workflow

Create annotation sheets/files for two independent human annotators. Each annotator labels every posting-field cell with:

- `confirmed`, `vague`, or `absent`
- exact evidence text and offsets for confirmed/vague
- reason code
- optional disagreement note
- rubric version

AI may prepare suggestions in a visually separate column, but those suggestions must not be copied into gold automatically.

Provide a validation script that checks:

- six fields per posting
- allowed statuses only
- evidence required for confirmed/vague
- null evidence for absent
- offset and substring correctness
- no duplicate IDs
- matched-pair integrity

Provide an adjudication workflow that preserves:

- annotator A label
- annotator B label
- raw agreement/disagreement
- adjudicated gold label
- adjudicator note

Compute percent agreement and, if meaningful for the resulting distribution, Cohen's kappa. Treat low agreement as a rubric issue to investigate, not as evidence that postings are inherently bad.

## Phase 5: Frozen split

After adjudication:

1. Create a development split and a stratified 20% holdout.
2. Include both regions in the holdout.
3. Avoid concentrating all rare statuses in one split where possible.
4. Write a manifest with posting IDs, rubric version, timestamp, and checksum.
5. Mark the holdout read-only by convention and document that it must not be used for prompt tuning.

With only 10:10 postings, plan to report raw correct/incorrect counts and overall three-class agreement. Per-field F1 on four holdout postings is not defensible as a primary result.

## Phase 6: Statistics and evaluation scripts

Implement scripts that calculate from human gold labels only:

- posting and cell counts
- status proportions by region and field
- annotator agreement
- matched-pair descriptive differences
- unmatched counts as observations only
- model-vs-gold confusion matrix when predictions are supplied
- overall accuracy/agreement
- macro metrics only with prominent sample-size output
- unsupported/fabricated evidence count
- schema failure count

Every report must include:

- sample size
- data source
- collection period
- occupation
- employment type
- rubric version
- `exploratory sample; not population-generalizable`

## Publishable assets

Prepare two layers:

### Internal/local layer

May contain full posting text when lawfully obtained for the hackathon workspace.

### Public repository layer

Contains only what licensing permits, preferably:

- rubric
- annotation schema
- source IDs and links
- derived labels
- aggregate statistics
- synthetic examples
- collection methodology

Do not assume that public accessibility grants redistribution permission.

## Deliverables

- source feasibility inventory
- occupation-selection note
- versioned rubric in YAML and Markdown
- curated posting metadata and matched-pair table
- independent annotation templates
- adjudication template
- validated gold dataset when two human passes are actually complete
- development/holdout manifests
- dataset validation script and tests
- aggregate-statistics script and tests
- evaluation script accepting backend prediction JSONL
- generated exploratory report with careful wording
- `DATA_HANDOFF.md` documenting paths, schemas, limitations, and any missing human work

## Completion check

Run and report:

1. dataset validator;
2. annotation integrity checks;
3. split/checksum generation;
4. aggregate report generation; and
5. evaluation on a synthetic prediction fixture.

If two independent humans have not completed annotation, do not label the result `gold`, do not create a misleading performance claim, and list the exact remaining manual steps.

