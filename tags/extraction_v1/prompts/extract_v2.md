You read one speech from a debate in the Lok Sabha, the lower house of the parliament of India. The speech can be in English, in Hindi, or in a mix of both.

The input has four parts. The `Member` line names the member who gives the speech. In this prompt, "the member" always means this person. The `Debate` line is the title of the debate. The `Date` line is the date. The text after `Speech:` is the speech.

The Debate line can be wrong. Use the speech text to decide what the speech is about.

Return a summary, a list of topics, and a list of other entities.

## Summary

One sentence, at most 30 words, in plain English. Say what the member raised, asked for, or argued. Do not say whether the member is right.

Start with a verb, for example "Asks", "Supports", "Opposes", "Criticises". Do not start with the name of the member, "The member", or "The speaker".

Example: "Asks for compensation for farmers in Vidarbha whose cotton crop failed after unseasonal rain."

## Topics

A topic is a subject or an issue that the speech is about, for example `Farmers' Suicide`, `Air Pollution`, `Arbitration`, `Rail connectivity`.

A topic is never a name. A named act, bill, article, scheme, mission, institution, place, or person goes in the list of other entities. The topic is the subject of that named thing. 

Examples:

| The speech is about | Topic | Other entity |
|---|---|---|
| The Waqf (Amendment) Bill, 2025 | `Waqf property management` | `Waqf (Amendment) Bill, 2025` (`law`) |
| The removal of Article 370 | `Special status of Jammu and Kashmir` | `Article 370` (`law`) |
| Chandrayaan-3 | `Lunar exploration` | `Chandrayaan-3` (`scheme`) |
| A new train to a town | `Rail connectivity` | the town (`place`) |

List at most 8 topics. Put the most important first. Every speech with a real subject has at least one topic. A speech that asks for a train to a town is about `Rail connectivity`. A speech on a bill about arbitration is about `Arbitration`.

## Other entities

An other entity is a named thing in the speech that a reader can search for. Use one of these types:

| type | Meaning | Example |
|---|---|---|
| `law` | A named act, bill, code, sanhita, or article of the Constitution. | `Right to Information Act`, `Article 370` |
| `scheme` | A named government scheme, programme, mission, or project. | `Pradhan Mantri Awaas Yojana`, `Chandrayaan-3` |
| `institution` | One named body or organisation. | `Election Commission`, `AIIMS` |
| `place` | A named place: a country, state, district, city, river, or region. | `Bundelkhand`, `Brahmaputra` |
| `person` | One named human. See the person test below. | `Mahatma Gandhi` |
| `group` | A class of many people. | `Fishermen`, `Scheduled Tribes`, `Companies` |
| `role` | One office that one person holds at a time. | `Governor` |

The type follows the name that you write:

- A name with "Act", "Bill", "Code", "Sanhita", or "Article" is a `law`.
- A name with "Yojana", "Scheme", "Mission", "Abhiyan", or "Programme" is a `scheme`.

Example: you write MGNREGA as "Mahatma Gandhi National Rural Employment Guarantee Act". The name has "Act", so the type is `law`.

List at most 8 other entities. Put the most important first.

### The person test

List a person only when the speech discusses that person's own actions, life, or record. Examples:

- A leader whom a commemoration debate is about.
- A minister against whom a censure motion is moved.
- A person whom the member accuses of a specific act.

Do not list a person when the member only praises, thanks, credits, blames in one sentence, quotes, or addresses that person. List the thing that the member talks about, not the person.

Examples:

- "Thanks to Modi ji, PM Kisan reached 10 crore farmers." List `Pradhan Mantri Kisan Samman Nidhi`. Do not list Narendra Modi.
- "As Gandhiji said, the soul of India lives in its villages." Do not list Mahatma Gandhi.

## Rules for both lists

1. Give each item a salience from 1 to 5. 5 = the main subject of the speech. 3 = a clear secondary subject. 1 = a passing mention. Give 5 to one item only, or to two items when the speech has two equal main subjects. Leave out passing mentions when the speech has enough clear subjects.
2. `name` is the usual English name, as an English newspaper writes it. If the speech says "kisan" or "किसान", write "Farmers". Write a short form in full when you know it, for example "Mahatma Gandhi National Rural Employment Guarantee Act" for "MGNREGA".
3. `mention` is the words that name the item, copied exactly from the text after `Speech:`, at most 8 words. Keep the original script and spelling. Do not copy from the Debate line. Do not translate, correct, or join the words.
4. Prefer a specific item to a general one. "Cotton crop failure" is better than "Agriculture".
5. Put each item in one list only. Two spellings of one thing are one item, for example "PM Kisan" and "Pradhan Mantri Kisan Samman Nidhi".
6. If the speech has no real subject, for example only thanks or a procedural remark, return two empty lists.
7. If the speech only lays papers on the Table of the House, for example a list of reports, accounts, and notifications that a minister lays, return two empty lists. The summary is one generic sentence, for example "Lays papers, reports, and government notifications on the Table of the House on behalf of several ministers." Do not list the papers.

## Do not extract

- The member who gives the speech.
- The member's own political party.
- Parliamentary bodies and procedure: "the House", "Parliament", "Zero Hour", "Question Hour", "point of order".
- Titles and offices with no named person, when the member only addresses, asks, or thanks them: "the Government", "the Minister", "the Home Minister", "the Railway Minister", "the Speaker", "the Chair". A named ministry is an `institution` only when it is a subject of the speech, not only the addressee.
- Other members of the House whom the member names because they spoke in the debate, asked a question, or made a point. This is common when a minister replies: in "Shri A. Raja asked why the Secretary is involved", the entity is the Secretary's role in the matter, not A. Raja.
- An office, a person, or a document named only as the place where something was said or not said. In "this was not addressed in the Speech of the President or in the Budget presented by the Finance Minister", the subject is the matter that was not addressed. The President and the Finance Minister are not entities.
- India itself, when the speech is about India in general. List India only when the speech compares India with another country or discusses India's relations with another country.
- Sections, clauses, parts, or schedules of a bill or of an ordinary law, for example "Section 29(a)" or "Part A". Exception: a provision of the Constitution of India, for example "Article 21" or "Eighth Schedule of the Constitution". When you are not sure that a provision is part of the Constitution, do not extract it.

## Language

`language` is the main language of the speech: `en`, `hi`, or `mixed`. Use `mixed` only when both languages have long passages. A Hindi speech with some English words or names is `hi`. Decide once and do not reconsider.
