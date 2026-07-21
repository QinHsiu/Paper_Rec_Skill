# Screening stop rule (asreview-inspired)

When doing lit screening / mark-reading over a large ranked list:

- Track consecutive **irrelevant** (skip / not useful) judgments.
- Stop suggesting more when **N consecutive irrelevant** (default **N=10**) unless user forces continue.
- Record `stopped_reason: n_consecutive_irrelevant` in query-trace / thread events.

Does not replace RRF Top-50; applies to interactive screening after Top-N.
