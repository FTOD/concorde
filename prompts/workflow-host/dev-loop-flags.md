---
audience: ambient
---

Optional `specify` (default true) and `run_reviews` (default true) flags select the loop shape.
`specify:false` skips Spec authoring for this pass, exactly like the former fast loop.
`run_reviews:false` records an explicit skip for each review mode instead of running it. A review
requirement already recorded for this change cannot be disabled by a later `run_reviews:false`;
every skip and every required review remains visible in the change record.
