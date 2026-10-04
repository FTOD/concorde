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

## The rules

### One fact in each sentence

Write one fact, one step or one requirement in each sentence. A normative sentence carries one
obligation, so it contains one of the [requirement keywords](#requirement-keywords) at most. When a
statement has two obligations, write two sentences.

### Short sentences

A descriptive sentence SHOULD have 25 words or fewer. Split a longer sentence into two sentences,
or move its details into a list. Count every word of a link's text. Count an inline code span as
one word. `CHK.style.sentence-length` reports a sentence of more than 35 words.

### Lists for three or more

When a sentence would name three or more conditions, cases, steps or items, write a vertical list.
Introduce the list with a short sentence that ends with a colon. Give each item one fact. Write the
items in the same grammatical form, all sentences or all phrases.

A requirement can use a list too. Its first paragraph states the obligation once and ends with a
colon. The list below it gives the conditions:

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

### No semicolons

Do not use a semicolon in prose. Write two sentences, or write a list. A semicolon in an inline
code span or a code block is not prose. `CHK.style.semicolon` reports a semicolon in prose.

### The actor and the active voice

A requirement names the Module, component or person that acts, and uses the active voice. Write
"The host SHALL delete the file." Do not write "The file is deleted." Use the passive voice only
when the actor does not matter to the reader, as in "The file is created at install."

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

A concept definition is one sentence, so the checks measure it as one sentence.

The other rules need a reader's judgment. A review judges them as part of readability, by the
criteria of [Evaluating a Spec](evaluation.md#readability). A text with no style warning can still
break a rule. A sentence of 30 words passes the check and is still longer than the target.
