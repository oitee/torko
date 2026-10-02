# Seed tag merge spec (v1)

## What this is

Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. The official website sansad.in attaches keyword tags to each debate. A first pass gave each tag a type, a domain, and a one-line description. See `classify_v1.md` in this same folder for those definitions.

This second pass removes the near-duplicates. The same idea appears in the tag list under many names, for example `Compensation` and `Compensations`, or `Road Construction` and `Road Development`.

## Input

Your task names one input file. Each line holds five fields, separated by tab characters:

```
tag<TAB>debate_count<TAB>domain<TAB>description<TAB>duplicate_hint
```

`debate_count` is the number of debates that carry the tag. `duplicate_hint` is a guess from the first pass. The hint is often wrong. Check it. Do not trust it.

## The job

Put the tags into groups. One group holds all the tags that mean the same thing. Most groups hold exactly one tag.

For each group:
1. **Choose the canonical name.** Prefer the correct spelling. Prefer the name with the highest debate count when both spellings are correct. Prefer the singular form for a general subject.
2. **Make every other name in the group an alias.**
3. **Write one description for the group.** Below 20 words. It explains the meaning to a reader who knows nothing about India or about parliament.

## What is the same thing, and what is not

Merge:
- A spelling error and its correct form. `Propoganda` and `Propaganda`.
- A singular and a plural. `Compensation` and `Compensations`.
- A short form and a long form of one name. `BALCO` and `Bharat Aluminium Co. Ltd (BALCO)`.
- Two names for one idea. `Price Rise` and `Inflation`.

Do not merge:
- A parent and a child. `Education` and `Higher Education` are different tags. A later step builds the hierarchy.
- Two related but different subjects. `Road Construction` is building a new road. `Road Maintenance` is repair work.
- Two different bodies with similar names.

When you are unsure, do not merge. A wrong merge hides speeches from a user. A missed merge only leaves two tags where one is enough.

## Type and domain

Keep the type and the domain from the input, with one exception. Change a value when it is clearly wrong, for example a named act that carries the type `topic`. Report every change that you make.

## Output format

Write one line for each group. Tab separated, six fields, no header:

```
canonical_tag<TAB>type<TAB>domain<TAB>description<TAB>aliases<TAB>total_debate_count
```

- `aliases` holds the other names in the group, separated by the pipe character `|`. Write `-` when the group holds only one tag.
- `total_debate_count` is the sum of the debate counts of every tag in the group.
- No tab character inside any field. No empty field. Use `-` when a value does not apply.

Every input tag must appear exactly one time in the output, as a canonical name or as an alias.

## Rules

- Never guess a fact about India that you do not know. Leave the tag alone when you are unsure.
- Write in simple English. Short sentences. Active voice. No semicolons.
- Report: the number of input lines, the number of output lines, the number of merges, and every type or domain that you changed.
