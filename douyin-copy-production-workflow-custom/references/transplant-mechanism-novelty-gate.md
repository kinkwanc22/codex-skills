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

## Mother-Topic-Native Blueprint Gate

Apply this gate to every Gary transplant mode before freezing a rebuilt source. Route novelty never outranks topic fidelity.

1. **Title-hidden test:** hide the source title and infer the most natural title from the proposed thesis and point list alone. The inferred title must express the same mother topic, audience question, and promised result. A more accurate alternate title means the proposal is another article.
2. **Direct-answer test:** every public point must answer the source mother topic in its original sense without needing a newly invented umbrella theory to connect it back.
3. **Promise-delivery test:** every point must move the same target reader toward the same result. Shared keywords or a nearby relationship example are insufficient.
4. **No-new-umbrella test:** reject any abstract framework, metaphor, discipline, or knowledge-card concept that explains the planned body more accurately than the locked mother topic.
5. **Causal-mapping test:** when the mother topic joins two domains, the same causal rule must operate in both. One example from each domain does not pass when the examples merely decorate an unrelated theory.
6. **Expansion-capacity test:** before Gemini, every planned point must have enough native material to expand without filler: one judgment, one mechanism, one concrete scene or observable signal, one position/interest movement, and one consequence. Add a second-domain scene when the mother topic explicitly promises two domains.

Reject the complete proposal when any public point fails. Do not patch a drifting point with vocabulary from the title. Record the failed route and design or select a new one within the mode's allowed content source.

Candidate generation depends on mode:

- In Codex-designed modes such as 3.3 and 3.5, create three materially different topic-native candidate routes before selecting the frozen route. This is a local Codex design pass and must not call Gemini. Compare their dominant causal claims rather than producing three cosmetic label variants.
- In knowledge-closed 3.1, generate alternatives only from traceable eligible knowledge; do not invent a Codex route to satisfy the count.
- In limited-inheritance 2.5-transplant and 3.2, candidate routes must stay inside their preservation/inheritance contracts. Do not use this gate to authorize complete replacement.

After Gemini returns, repeat the title-hidden, direct-answer, no-new-umbrella, and causal-mapping tests on the accepted body. If the natural title has changed, an internal mechanism has become the real article, or examples have become decorative, reject the body. Change the frozen-source design and rerun only with user authorization; do not cosmetically patch the final manuscript.

## Comparison Window

Before knowledge selection or independent route design, load:

- the latest 10 usable records from the active mode;
- the latest 10 usable 3.1 and 3.2 records when either of those modes is involved;
- every usable record for the same source or same public mother topic that is available in the current ledger/history.

`usable` includes `generated / 正文待确认`, `accepted*`, and user-confirmed records. Do not wait for publication or final approval before excluding a route already generated in the current batch. Rejected records exclude only their failed route when the rejection reason identifies that route; they do not blacklist an entire knowledge family.

### 3.5 override: complete route exclusion, all statuses

For 3.5 only, ignore the ordinary recent/usable window for historical 3.1. Load every discoverable 3.1 route and artifact across all statuses and production stages, including rejected, abandoned, failed, retry, proposed, and unfinished work. Also encode every substantive source-body public viewpoint and dominant mechanism route as exclusion records. Source and historical public skeletons are forbidden in 3.5; the only inherited elements are the public topic and its promise boundary, audience, result, attack direction, and force band. Familiar foundational concepts may remain as secondary explanation when they do not become a numbered point, dominant bridge, or substantial reproduction of an earlier passage.

Use `--recent 0 --all-statuses` and pass the source record through `--exclusion-record`. Use `--strict-zero-overlap` only when the active 3.5 task explicitly requires literal exclusion of every concept. The deterministic result is only a lexical/concept-field screen. Codex must separately compare each proposed public point, dominant bridge, rationale, and conclusion. A collision in the public skeleton or dominant causal machinery rejects the whole proposal; a collision limited to a familiar supporting concept is recorded for final whole-document review.

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
    "candidate_route_count": 3,
    "title_hidden_inference": "<natural title inferred without source title>",
    "mother_topic_native_pass": true,
    "no_new_umbrella_pass": true,
    "expansion_capacity_pass": true,
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
5. After Gemini returns, repeat the Mother-Topic-Native Blueprint Gate on the complete body and audit for causal-route drift. If Gemini changes the natural title, promotes a supporting concept into a new umbrella, makes cross-domain examples decorative, or collapses distinct frozen points back into one saturated chain, repair the frozen source and rerun the complete isolated request only with user authorization; do not patch the final body into artificial variety.

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

No transplant draft enters Word export unless `mechanism_novelty_pass: true`, `mother_topic_native_pass: true`, `no_new_umbrella_pass: true`, and `expansion_capacity_pass: true` are present and the current draft has already been added to the comparison history for the next article. Exact-text dedupe remains a secondary final check; it cannot substitute for this mechanism-level and mother-topic-native gate.
