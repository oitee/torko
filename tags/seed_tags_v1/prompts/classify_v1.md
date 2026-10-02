# Seed tag classification spec (v1)

## What this is

Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. The official website sansad.in attaches keyword tags to each debate. This task labels those tags, so that Torko can use them as the first tag vocabulary.

Each input line is one sansad.in tag and the number of debates that carry it. Nothing else is known about the tag.

## The job

Give each tag four values: a type, a domain, a one-line description, and a note when the tag is a near-duplicate of another tag.

## Types

Use exactly one of these words.

| Type | Meaning | Example |
|---|---|---|
| `topic` | A subject of debate. The largest group. | `Air Pollution`, `Unemployment` |
| `law` | A named act, bill, code, or constitutional provision. | `Right to Information Act`, `Article 370` |
| `person` | One named human, and nothing else. A job title is not a person. | `Mahatma Gandhi` |
| `role` | One office that one human holds at a time. | `Prime Minister`, `Chief Justice` |
| `group` | A class of many humans with a shared property. | `Farmers`, `Refugees`, `Judges` |
| `place` | A named geographic place. A state, a district, a city, a river, or a region. | `Assam`, `Ganga` |
| `institution` | A named body or organisation. A ministry, a court, a public company, a commission, or a board. | `ICCR`, `Supreme Court`, `Air India` |
| `scheme` | A named government scheme, programme, mission, fund, or a named policy. | `MGNREGA`, `National Education Policy` |
| `junk` | The tag is not usable. It is a typing error, it is empty of meaning, or it is pure parliamentary procedure. | `Oil Polilitcs`, `Quorum`, `Technical Information` |

### Place subtypes

Every `place` tag also carries a subtype. The subtype separates real geography from a general kind of area. Only the real geography group may drive a map, a state filter, or a parent-child expansion.

Real geography: `country`, `state`, `union_territory`, `city`, `region`, `river`, `landmark` (one named structure or site), `boundary`.

Not real geography: `area_type` (an area named by a property, for example `Drought Prone Areas`), `facility` (a class of built places, for example `Railway Station`), `place_class` (a class of units, for example `Districts`).

Rules:
- A general subject is `topic`. A named thing is `law`, `person`, `place`, `institution`, or `scheme`.
- `Railway Projects` is a `topic`. `Konkan Railway` is an `institution`.
- `Education Policy` as a general subject is a `topic`. `National Education Policy 2020` is a `scheme`.
- A tag with a spelling error that is still readable is not junk. Keep the type, and write the correct spelling in the description.

## Domains

Give each tag one domain from this list. The list follows the Union ministries. Use `-` for the types `person` and `junk`, and for a `place` with no clear subject.

```
Agriculture and Farmers
Food and Public Distribution
Rural Development
Urban Development and Housing
Water and Drinking Water
Environment, Forests and Climate
Energy
Railways
Roads and Highways
Civil Aviation and Shipping
Health and Family Welfare
Education
Labour and Employment
Social Justice and Reservation
Tribal Affairs
Women and Children
Economy, Finance and Taxation
Industry, Trade and Commerce
Science, Technology and Telecom
Defence
Home Affairs and Law and Order
Law, Justice and Constitution
Elections and Governance
Parliament and Procedure
External Affairs
Disasters and Relief
Culture, Tourism and Sports
Media and Broadcasting
```

Write the domain exactly as it appears above. Do not invent a new domain.

## Description

One line. Below 20 words. It says what the tag means to a reader who knows nothing about India or about parliament. This text becomes an embedding later, so it must carry meaning, not repeat the tag name.

Bad: `Farmers' Welfare - about farmers welfare.`
Good: `Government support for farmers, including income support, loan relief, and crop insurance.`

## Output format

One output line for each input line, in the same order. Tab separated, five fields, no header:

```
tag<TAB>type<TAB>domain<TAB>description<TAB>duplicate_of
```

- `tag` is copied from the input, character for character.
- `duplicate_of` holds another tag name when this tag means the same thing as that tag, for example `Compensations` is a duplicate of `Compensation`. Write `-` when there is no duplicate. This field is only a hint for a later step. Only use a tag name that you can see in your own chunk.
- No tab character inside a description. No empty field. Use `-` when a value does not apply.

## Rules

- Never guess a fact about India that you do not know. When the meaning of a tag is unclear, use the type `topic`, the best domain, and say in the description that the meaning is unclear.
- Write in simple English. Short sentences. Active voice. No semicolons.
