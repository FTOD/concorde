# Quickstart: Validate Release Publication

Prerequisites: Python 3.11, `uv`, `uv sync` done, `gh` authenticated (only for the live checks),
and a clean `git status`. Paths are repository-relative.

## 1. Unit and contract evidence (no network)

```bash
uv run python -m unittest discover -s tests/concorde/unit -p 'test_publish_release.py' -v
uv run python -m unittest discover -s tests/concorde/contract -p 'test_release*.py' -v
```

Expected: all pass. Covers version-authority checks, FTOD URLs, `release.json` schema/example
conformance, and the publisher's new / identical / divergent / mismatch / partial decisions against
a fake `gh`.

## 2. Local build, verify, and dry-run plan

```bash
uv run python scripts/release/build-components.py --output dist
uv run python scripts/release/verify-release.py --dist dist \
  --expect-version "$(uv run python scripts/release/build-components.py --print-version)" \
  --expect-base-url https://github.com/FTOD/concorde/releases/download/v0.1.0
uv run python scripts/release/publish-release.py --dist dist --tag v0.1.0 --dry-run
```

Expected: verifier prints seven digests; publisher prints `"outcome": "dry-run"` with the ordered
plan (create draft → upload 7 assets → publish) and the rendered notes, and performs no `gh` call.
A deliberately wrong tag (`--tag v9.9.9`) must exit 1 with `version-mismatch`.

## 3. Workflow rehearsal (no publication)

Trigger `Publish Concorde release` via `workflow_dispatch` with `dry_run=true` on the GitHub Actions
page. Expected: the job runs tests, build, verify, and prints the same plan as step 2 in its summary;
no release is created.

## 4. Live publication

```bash
git tag v0.1.0 && git push origin v0.1.0
```

Expected within 15 minutes (SC-001): a published (non-draft) release `v0.1.0` with exactly seven
assets and notes listing `concorde-core@0.1.0`, `concorde@0.1.0`, and `>=0.16.4,<0.16.5`.

## 5. Consumer check from a clean project (SC-003)

On a machine or directory without the Concorde checkout:

```bash
target="$(mktemp -d)" && cd "$target"
uvx --from specify-cli==0.16.4 specify init --here --integration claude --ignore-agent-tools
base=https://github.com/FTOD/concorde/releases/download/v0.1.0
uvx --from specify-cli==0.16.4 specify extension catalog add "$base/extensions.json" --name concorde --install-allowed
uvx --from specify-cli==0.16.4 specify preset catalog add "$base/presets.json" --name concorde --install-allowed
uvx --from specify-cli==0.16.4 specify bundle catalog add "$base/bundles.json" --id concorde
uvx --from specify-cli==0.16.4 specify bundle info concorde-bundle --json
```

Expected: the preview names `concorde-core` and `concorde` at `0.1.0` with matching digests, in under
2 minutes, with no local server.

## 6. Current-release pointer (FR-007)

```bash
curl -fsSL https://github.com/FTOD/concorde/releases/latest/download/release.json
```

Expected: `"version": "0.1.0"` and three catalog URLs under the `v0.1.0` base. After a later
`v0.2.0` publishes, the same command returns `0.2.0` while `…/download/v0.1.0/…` content is unchanged.

## 7. Idempotence and divergence (FR-006)

- Re-run the workflow for the same tag (`workflow_dispatch`, `dry_run=false`, same ref): expected
  `already-published` no-op, exit 0, no asset changes.
- In a scratch clone, change one allowlisted preset file, rebuild, and run the publisher against
  `v0.1.0` with `--dry-run` off but `--compare-only`: expected exit 2 `divergent`, naming the asset
  whose digest differs, and no mutation.
