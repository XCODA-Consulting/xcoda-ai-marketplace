# Worked Example: Webhook Retry Delivery

Two source materials, neither a formal PRD: a design-brainstorm doc and a customer escalation
thread. This shows the methodology on genuinely mixed, informal sources — the common case, not
the exception.

## Sources (as given to the skill)

**S1 — `brainstorm-retry-delivery.md`** (internal doc, informal):
> "...if a webhook delivery fails we should probably just retry it a few times. Exponential
> backoff seems reasonable. Need to think about what happens if the receiver processes the
> first attempt but the ack gets lost — don't want them getting charged twice or whatever the
> side effect is."

**S2 — customer escalation thread** (support ticket, verbatim quote):
> "We got the same order-confirmation webhook 4 times in one hour after a network blip on our
> side. Our system doesn't dedupe, so we ended up creating 4 shipping labels for one order.
> If retries are going to happen, there needs to be a way for us to tell it's the same event."

## Resulting DoD (abridged)

```markdown
# Webhook Retry Delivery — Definition of Done

## 1. Summary
Failed webhook deliveries are automatically retried with exponential backoff, and every
delivery — original or retry — carries a stable identifier so receivers can detect and
ignore duplicates. This is the full ask; no follow-on slice is anticipated.

## 2. Why this matters
A production customer lost money (four duplicate shipping labels) because retried webhook
deliveries were indistinguishable from the original. Without idempotency, "just retry on
failure" makes reliability worse for receivers who don't already dedupe.

## 3. Source material
- `brainstorm-retry-delivery.md` — internal design brainstorm; read in full, it names the
  backoff approach and flags (without resolving) the duplicate-delivery risk.
- Customer escalation thread (ticket #4821) — read in full; this is the actual triggering
  incident and the real requirement source for idempotency.

## 4. Design context — read before designing

### Delivery identity must survive retries
S1 flags the duplicate-side-effect risk but doesn't resolve it. S2 makes it concrete: "there
needs to be a way for us to tell it's the same event."

**Design implication:** every delivery attempt for the same logical event carries the same
caller-visible event ID, and that ID must be stable across retries — not regenerated per
attempt. The event ID is part of the payload contract, not just an internal retry-tracking
field.

### Retries must not amplify load indiscriminately
S1: "exponential backoff seems reasonable" — a stated preference, not a spec.

**Design implication:** backoff must be exponential with jitter and a hard cap on total
attempts; a receiver that's down for an extended window should stop receiving retries rather
than accumulate an unbounded queue.

## 5. Persona
- **Receiver integrator**: the engineer on the customer side implementing the webhook
  consumer; needs a documented, stable way to detect duplicates.

## 6. Preconditions
- The webhook delivery system already tracks delivery attempts (attempt count, timestamp)
  for observability — this feature extends that record, not replaces it.

## 7. User acceptance criteria

### Duplicate detection

#### Retried deliveries carry the same event ID as the original
GIVEN a webhook delivery fails and is retried
WHEN the receiver inspects the retried payload
THEN the event ID matches the original attempt's event ID exactly

**Source:** Customer escalation thread (ticket #4821) — "there needs to be a way for us to
tell it's the same event."

### Backoff behavior

#### Failed deliveries retry with exponential backoff up to a capped attempt count
GIVEN a webhook delivery attempt fails
WHEN the system schedules a retry
THEN the delay follows exponential backoff with jitter, and retries stop after the
configured maximum attempt count

**Derived from:** `brainstorm-retry-delivery.md` — "exponential backoff seems reasonable"
(a stated preference, not itself a requirement someone asked for — hence Derived from, not
Source).

## 8. Design seams / forward-compatibility
- Expose the max-attempts and backoff-curve parameters as configuration, not constants — S1's
  "seems reasonable" reads as a starting guess, not a validated number; expect it to be tuned
  post-launch without a code change.

## 9. Out of scope
- A receiver-facing dashboard for delivery status — not requested by either source; deferred
  until there's a concrete ask for it.

## 10. Known unknowns
- No formal SLA exists yet for "how long is too long to keep retrying" — the max-attempts
  value in this DoD is a starting assumption (S1's "seems reasonable"), not a validated
  target. Flag for revisit once retry telemetry exists.
```

Notice what each provenance label is doing: the *existence* of retries and backoff is only
`Derived from:` S1 (a brainstorm, not a request); the *idempotency requirement* is `Source:`
S2 because that's the thread that actually asked for it. Swapping those — citing S1 as the
Source for idempotency because it "mentioned" the duplicate-side-effect risk — would overstate
provenance: S1 flagged a concern, S2 is what actually demanded a fix.
