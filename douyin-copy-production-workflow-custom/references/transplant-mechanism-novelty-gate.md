# Transplant Mechanism Novelty Gate / 换芯机制级排重门

Read this file for every Gary transplant mode, including `2.5成稿换芯`, `3.1`, `3.5`, `3.2`, and `3.3`. Apply it before the rebuilt source is frozen and before any Gemini request. This gate changes selection and route design only; it must never be appended to, summarized inside, or used to replace the complete 2.5 expansion prompt.

## What Counts As A Collision

Different words, examples, knowledge IDs, or point order do not make a route new. Compare the actual causal machinery. Normalize every proposed article into these six fields:

1. `problem_trigger`: what starts the audience problem;
2. `core_mechanism`: the main psychological, interest, social, or behavioral mechanism;
3. `action_chain`: what the man actually does, in sequence;
4. `proof_operation`: what observable evidence, comparison, or case proves the judgment;
5. `position_or_interest_shift`: whose cost, choice, attention, risk, or relationship position changes;
6. `desired_result`: the concrete result promised by the route.

Reject the proposal before freezing when any of these is true:

- `core_mechanism + action_chain` repeats a recent route;
- four or more of the six fields materially match one recent route;
- the article again uses the same dominant generic chain, such as `停止讨好 -> 收回注意力 -> 制造损失感 -> 对方回头投入`, even though its nouns, examples, card IDs, or public point names differ;
- the majority of numbered points are different surface versions of the same mechanism, operation, proof, or result;
- novelty comes mainly from renaming, changing examples, moving paragraphs, adding terminology, or making the route safer and more abstract.

The public mother topic, promised count, attack direction, and topic-defining mechanisms remain locked. A necessary topic-defining mechanism may recur, but it may not automatically control the whole new article. Keep it as a limited support mechanism and change the supporting causal route, operation, proof, and consequence. Do not weaken the source merely to pass this gate.

## Comparison Window

Before knowledge selection or independent route design, load:

- the latest 10 usable records from the active mode;
- the latest 10 usable 3.1 and 3.2 records when either of those modes is involved;
- every usable record for the same source or same public mother topic that is available in the current ledger/history.

`usable` includes `generated / 正文待确认`, `accepted*`, and user-confirmed records. Do not wait for publication or final approval before excluding a route already generated in the current batch. Rejected records exclude only their failed route when the rejection reason identifies that route; they do not blacklist an entire knowledge family.

For a batch, refresh the comparison window after every accepted/generated draft. A three-article group may share tone, but it may not share one dominant causal chain.

## Required Pre-Freeze Record

Save this block beside the provenance/route record:

```json
{
  "mechanism_novelty": {
    "lookback_active_mode": 10,
    "lookback_cross_version": 10,
    "problem_trigger": "<trigger>",
    "core_mechanism": "<dominant mechanism>",
    "action_chain": ["<action 1>", "<action 2>", "<action 3>"],
    "proof_operation": ["<observable proof method>"],
    "position_or_interest_shift": "<who loses or gains what>",
    "desired_result": "<promised result>",
    "dominant_causal_chain": "<trigger -> mechanism -> action -> shift -> result>",
    "compared_route_ids": ["<recent route id>"],
    "collision_candidates": [],
    "rejected_alternatives": ["<candidate + reason>"],
    "mechanism_novelty_pass": true
  }
}
```

`route_signature` remains required, but it is only a label. Knowledge-ID uniqueness, phrase similarity, and a new title are insufficient without this six-field record.

## Selection And Retry Behavior

1. Run the gate before selecting the final knowledge combination or 3.3 route.
2. If it collides, reject that route and select different traceable modules/operations; do not send it to Gemini.
3. If the mother topic inherently requires one repeated mechanism, record the exception and change at least the action chain, proof operation, interest movement, and result path.
4. If no topic-native alternative can pass without changing the mother topic or inventing unsupported content, stop before freeze and report the missing route. Do not solve the problem by generic filler or safety language.
5. After Gemini returns, audit for causal-route drift. If Gemini collapses distinct frozen points back into one saturated chain, repair the frozen source and rerun the complete isolated request; do not patch the final body into artificial variety.

Run the deterministic screen after saving the proposed six-field record and before freezing:

```bash
python3 scripts/validate_transplant_mechanism_novelty.py \
  --proposal <proposed-route.json> \
  --ledger <active-ledger.json> \
  --ledger <cross-version-ledger.json> \
  --report-out <mechanism-novelty-report.json>
```

This screen catches recorded-field collisions; Codex must still perform the semantic comparison because synonyms can hide the same causal chain.

## Acceptance Rule

No transplant draft enters Word export unless `mechanism_novelty_pass: true` is present and the current draft has already been added to the comparison history for the next article. Exact-text dedupe remains a secondary final check; it cannot substitute for this mechanism-level gate.
