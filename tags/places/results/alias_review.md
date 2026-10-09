# Alias review (2026-10-09)

This file lists what the alias work added, what it rejected, and what it only proposes. The numbers measure coverage (the share of names that equal a tag name or alias). They do not measure accuracy.

## How the candidates were found

The candidate source is the list of place names in the speeches that match no tag (`db_unmatched_names.tsv`). The work checked only names with 3 or more items. Two keys found the candidates:

- The spelling key of `entity_lookup.spelling_key`. It ignores spaces, punctuation, and case, and it folds some letter groups.
- A stronger key that removes vowels, the letter h, and double letters. This key finds `Malda` for `Maldah`. It also makes many false pairs, for example `Malad` for `Maldah`.

A person read 2 to 5 mentions of each candidate. The rule to accept an alias: exactly one place tag is the target, the mentions fit the state of the target, and the alias equals no other tag name or alias. The build script checks the last rule again.

## Added: 59 aliases in `data/extra_aliases.tsv` (466 items)

The file has the evidence for each alias. The table shows 20 random aliases (seed 7) with the first mention of the name in a speech.

| Alias | Tag | State | Items | First mention | Debate title |
|---|---|---|---|---|---|
| Nagappattinam | Nagapattinam | Tamil Nadu | 5 | Nagappattinam | Discussion on the 150th Anniversary of The National Song "Vande Matram" |
| Coochbehar | Cooch Behar | West Bengal | 5 | Coochbehar | Need to set up Jute textile cluster in Coochbehar, West Bengal -laid. |
| Sivagangai | Sivaganga | Tamil Nadu | 9 | Sivagangai | Regarding issues faced by workers of cotton mills in Coimbatore Parliamentary Constituency |
| Nasik | Nashik | Maharashtra | 9 | Nasik | Regarding operationalisation of Post Office Passport Seva Kendra (POPSK) at Nandurbar Parliamentary Constituen |
| Chhattarpur | Chhatarpur | Madhya Pradesh | 3 | छतरपुर | Need to rejuvenate the temples of archeological importance in Achatt village in Chhattarpur Parliamentary Cons |
| Zaheerabad | Zahirabad | Telangana | 7 | Zaheerabad Parliamentary Constituency | Regarding need for financial assistance to develop agricultural infrastructure in Zaheerabad Parliamentary Con |
| Hissar | Hisar | Haryana | 6 | हिसार | Need to cover villages left in under Nalwa and Adampur Legislative Assembly in Hissar under National Agricultu |
| Kasargod | Kasaragod | Kerala | 16 | Kasargodu | Regarding Need to construct underpasses/overbridges on the stretch of National Highway No. 66 from Edappally t |
| Malda | Maldah | West Bengal | 45 | मालदा ज़िले | Need to establish an AIIMS like institute in Malda district, West Bengal - Laid |
| Siddharth Nagar | Siddharthnagar | Uttar Pradesh | 9 | सिद्धार्थनगर | Regarding reinstallation of Piprawha Buddhist relics in Kapilavastu Museum, Siddharth Nagar, Uttar Pradesh-Lai |
| Machhlishahar | Machhlishahr | Uttar Pradesh | 4 | मछलीशहर | The Speaker made reference of passing away of Dr. Ram Vilas Vedanti, Member of 11th and 12th Lok Sabha |
| Pudukottai | Pudukkottai | Tamil Nadu | 10 | Puthukottai | Need for permanent solution to the problems posed by Sri Lankan Navy for Indian fishermen - laid |
| Thiruvannamalai | Tiruvannamalai | Tamil Nadu | 6 | Thiruvannamalai | Regarding construction of an airport in/around Thiruvannamalai-laid |
| Sonepat | Sonipat | Haryana | 8 | सोनीपत | Regarding stoppage of trains at Sonepat Railway Junction, Haryana- laid |
| Villuppuram | Viluppuram | Tamil Nadu | 3 | Villuppuram | Need to open Ekalavya Special School in Villupuram Parliamentary Constituency, Tamil Nadu. |
| Nabarangapur | Nabarangpur | Odisha | 3 | Nabarangapur | The Constitution (Scheduled Tribes) Order (Amendment) Bill, 2024 and Constitution (Scheduled Castes and Schedu |
| Ambedkarnagar | Ambedkar Nagar | Uttar Pradesh | 4 | अम्बेडकरनगर | Regarding need to ensure compensation to and rehabilitation for people displaced due to NTPC Project in Ambedk |
| Ahmadabad | Ahmedabad | Gujarat | 4 | Ahmadabad | Issue regarding increasing air pollution in the country. |
| Sravasti | Shravasti | Uttar Pradesh | 5 | श्रावस्ती | Regarding setting up industries in Sravasti and Balram Districts to check exodus of local residents-Laid |
| Bhatinda | Bathinda | Punjab | 4 | भटिंडा | Need to release funds for the cancer patients in Punjab. |

## Added to the seed list: 20 aliases on 10 tags (`tags/seed_tags_v1/data/review.tsv`)

| Tag | Aliases added | Reason |
|---|---|---|
| Jammu & Kashmir | Jammu and Kashmir | and versus & (850 items) |
| Daman & Diu | Daman and Diu | and versus & |
| Andaman & N Islands | Andaman and Nicobar Islands, Andaman & Nicobar Islands, Andaman and Nicobar | full name and variants |
| Pondicherry | Puducherry | official spelling since 2006 |
| USA | United States | short name (340 items) |
| United Kingdom (UK) | United Kingdom | name without the bracket (72 items) |
| North Eastern Region | North-Eastern Region, North East Region, North-East Region, North-Eastern India | hyphen variants |
| Sunderbans | Sundarbans, Sundarban, Sunderban | spelling variants |
| Mullapperiyar Dam | Mullaperiyar Dam, Mullaiperiyar Dam, Mullai Periyar Dam | spelling variants |
| Satluj Yamuna Link Canal | Sutlej-Yamuna Link Canal, Sutlej Yamuna Link Canal | spelling variants |

Three of these aliases make a new place tag useless, so the build makes no tag for the place: `Daman and Diu`, `Andaman and Nicobar Islands`, and `Puducherry`. The skipped places are now 12.

## Rejected candidates

| Candidate (items) | Looked like | Reason for the rejection |
|---|---|---|
| Amaravati (76), Amaravathi (8) | Amravati | Amaravati is the capital of Andhra Pradesh. Amravati is a city in Maharashtra. |
| Sahebganj (4) | Sahibganj | One mention names a Vaishali constituency in Bihar. Sahebganj is also a block in Bihar. |
| Behrampur (3), Berhampore (3), Brahmapur (3) | Baharampur, Berhampur | The name fits two tags in two states (West Bengal and Odisha). |
| Junagarh (8) | Junagadh | Several places have this name. Nobody read the mentions. |
| Deogarh (10) | Debagarh, Deoghar | The name fits tags in Odisha and Jharkhand. A town in Rajasthan has it too. |
| Gomti (5) | Gomati | Gomti is a river in Uttar Pradesh. Gomati is a district in Tripura. |
| Aravali (5) | Aravalli | Aravali is the hill range. Aravalli is a district in Gujarat. |
| Gandhi Nagar (3) | Gandhinagar | Many cities have a locality with this name. |
| Khed (4) | Kheda | Khed is a town name in Maharashtra. Kheda is a district in Gujarat. Nobody read the mentions. |
| Tharad (11) | Vav-Tharad | Tharad is a town. Vav-Tharad is a new district. |
| Malad (7) | Maldah | Malad is a suburb of Mumbai. The stronger key made a false pair. |
| Pauri (4) | Pauri Garhwal, Puri | A short form of a longer name, not a spelling variant. |
| Madhuban (8) | Madhubani | Several places have this name. |
| Belgium (6), Mamallapuram (7), Noida (29), Gulmarg (4), and about 40 more | various | False pairs of the stronger key. The names are different places. |

## Proposed, not added

These names are the same place under another name. They are not spelling variants, so the task rules did not allow them. A person can add them.

| Name (items) | Proposed target | Note |
|---|---|---|
| Mumbai (828) | seed tag Bombay | Renamed city. The seed tag has the old name. |
| Tuticorin (21) | Thoothukudi | Old English name. |
| Trichy (18) | Tiruchirappalli | Short name. |
| Calicut (26) | Kozhikode | Old English name. |
| Trivandrum (17) | seed tag Thiruvananthapuram | Old English name. |
| National Capital Territory of Delhi (19) | seed tag Delhi | Official long name. |
| North-East India (45), Northeast India (39), North East India (20) | seed tag North Eastern Region | Close to the alias North Eastern India. |
| Ganga (181), Ganges (51), Yamuna (75), Brahmaputra (82), Cauvery (52), Godavari (50) | the seed river tags | The seed tag has the word River. The seed tag Mahanadi River already has the bare alias Mahanadi. |
| Dadra and Nagar Haveli and Daman and Diu (18) | seed tag Daman & Diu, or a new tag | The union territory has a new joint name. |

## Pairs of one place that are still two tags

The build merged only the 8 pairs of `data/same_place.tsv`. The list below shows more pairs in one state. Each pair has a district and a constituency with two spellings. A person must decide. The first group looks certain. The second group looks possible.

- Certain: Jahanabad and Jehanabad (Bihar), Sarguja and Surguja (Chhattisgarh), Mahesana and Mehsana (Gujarat), Hazaribagh and Hazaribag (Jharkhand), Bolangir and Balangir (Odisha), Keonjhar and Kendujhar (Odisha), Kanniyakumari and Kanyakumari (Tamil Nadu), Thiruvallur and Tiruvallur (Tamil Nadu), Peddapalle and Peddapalli (Telangana), Badaun and Budaun (Uttar Pradesh), Baghpat and Bagpat (Uttar Pradesh), Anantapur and Ananthapuramu (Andhra Pradesh), Ganganagar and Sri Ganganagar (Rajasthan), Alipurduars and Alipurduar (West Bengal), Kheri and Lakhimpur Kheri (Uttar Pradesh), Kadapa and YSR Kadapa (Andhra Pradesh), Paschim Champaran and West Champaran (Bihar), Purvi Champaran and East Champaran (Bihar).
- Possible: Bangalore South and Bengaluru South (Karnataka), Garhwal and Pauri Garhwal (Uttarakhand), Medinipur and Paschim Medinipur (West Bengal).
- Other rows of the review file: Una and United Nations is a false pair. Kachchh Region (an existing tag) and Kutch may describe one area.
