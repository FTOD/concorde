# Decision log: per-worker-models

Goal: Let the worker model configuration choose the backend, model and thinking level of each individual worker, not only of each worker role: a worker number (its position among an Operation's workers of one role, from 1) is the most specific level, so spec_panel's reviewers can each run on a different model; configure_workers sets it and reports it, and each worker's evidence names what it used

## Closed: merged, 2026-09-27T04:44:44Z
