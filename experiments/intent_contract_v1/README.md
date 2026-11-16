# Exposed intent-contract correction

This is a staged source correction, **not an installed feature or a new live
model comparison**. The completed synthetic screen exposed a contradiction:
the prompt asked for the complete placement context while the strict tool
accepted only six intent fields. Both the loopback product client and private
hosted screening draft contained it. The screen and its failures stay frozen.

`model_intent.patch` applies to the project-owned `autorouter/model_intent.py`
with SHA256
`998725516642ca551a4b0ea6b40df3740d8995c60c4f02f31feb545858d8d6f3`.
It explicitly identifies the six schema fields, directs the model to copy only
those choices, and checks current caller choices before validating
the model's arguments. A changed budget must be reported as changed context
even when the response repeats the old budget. Source, permissions, protection,
semantic validation and explicit approval remain mandatory.

The tests apply the patch to **one small temporary module**, load that whole
module, and run the existing shared intent controls plus the two reproduced
regressions. They do not extract functions, create an installation, call an
external model or run KiCad. Run on the current Mac checkout:

```sh
.venv/bin/python -B -m unittest experiments.intent_contract_v1.test_contract
```

The current runtime097 installation, its 479-file full270 population and the
completed hosted screen are deliberately unchanged. Integrate the correction
with the next coherent product batch after that qualification; do not describe
these source tests as installed/GUI or live-model qualification. The matching
private hosted patch also preserves tool descriptions and fixes stale-response
classification; it remains local with its frozen baseline and offline proof.
An earlier draft duplicated the intent inside its context and exceeded the
existing 8,192 input preflight bound. That refusal is retained; the correction
uses concise instructions instead of adding context or raising the bound.

Remaining model-quality issues include policy-aware framing of source-scope
limitations, actionable complete clarification questions, and an actual
approved placement/routing task. No model is qualified by this patch. Further
inference requires separate authorization and a prospectively declared protocol;
unused attempt slots from the completed screen are not retry permission.
