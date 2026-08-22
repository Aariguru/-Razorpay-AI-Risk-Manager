# Bounded AI investigation workflow

## Workflow

```text
Risk assessment
    → collect read-only evidence
    → structured recommendation provider
    → investigation record
    → human analyst review
```

The investigation API is intentionally available only after a stored risk assessment exists. This ensures the agent starts with model explanations rather than generating unsupported risk claims.

## Approved evidence tools

The agent invokes a fixed allowlist of local, read-only tools:

1. Transaction context — safe transaction attributes only; no payment token or network hash is sent to the recommendation provider.
2. Stored risk assessment — score components, model version, feature values, and reasons.
3. Customer history — aggregate counts, known countries, and device count.
4. Device context — device transaction/customer counts and 24-hour activity.
5. Risk policy — score thresholds and the no-autonomous-action constraint.

The agent has no tool that can submit a payment, alter a transaction, block a customer, fetch internet data, or access Razorpay systems.

## Providers

- `mock` is deterministic and is the default. It makes the demo and tests work without credentials.
- `openai` is optional and requires `OPENAI_API_KEY` plus `AGENT_PROVIDER=openai` or an explicit request value. It uses the OpenAI Responses API with `store: false`, strict JSON-schema output, and a prompt that limits it to supplied evidence.

## Output contract

Every investigation stores and returns a recommendation (`allow`, `manual_review`, or `block`), confidence, concise summary, collected evidence, and explicit limitations. The output is decision support only; the Phase 4 review endpoint remains the human control point.
