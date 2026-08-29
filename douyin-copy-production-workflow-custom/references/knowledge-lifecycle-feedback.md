# Gary Knowledge Lifecycle Feedback

Read this file when a Gary draft uses the Obsidian knowledge base, when the user asks to strengthen the knowledge base, or when publication data must feed future retrieval.

## Shared Work ID

Every independently publishable Gary draft must have one stable `work_id` that connects:

- body-derived mother-topic anchor;
- source and version;
- target account;
- actually adopted B/X/atomic/case knowledge IDs;
- route signature;
- actually adopted opening source, broad category, and micro-framework;
- generated, workflow-accepted, user-confirmed, published, and data-reviewed events;
- publication snapshots and audit state.

Create a new ID for a new cycle manuscript under the same mother topic. Keep the same ID when the same manuscript is revised or moves through later states.

## Draft Registration

After a generated or accepted 3.1/3.2 body has its final provenance, run:

`/Users/kin/Documents/Codex/2026-07-10/qu/scripts/register_draft_and_iterate.py`

Pass the known `work_id`, account, exact source-body mother-topic anchor, route signature, confirmed knowledge IDs, and actual opening framework. Never promote automatically detected candidates into confirmed-use fields.

The first registration may let the script generate a `GARY-...` work ID. Preserve that returned ID for all later state and performance events.

## Publication Data

When the user supplies or authorizes collection of publication data, run:

`/Users/kin/Documents/Codex/2026-07-10/qu/scripts/record_publish_performance.py`

Use the exact work ID. Record raw counts and snapshot time; derive rates from views. Keep multiple snapshots rather than overwriting earlier observations. Do not mark a draft published or data-reviewed without direct evidence.

## Retrieval Feedback

Publication data is a tie-breaker inside topic-compatible retrieval, not permission to change the mother topic or copy a prior route.

1. Filter by exact mother topic, account, force band, relationship stage, and promised result.
2. Exclude same-source routes and recent saturation.
3. Among remaining compatible candidates, use prior account data as supporting evidence.
4. Consider playback, likes, favorites, follows, group joins, audit state, posting time, and paid-traffic context separately.
5. Fewer than three comparable uses means only `positive_record` or `negative_record`, never a stable rule.
6. A high-performing combination does not prove that one knowledge point or hook caused the result.

## Pre-Knowledge-Base Historical Works

For Gary works published before stable knowledge IDs existed, store them in the separate historical performance evidence ledger before exposing them to retrieval:

- `/Users/kin/Gary 男性情感/Gary 男性情感/05_复盘与自生长/02_发布数据/历史作品效果证据.jsonl`

Each historical record must keep the published title, exact source-body mother-topic anchor, account, publication date, upstream-source evidence grade, raw backend counts, and any title/source count or perspective conflict. Leave `knowledge_ids` empty and use a legacy route-unknown signature; never reverse-assign current B/X knowledge, routes, or opening categories to an old work.

The source opening is not automatically the verified published opening. Unless the actual published body or video has been checked, keep opening attribution disabled. Historical follower rate remains follower rate; leave group joins null unless a work-specific source marker proves them.

`build_knowledge_call_pack.py` may return same-topic historical performance as a separate evidence block. Use it only after topic/account/force compatibility filtering and only as a candidate-ordering signal. Do not merge its score into the textual relevance score of B/X knowledge cards and do not describe it as causal proof.

## Opening Feedback

Register the opening actually used in the published video, not every Word candidate. Track both broad category and micro-framework. For repeated mother topics, rotate micro-frameworks before recycling surface wording. Keep the opening's promise, count, force, and mechanism aligned with the accepted body.
