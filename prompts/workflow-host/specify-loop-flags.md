---
audience: ambient
---

Optional `specify` (default true) and `run_reviews` (default true) select authoring and Spec review.
`specify:false` reviews the existing Spec without authoring. `run_reviews:false` records an explicit
Spec review skip unless that review was already required for this change. A later request cannot
cancel a recorded requirement. This loop does not require or skip code review.
