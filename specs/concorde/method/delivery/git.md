# Delivery's Git procedures

The exact Git procedures of [Delivery](module.md)'s steps 8 to 10. The entry explains why Delivery
records the index, restores it and verifies the commit it names. This document gives the commands
and their order. Its [requirements](requirements.md) state what each procedure must achieve.

## Recording and restoring the index

Step 8 records the index with Git's own means rather than a copy Delivery would keep:

- `git write-tree` records the index's entries.
- `git ls-files` lists the paths. Those the tree lacks are intent-to-add entries a tree cannot hold.
- `git ls-files -v` shows the skip-worktree and assume-unchanged flags.

When step 9 fails, Delivery restores the recorded parts with these commands, in this order:

1. `git read-tree` restores the index's entries.
2. `git add -N` marks the intent-to-add entries again.
3. `git update-index` sets each kind of flag again.

Even when another restoration fails, Delivery attempts to restore the intent-to-add entries and
each kind of flag. When Git refuses to read the recorded tree back into the index, Delivery
attempts none of the later restorations. They apply only to an index that was read back.

## Identifying the commit

Step 10 verifies the commit that `git commit` names on its standard output as the one it created.
Once its post-commit hook runs, Git prints the commit it created. Git gives every hook's standard
output to its standard error. A post-commit hook that commits again on top therefore cannot change
what Git prints.

No other source would do:

- The branch head would name a commit a post-commit hook made on top.
- A repository may switch off its reflog, so the branch's reflog would not do.
- The first commit on top of the validated head would not do either.

A hook amending the commit replaces it, and Git names the replacement.
