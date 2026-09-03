# Quickstart: scaffold and publish a project docsite

```bash
# 1. In an initialized project (after concorde-init has applied Initialization Proposal 3)
python3 .concorde/framework/scripts/concorde.py --project-root . docsite --propose \
  --title "Atlas" --repository https://github.com/org/atlas > .concorde/docsite-proposal.json
# review files, digests, conflicts, and prerequisites, then
python3 .concorde/framework/scripts/concorde.py --project-root . docsite \
  --apply --proposal .concorde/docsite-proposal.json

# 2. Publish
cd docsite && npm ci && npm run check
```

From the Concorde checkout use `python3 scripts/concorde.py` instead of the framework path. Add
`--github-pages` to include `.github/workflows/deploy-docsite.yml`.

Evidence commands used by this attempt:

```bash
.venv/bin/python -m unittest discover -s tests/concorde -t . -p 'test_*.py'
python3 scripts/concorde.py --project-root . validate --format json
cd docsite && npm run check
python3 scripts/development/sync-agent-surfaces.py status --format json
```
