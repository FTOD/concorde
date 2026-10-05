# Sentence style

This is the sentence part of [Spec writing guidelines](writing.md). [Writing guidance](module.md)
says what a Spec must communicate. This chapter says how its sentences are written. It applies to
the reading of every document and to every concept definition in the glossary.

The rules are inspired by the structural rules of ASD-STE100 Simplified Technical English. The
Protocol adopts only those structural rules, stated here in its own words. It does not adopt the
STE dictionary or the STE rules for modal verbs.

This chapter serves understanding. A short sentence that carries one fact is read correctly on the
first pass. This is true for a person and for a model. A requirement that names its actor and
carries one obligation tells each task what it must do.

The rules never change what a text means. A rewrite in this style keeps every fact, every
condition and every link between facts. When a rule would change the meaning of a sentence, keep
the meaning and break the rule.

## The rules

### One fact in each sentence

Write one fact, one step or one requirement in each sentence. A normative sentence carries one
obligation, so it contains one of the [requirement keywords](#requirement-keywords) at most. When a
statement has two obligations, write two sentences.

The conditions, exceptions and failures of one obligation are part of that one fact. They stay in
its sentence, as [Requirements](#requirements) says.

### Short sentences

A descriptive sentence SHOULD have 25 words or fewer. Split a longer sentence into two sentences,
or move its details into a list. Count every word of a link's text. Count an inline code span as
one word. `CHK.style.sentence-length` reports a sentence of more than 35 words.

Shorten a sentence only by its form, never by its meaning. Keep the words that carry meaning, as
[The links between facts](#the-links-between-facts) says.

A concept definition is one sentence that must identify its term. It can need more words than a
sentence of a reading. Keep it as short as identifying its term allows, and move every other detail
into the term's explanation. `CHK.style.sentence-length` reports a concept definition of more than
50 words.

The statement of a requirement has no length bound. It keeps its one obligation whole, with every
condition, exception and failure, as [Requirements](#requirements) says.
`CHK.style.sentence-length` does not measure it.

### Lists for three or more

When a sentence would name three or more conditions, cases, steps or items, write a vertical list.
Introduce the list with a short sentence that ends with a colon. Give each item one fact. Write the
items in the same grammatical form, all sentences or all phrases.

A requirement can use a list too. Its first paragraph states the obligation once and ends with a
colon. The list below it gives the conditions of that one obligation, never new obligations:

```markdown
### req.checkout.refuse-stale — Refuse a stale cart

Checkout SHALL refuse the submission when any of these conditions is true:

- The cart changed after the price was shown.
- An item in the cart is no longer sold.
- The delivery address is outside every delivery zone.
```

### The condition before the statement

Put a condition before the statement it limits, so that the reader knows the situation before the
rule. Write "When the lock is busy, the store SHALL refuse the write." Do not write "The store
refuses the write if the lock is busy and no merge runs, unless the caller waits."

A condition stays next to what it limits. When it limits only a part of a sentence, such as an
action that a guidance tells its reader to take, it stays with that part. See
[Requirements](#requirements).

### The links between facts

Keep the words that link facts or limit them. These words carry meaning:

- Causes and purposes, such as "since", "because", "so" and "so that".
- Limits, such as "only", "each", "every", "never" and "at most".
- Conditions and exceptions, such as "when", "unless", "until" and "except".

Do not drop such a word to shorten a sentence. When you split a sentence, carry the link into the
new sentence. Write "The host removes the directory when the run ends. It does this so that no
credential outlives the run." Do not drop the second sentence, because it says why the rule
exists.

### No semicolons

Do not use a semicolon in prose. Write two sentences, or write a list. A semicolon in an inline
code span or a code block is not prose. `CHK.style.semicolon` reports a semicolon in prose.

### The actor and the active voice

A requirement names the Module, component or person that acts, and uses the active voice. Write
"The host SHALL delete the file." Do not write "The file is deleted." Use the passive voice only
when the actor does not matter to the reader, as in "The file is created at install."

The subject of an obligation is the party that bears it. A rewrite keeps that party as the subject.
It never introduces an actor that the original text did not name. When a requirement names no
actor, the choice of an actor changes its promise. That choice is a change of the Spec, not of its
style.

### Requirements

The statement of a requirement is one sentence with one obligation. Its conditions, exceptions and
failures belong to that obligation, so they stay in the same sentence. Never split one obligation
into separate rules to make its sentences shorter. A requirement keeps this sentence whatever its
length.

Three or more conditions can stand in a list below the statement, as
[Lists for three or more](#lists-for-three-or-more) shows. The statement ends with a colon, and
each item is a condition of the one obligation. An item is never an obligation of its own.

Write this:

```markdown
### req.runner.remove-checkout — Remove the checkout after each run

The runner SHALL remove the checkout of each run when the run ends, also when the run failed, so
that no later run finds a stale checkout.
```

Do not write this, because the list turns one obligation into separate rules and drops its purpose:

```markdown
### req.runner.remove-checkout — Remove the checkout after each run

The runner SHALL follow these rules for the checkout:

- Remove the checkout when the run ends.
- Remove the checkout when the run failed.
```

Each condition stays next to what it limits:

- A condition of the whole obligation comes before the subject.
- A condition of one part, such as one action or one object, stays next to that part.

Write "The guidance SHALL tell the main agent to merge a task only after its delivery." Do not
write "Only after its delivery, the guidance SHALL tell the main agent to merge a task." The
delivery limits the merge, not what the guidance says.

Keep the subject that bears the obligation. Write "The guidance SHALL tell each task session to
stay inside its worktree." Do not change it to "Each task session SHALL stay inside its worktree."
That sentence gives the obligation to another party.

### Simple tenses

Use the simple present for what is true and for what a component does. Use the simple past for
what happened before, and the simple future only when the order in time matters. Avoid
progressive and perfect forms when a simple form says the same.

### One word for one meaning

The project glossary is the controlled vocabulary of the Specs. Use a defined term only with the
meaning its definition gives. Do not use a synonym for a defined term. Do not use the word of a
term in another sense. A word that the glossary does not define keeps its ordinary meaning. See
[Terms](module.md#terms).

### Requirement keywords

The requirement keywords `MUST`, `MUST NOT`, `SHALL`, `SHALL NOT`, `SHOULD` and `MAY` keep the
meanings that the Protocol gives them. They are not the modal verbs that STE restricts. A rule of
STE that forbids "should" or "may" does not apply to a Spec. `CHK.style.one-obligation` reports a
sentence that contains more than one of these keywords in capital letters. A keyword with its NOT
is one keyword.

## What a program measures

The three style checks of [Checks](checks.md#style) have strictness warning. They measure the prose
of the reading as a reader sees it:

- Fences, headings, tables, front matter, comments and HTML anchors are not prose.
- A link counts as its text. An inline code span counts as one word.
- Each paragraph and each list item is split into sentences by the sentence-break rule of
  `CHK.concept.definition`.

A concept definition is one sentence, so the checks measure it as one sentence. Its length bound is
50 words instead of 35.

The statement of a requirement is the first sentence of the paragraph that follows the
requirement's heading, as `CHK.requirement.statement` reads it. `CHK.style.sentence-length` does
not measure it. `CHK.style.semicolon` and `CHK.style.one-obligation` measure it as any other
sentence.

The other rules need a reader's judgment. A review judges them as part of readability, by the
criteria of [Evaluating a Spec](evaluation.md#readability). A text with no style warning can still
break a rule. A sentence of 30 words passes the check and is still longer than the target.
