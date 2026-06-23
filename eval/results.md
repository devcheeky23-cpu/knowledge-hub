# Golden-set eval results (#11)

- Method: **manual evaluation against the live Hugging Face Space** (deployed Knowledge Hub).
- Date: 2026-06-23
- Questions: 18  ·  Categories: 11 answerable / 4 out-of-scope (abstain) / 3 conflict
- **Pass: 18/18 = 100%** (threshold 75%) — every question returned the expected mode, the expected citation(s), and an answer matching the expected answer.

Each question below was asked on the live Space chat page; the system response was compared to its expected answer/mode/citation and marked pass/fail by the project owner.

| id | cat | question | expected mode | expected answer | result | Pass? |
|----|-----|----------|---------------|-----------------|--------|-------|
| A1 | answ | Which HTTP header carries the authentication token? | found | The bearer token is sent in the Authorization header. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A2 | answ | How long are access tokens valid before they expire? | found | Access tokens are valid for 24 hours; after that the client must log in again. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A3 | answ | Does ShopFlow issue refresh tokens? | found | No. ShopFlow does not currently issue refresh tokens; clients re-login after expiry. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A4 | answ | How long is a password reset link valid, and how many times can it be used? | found | The reset link is valid for one hour and can be used only once. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A5 | answ | What HTTP status does POST /cart/items return when the requested quantity exceeds available inventory? | found | It responds 409. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A6 | answ | Under which order statuses can an order be cancelled? | found | Only orders in pending or paid status can be cancelled; a shipped order cannot be cancelled (responds 409) and must be returned instead. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A7 | answ | What are the possible statuses an order can have? | found | pending, paid, shipped, delivered, or cancelled. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A8 | answ | How long are inactive carts kept before being cleared? | found | Carts are persisted for 30 days of inactivity before being cleared. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A9 | answ | Once a refund is approved, how long does it take to appear? | found | Typically 5 to 7 business days, depending on the card issuer. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A10 | answ | What is the default and maximum page_size when listing products? | found | Default page_size is 20 and the maximum is 100. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| A11 | answ | What happens to the cart if payment fails during checkout? | found | If payment fails the order is not created and the cart is preserved (the API responds 402 on payment capture failure). | mode ✅ · citation ✅ · answer matches expected | ✅ |
| O1 | out_ | What is ShopFlow's monthly subscription pricing? | abstain | Abstain — the documents do not contain subscription pricing. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| O2 | out_ | Which programming language and framework is the ShopFlow backend built with? | abstain | Abstain — the documents do not state the backend language or framework. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| O3 | out_ | What is ShopFlow's customer support phone number? | abstain | Abstain — no support phone number appears in the documents. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| O4 | out_ | What is ShopFlow's uptime or availability SLA? | abstain | Abstain — the documents do not mention an uptime or availability SLA. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| C1 | conf | What is the return window for getting a refund? | conflict | Conflict — the 2022 refund policy says 14 days from delivery, while the 2024 refund policy says 30 days. Both should be reported without choosing a side. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| C2 | conf | How many days after delivery do I have to return an item for a refund? | conflict | Conflict — 14 days per the 2022 policy versus 30 days per the 2024 policy. | mode ✅ · citation ✅ · answer matches expected | ✅ |
| C3 | conf | Can I return an item 20 days after delivery for a refund? | conflict | Conflict — the 2022 policy says no (past the 14-day window), but the 2024 policy says yes (within 30 days). Both should be reported. | mode ✅ · citation ✅ · answer matches expected | ✅ |

## Notes

- Answerable (A1–A11): each returned `found` with a citation to the correct source document.
- Out-of-scope (O1–O4): each returned `abstain` with no citations and no hallucinated content.
- Conflict (C1–C3): each returned `conflict`, reporting both the 2022 (14-day) and 2024 (30-day) refund policies without choosing a side.