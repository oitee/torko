You read one speech from a debate in the Lok Sabha, the lower house of the parliament of India. The speech can be in English, in Hindi, or in a mix of both.

Return a summary, a list of topics, and a list of other entities.

## Summary

One sentence, at most 30 words, in plain English. Say what the member raised, asked for, or argued. Do not say whether the member is right. Do not start with "The member" or "The speaker". Start with the subject. Example: "Asks for compensation for farmers in Vidarbha whose cotton crop failed after unseasonal rain."

## Topics

A topic is a subject or an issue that the speech is about, for example `Farmers' Suicide`, `Air Pollution`, `Arbitration`, `Rail connectivity`.

List at most 8 topics. Put the most important first. Every speech with a real subject has at least one topic, even when the speech is mainly about a place or a law. A speech that asks for a train to a town is about `Rail connectivity`. A speech on a bill about arbitration is about `Arbitration`.

## Other entities

An other entity is a named thing in the speech that a reader can search for. Use one of these types:

| type | Meaning | Example |
|---|---|---|
| `law` | A named act, bill, code, or article of the Constitution. | `Right to Information Act`, `Article 370` |
| `scheme` | A named government scheme, programme, or project. | `Pradhan Mantri Awaas Yojana` |
| `institution` | One named body or organisation. | `Election Commission`, `AIIMS` |
| `place` | A named place: a country, state, district, city, river, or region. | `Bundelkhand`, `Brahmaputra` |
| `person` | One named human who is not the speaker. | `Mahatma Gandhi` |
| `group` | A class of many people. | `Fishermen`, `Scheduled Tribes`, `Companies` |
| `role` | One office that one person holds at a time. | `Governor` |

List at most 8 other entities. Put the most important first.

## Rules for both lists

1. Give each item a salience from 1 to 5. 5 = the main subject of the speech. 3 = a clear secondary subject. 1 = a passing mention. Give 5 to one item only, or to two items when the speech has two equal main subjects. Leave out passing mentions when the speech has enough clear subjects.
2. `name` is the usual English name, as an English newspaper writes it. If the speech says "kisan" or "किसान", write "Farmers". Write a short form in full when you know it, for example "Mahatma Gandhi National Rural Employment Guarantee Act" for "MGNREGA".
3. `mention` is the words in the speech that name the item, copied exactly, at most 8 words. Keep the original script and spelling.
4. Prefer a specific item to a general one. "Cotton crop failure" is better than "Agriculture".
5. Do not put the same item in both lists.
6. If the speech has no real subject, for example only thanks or a procedural remark, return two empty lists.
7. If the speech only lays papers on the Table of the House, for example a list of reports, accounts, and notifications that a minister lays, return two empty lists. The summary is one generic sentence, for example "Lays papers, reports, and government notifications on the Table of the House on behalf of several ministers." Do not list the papers.

## Do not extract

- The speaker.
- The member's own political party, and party leaders whom the member only thanks or praises.
- Parliamentary bodies and procedure: "the House", "Parliament", "Zero Hour", "Question Hour", "point of order".
- Titles and offices with no named person, when the member only addresses, asks, or thanks them: "the Government", "the Minister", "the Home Minister", "the Railway Minister", "the Speaker", "the Chair". A named ministry is an `institution` only when it is a subject of the speech, not only the addressee.
- A person whom the member only addresses, questions, or congratulates. Exception: the person is the central subject of the speech, for example a censure motion against a named minister.
- Other members of the House whom the speaker names because they spoke in the debate, asked a question, or made a point. This is common when a minister replies: in "Shri A. Raja has asked why the Secretary is involved", the entity is the Secretary's role in the matter, not A. Raja.
- An office, a person, or a document named only as the place where something was said or not said. In "this was not addressed in the Speech of the President or in the Budget presented by the Finance Minister", the subject is the matter that was not addressed. The President and the Finance Minister are not entities.
- India itself, when the speech is about India in general. List India only when the speech compares India with another country or discusses India's relations with another country.
- Sections, clauses, parts, or schedules of a bill or of an ordinary law, for example "Section 29(a)" or "Part A". Exception: a provision of the Constitution of India, for example "Article 21" or "Eighth Schedule of the Constitution". When you are not sure that a provision is part of the Constitution, do not extract it.

## Language

`language` is the main language of the speech: `en`, `hi`, or `mixed`.
