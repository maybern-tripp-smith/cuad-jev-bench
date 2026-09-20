# PAIR_MANIFEST — cuad-jev-2026-09-20

**Frozen before any Jev call.** Seed `20260920`.

## Criterion (exact)

`more relevant to the requested contract category`

## Counts

| Set | n |
|-----|--:|
| Stratum A (certain, cross-contract unrelated) | 40 |
| Stratum B (BM25 hard-neg, same contract) | 200 |
| Candidate queries (Score top-10) | 100 |
| Unique text units | 1406 |

## Construction rules

### Stratum A
For category C (prefer non-meta categories), pair a CUAD gold span text against a
paragraph from a **different** contract that has **no** human annotation for C.
Length band ≈ 0.4–2.5× gold when available. Gold side is always `a`. Rule-built;
no human taste ranking among candidates beyond seeded RNG among rule-eligible set.

### Stratum B
For a gold span, BM25-rank paragraphs of the **same** contract with query =
span text + category + description; select the highest-scoring paragraph that
does not overlap the gold char span. Cap 200; diversify categories (≤12) and
contracts (≤4). Seed `20260920`.

### Candidate queries
Sample 100 (contract, category) pairs with ≥1 gold span and ≥5 paragraphs.
BM25 over paragraph chunks (~≤400 tok) with query = category + description;
take top-10. If no gold paragraph appears in top-10, inject one gold
paragraph (logged as `gold_injected`) so rank under Jev Score is measurable.
Injection is **not** counted as BM25 retrieval success.

## Category histograms

### A
{
  "Notice Period To Terminate Renewal": 3,
  "License Grant": 3,
  "Anti-Assignment": 3,
  "Non-Transferable License": 3,
  "Cap On Liability": 3,
  "Post-Termination Services": 3,
  "Governing Law": 3,
  "Renewal Term": 2,
  "Revenue/Profit Sharing": 2,
  "Rofr/Rofo/Rofn": 2,
  "Warranty Duration": 2,
  "Minimum Commitment": 2,
  "Audit Rights": 2,
  "Exclusivity": 2,
  "Insurance": 1,
  "Competitive Restriction Exception": 1,
  "Joint Ip Ownership": 1,
  "Affiliate License-Licensor": 1,
  "Irrevocable Or Perpetual License": 1
}

### B
{
  "License Grant": 12,
  "Parties": 12,
  "Cap On Liability": 12,
  "Insurance": 11,
  "Audit Rights": 11,
  "Minimum Commitment": 10,
  "Rofr/Rofo/Rofn": 10,
  "Non-Transferable License": 9,
  "Post-Termination Services": 9,
  "Ip Ownership Assignment": 9,
  "Change Of Control": 9,
  "Expiration Date": 8,
  "Warranty Duration": 8,
  "Governing Law": 8,
  "Exclusivity": 6,
  "Anti-Assignment": 6,
  "Affiliate License-Licensee": 5,
  "Uncapped Liability": 5,
  "Renewal Term": 5,
  "Revenue/Profit Sharing": 4,
  "Volume Restriction": 4,
  "Non-Compete": 3,
  "Document Name": 3,
  "Notice Period To Terminate Renewal": 3,
  "Termination For Convenience": 3,
  "Most Favored Nation": 2,
  "Irrevocable Or Perpetual License": 2,
  "Effective Date": 2,
  "No-Solicit Of Employees": 2,
  "Joint Ip Ownership": 2,
  "Competitive Restriction Exception": 1,
  "Agreement Date": 1,
  "Price Restrictions": 1,
  "No-Solicit Of Customers": 1,
  "Non-Disparagement": 1
}

### Queries
{
  "Expiration Date": 8,
  "Document Name": 8,
  "Parties": 7,
  "Cap On Liability": 7,
  "Audit Rights": 7,
  "Ip Ownership Assignment": 6,
  "Agreement Date": 5,
  "License Grant": 5,
  "Anti-Assignment": 5,
  "Exclusivity": 4,
  "Governing Law": 4,
  "Competitive Restriction Exception": 3,
  "Termination For Convenience": 3,
  "Non-Transferable License": 3,
  "Effective Date": 3,
  "Renewal Term": 3,
  "Covenant Not To Sue": 2,
  "Revenue/Profit Sharing": 2,
  "Minimum Commitment": 2,
  "Change Of Control": 2,
  "Volume Restriction": 1,
  "No-Solicit Of Customers": 1,
  "Rofr/Rofo/Rofn": 1,
  "Liquidated Damages": 1,
  "Insurance": 1,
  "No-Solicit Of Employees": 1,
  "Warranty Duration": 1,
  "Affiliate License-Licensee": 1,
  "Post-Termination Services": 1,
  "Uncapped Liability": 1,
  "Notice Period To Terminate Renewal": 1
}

## Files

- `data/pairs/gold_pairs.jsonl`
- `data/pairs/candidate_queries.jsonl`
- `data/pairs/units.jsonl`
- `data/pairs/PAIR_MANIFEST.md` (this file)
