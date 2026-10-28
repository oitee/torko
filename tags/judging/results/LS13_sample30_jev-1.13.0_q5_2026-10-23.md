# Relevance check review: sample

Model `jev-1.13.0`, questions `q5`, written on 2026-10-23. 30 speeches. For a topic or a recognised tag, `P(keep)` is P(a main or supporting subject). For a named item, `P(keep)` is P(part of the member's point). An `llm` item is kept at 0.4, a `dict` or `recognised` item at 0.8. `P(refers)` and `Model type` exist only for rows that question version q4 judged. `Source`: `llm` = the extraction, `dict` = the entity dictionary found the words in the text, `recognised` = a recognised tag, near the summary in meaning (its rank and distance in brackets). Write keep or drop in the `review` column of `sample_jev-1.13.0_q5_2026-10-23.tsv`. 0 items carry an earlier manual mark already.

## Devendra Prasad Yadav: Discussion regarding natural calamities in West Bengal, Andhra Pradesh, Bihar and Orissa.

1999-10-28, 130 words, state `speech`. Speech id 408218.

**Summary.** Raises a point of order regarding parliamentary decorum and the maintenance of dignity and rules in the House.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.93 | - | llm | topic |  | Parliamentary decorum | सदन की गरिमा |
| yes | 0.89 | - | recognised (1, 0.33) | topic |  | Question of Privilege | A formal complaint that parliament's rights have been breached. |
| no | 0.68 | - | recognised (2, 0.34) | topic |  | Contempt of House | An act that disrespects the authority of parliament and can bring punishment for the person who did it. |
| no | 0.05 | - | recognised (3, 0.35) | law |  | Rule 193 | Lok Sabha procedural rule allowing members to raise discussions on matters of urgent public importance without formal voting. |
| no | 0.05 | - | recognised (4, 0.35) | law |  | Rule 374 | Lok Sabha procedural rule empowering the Speaker to suspend members who disregard the authority of the Chair. |
| yes | 0.90 | - | recognised (5, 0.35) | topic |  | Parliamentary Etiquette | Expected standards of conduct during parliament sessions. |
| no | 0.07 | - | recognised (6, 0.36) | topic |  | Parliamentary Zero Hour | A period in a parliament session for raising urgent matters. |
| no | 0.04 | - | recognised (8, 0.36) | law |  | Rule 56 | Parliamentary procedure rule |
| yes | 0.81 | - | recognised (9, 0.37) | topic |  | Parliamentary Disruptions | Interruptions, protests, and adjournments that halt official proceedings in legislative houses. |
| no | 0.04 | - | recognised (10, 0.37) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| no | 0.35 | - | recognised (11, 0.37) | topic |  | Observation | A formal note made by parliament on a matter. |
| yes | 0.89 | - | recognised (12, 0.37) | topic |  | MP(s) Conduct | Behavior and ethics of parliament members |
| no | 0.11 | - | recognised (14, 0.37) | topic |  | Rule 184 | A specific rule that allows a parliamentary discussion with a vote. |
| no | 0.54 | - | dict | person |  | Raghunath Jha | रघुनाथ झा |
| yes | 0.95 | - | dict | person |  | Raghuvansh Prasad Singh | रघुवंश बाबू |

## Amar Roy Pradhan: Statement regarding Government Business for the week commencing Monday, 6th December, 1999 and submissions made by the members.

1999-12-03, 120 words, state `speech`. Speech id 407471.

**Summary.** Requests inclusion of remedial steps against terrorism and improvement of living conditions for Indian citizens in Bangladeshi enclaves in the agenda.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.88 | - | llm | topic |  | Counter-terrorism | increasing terrorism |
| yes | 0.90 | - | llm | topic |  | Enclave residents welfare | exchange of Indian enclaves with Bangladeshi enclaves |
| no | 0.42 | - | recognised (1, 0.36) | law |  | Land Boundary Agreement | Bilateral treaty between India and Bangladesh to exchange enclaves and resolve long-standing border disputes. |
| no | 0.02 | - | recognised (2, 0.38) | law |  | Citizenship (Amendment) Bill, 2015 | Proposed legislation to merge the Person of Indian Origin and Overseas Citizen of India categories. |
| yes | 0.86 | - | recognised (3, 0.38) | topic |  | Indo-Bangladesh Relation | Relations between India and Bangladesh. |
| yes | 0.87 | - | recognised (4, 0.38) | topic |  | Indian Citizens | Persons holding citizenship of India |
| no | 0.03 | - | recognised (5, 0.38) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.02 | - | recognised (6, 0.38) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.04 | - | recognised (7, 0.39) | topic |  | Rehabilitation of Kashmiri Pandits | Efforts and policies to resettle displaced Kashmiri Pandits back in the Kashmir Valley. |
| no | 0.40 | - | recognised (8, 0.39) | topic |  | Development of Jammu and Kashmir | Economic growth, infrastructure creation, and social progress within the region of Jammu and Kashmir. |
| no | 0.02 | - | recognised (9, 0.39) | topic |  | Special Category Status for Andhra Pradesh | Demand for preferential central financial assistance and tax concessions for Andhra Pradesh post-bifurcation. |
| no | 0.05 | - | recognised (10, 0.39) | law |  | Assam Accord | Settlement signed in 1985 between the Indian government and Assam movement leaders to detect and deport foreigners. |
| no | 0.02 | - | recognised (11, 0.39) | topic |  | Citizenship Amendment Act Protests | Nationwide public demonstrations and protests against the Citizenship (Amendment) Act of 2019. |
| no | 0.01 | - | recognised (12, 0.40) | law |  | Citizens Amendment Act (CAA) | Law amending citizenship provisions for religious minorities from neighboring countries. |
| yes | 0.95 | - | llm | place |  | Jammu and Kashmir | Jammu and Kashmir |
| yes | 0.90 | - | llm | place |  | Punjab | Punjab |
| yes | 0.97 | - | llm | place |  | North-Eastern region | North-Eastern region |
| no | 0.01 | - | dict | law |  | National Exit Test | NEXT |
| yes | 0.99 | - | dict | place |  | Bangladesh | Bangladeshi |

## Varkala Radhakrishnan: Discussion regarding Code of Civil Procedure (Amendment) Bill, 1999 (Not concluded).

1999-12-16, 1969 words, state `speech`. Speech id 406612.

**Summary.** Supports the Code of Civil Procedure (Amendment) Bill, arguing that judicial delays require comprehensive reforms including judicial decentralization, a constitutional Judicial Commission, and amendment of the Contempt of Courts Act.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Judicial delay | delay in the administration of justice |
| yes | 0.95 | - | llm | topic |  | Judicial decentralization | decentralising judicial powers *(not in text)* |
| yes | 0.97 | - | llm | topic |  | Appointment of judges | appointment of judges to the higher judiciary |
| yes | 0.91 | - | llm | topic |  | Contempt of court | Contempt of Court Act |
| yes | 0.88 | - | llm | topic |  | Alternative dispute resolution | arbitration, conciliation and judicial settlements |
| no | 0.23 | - | recognised (1, 0.34) | law |  | Arbitration and Conciliation (Amendment) Act | Indian amending legislation updating arbitration and conciliation procedures to ensure speedy dispute resolution and attract investment. |
| yes | 0.99 | - | recognised (2, 0.36) | topic |  | Judicial Delay | Slow pace of court cases affecting justice |
| no | 0.36 | - | recognised (3, 0.36) | topic |  | High Court Benches | Setting up regional permanent or circuit benches of High Courts to improve judicial accessibility. |
| no | 0.01 | - | recognised (4, 0.36) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.03 | - | recognised (5, 0.36) | law |  | Commercial Courts Act | Indian law establishing dedicated courts and divisions to fast-track the resolution of commercial disputes. |
| no | 0.02 | - | recognised (6, 0.37) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.06 | - | recognised (7, 0.37) | law |  | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| yes | 0.97 | - | recognised (8, 0.37) | topic |  | Judicial Pendency and Vacancies | Accumulation of unresolved court cases and the shortage of judges across the judicial system. |
| no | 0.01 | - | recognised (9, 0.37) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.03 | - | recognised (10, 0.37) | law |  | Delhi High Court (Amendment) Act | An Indian act amending the pecuniary jurisdiction and procedural rules of the Delhi High Court. |
| yes | 0.99 | - | recognised (11, 0.38) | topic |  | Judicial Reforms | Changes made to improve the courts and legal process. |
| no | 0.02 | - | recognised (13, 0.39) | law |  | Negotiable Instruments (Amendment) Act | Act amending the law on negotiable instruments to expedite trials for dishonoured cheques. |
| yes | 0.99 | - | llm | law |  | Code of Civil Procedure (Amendment) Bill, 1999 | Code of Civil Procedure (Amendment) Bill, 1999 *(not in text)* |
| yes | 1.00 | - | llm | law |  | Indian Evidence Act | Indian Evidence Act |
| yes | 1.00 | - | llm | law |  | Contempt of Court Act | Contempt of Court Act |
| yes | 1.00 | - | llm | institution |  | Supreme Court | Supreme Court |
| yes | 0.98 | - | llm | institution |  | High Courts | High Courts |
| no | 0.69 | - | dict | group |  | Judges | Judges |
| no | 0.00 | - | dict | law |  | Insolvency and Bankruptcy Code | Code |
| no | 0.20 | - | dict | institution |  | Executive | Executive |
| yes | 0.86 | - | dict | law |  | Constitution of India | Constitution |
| no | 0.00 | - | dict | group |  | Left Parties | Left |
| yes | 0.97 | - | dict | law |  | Fundamental Rights | Fundamental Rights |
| no | 0.23 | - | dict | group |  | Ministers | Ministers |
| no | 0.05 | - | dict | institution |  | Panchayati Raj | Panchayati Raj |

## Nitish Sengupta: Discussion on the National Housing Bank (Amendment) Bill, 2000. (Bill passed)

2000-05-12, 829 words, state `speech`. Speech id 404176.

**Summary.** Supports the National Housing Bank (Amendment) Bill, 2000, and suggests increasing its share capital and expanding its lending powers.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Housing finance | housing finances |
| yes | 0.93 | - | llm | topic |  | Banking regulation | checks and balances |
| yes | 0.94 | - | llm | topic |  | Capital requirement | paid-up capitals |
| yes | 0.99 | - | recognised (1, 0.33) | institution |  | National Housing Bank | A government bank that funds housing loans and construction. |
| no | 0.04 | - | recognised (2, 0.38) | law |  | Banking Regulation (Amendment) Act | Act amending banking regulations to bring urban and multi-state cooperative banks under Reserve Bank of India supervision. |
| no | 0.01 | - | recognised (3, 0.38) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.03 | - | recognised (4, 0.39) | institution |  | HUDCO | A government agency that finances affordable housing projects. |
| no | 0.02 | - | recognised (5, 0.39) | law |  | Real Estate (Regulation and Development) Act | Act of parliament regulating the real estate sector and protecting home buyers' interests. |
| no | 0.01 | - | recognised (6, 0.39) | law |  | Taxation Laws (Amendment) Bill | Legislative bill introduced in the Indian parliament to amend existing income tax and financial statutes. |
| no | 0.01 | - | recognised (7, 0.39) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.01 | - | recognised (8, 0.40) | law |  | Insurance Laws (Amendment) Act | Indian act amending insurance legislation to permit increased foreign direct investment and update regulations. |
| no | 0.03 | - | recognised (9, 0.40) | law |  | SARFAESI Act | Act of Parliament allowing banks and financial institutions to auction commercial or residential properties to recover loans. |
| no | 0.01 | - | recognised (11, 0.40) | law |  | National Capital Territory of Delhi Laws (Special Provisions) Second (Amendment) Act | Indian act extending temporary protection to unauthorized constructions and encroachments in Delhi from punitive action. |
| no | 0.02 | - | recognised (12, 0.40) | law |  | Negotiable Instruments (Amendment) Act | Act amending the law on negotiable instruments to expedite trials for dishonoured cheques. |
| yes | 0.83 | - | recognised (13, 0.40) | topic |  | Housing Loans | General credit that helps people pay for building or buying a home. |
| yes | 0.99 | - | llm | law |  | National Housing Bank (Amendment) Bill, 2000 | National Housing Bank (Amendment) Bill, 2000 *(not in text)* |
| yes | 1.00 | - | llm | institution |  | Reserve Bank of India | Reserve Bank of India |
| yes | 0.52 | - | llm | law |  | Public Debts Recovery Act | Public Debts Recovery Act |
| yes | 1.00 | - | llm | institution |  | National Housing Bank | National Housing Bank |
| no | 0.14 | - | llm | institution |  | Grindlays Bank | Grindlays Bank |
| no | 0.45 | - | dict | role |  | Director | Director |
| no | 0.19 | - | dict | institution |  | Appellate Tribunal | Appellate Tribunal |
| no | 0.14 | - | dict | person |  | Harshad Mehta | Harshad Mehta |

## Madhavrao Scindia: Requested to constitute an inquiry committee against the Indraprastha Apolo Hospital fo find out the mishandling in the case of Shri Kumaramangalam, Minister of Energy resulting in a deteriorating health condition of the Minister.

2000-08-18, 110 words, state `speech`. Speech id 402177.

**Summary.** Expresses concern over the deteriorating health of a Union Cabinet colleague and conveys wishes for his speedy recovery.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| no | 0.28 | - | recognised (1, 0.41) | topic |  | Diseases | Illness and conditions affecting health |
| no | 0.05 | - | recognised (2, 0.42) | topic |  | Cancer | Serious disease affecting population health |
| no | 0.07 | - | recognised (3, 0.42) | topic |  | Heart Diseases | Cardiovascular conditions affecting the heart |
| no | 0.01 | - | recognised (4, 0.42) | person |  | Rajiv Gandhi | Former Prime Minister of India |
| no | 0.07 | - | recognised (5, 0.42) | institution |  | Ministry of Health | Union ministry responsible for public health policies and medical programmes in India. |
| no | 0.01 | - | recognised (6, 0.42) | law |  | Senior Citizens (Provision of Geriatric and Dementia Care) Bill | Proposed law to provide specialised healthcare, geriatric services, and dementia care for elderly persons in India. |
| no | 0.01 | - | recognised (7, 0.42) | scheme |  | Pradhan Mantri Swasthya Suraksha Yojana | Central government scheme aimed at correcting regional imbalances in tertiary healthcare and medical education. |
| no | 0.08 | - | recognised (8, 0.43) | topic |  | Chronic Diseases | Long-term illnesses affecting health over extended periods |
| no | 0.01 | - | recognised (9, 0.43) | topic |  | Pan Masala | Betel leaf preparation with health concerns |
| no | 0.06 | - | recognised (10, 0.43) | institution |  | Ministry of Health and Family Welfare | Union ministry responsible for public health, family planning, medical education, and healthcare infrastructure. |
| no | 0.01 | - | recognised (11, 0.43) | scheme |  | PM Ayushman Bharat Health Infrastructure Mission | Central scheme aimed at strengthening primary, secondary, and tertiary public healthcare infrastructure and surveillance. |
| no | 0.01 | - | recognised (12, 0.43) | scheme |  | Pradhan Mantri Atmanirbhar Swasth Bharat Yojana | Central government scheme to strengthen healthcare infrastructure and disease surveillance across India. |
| no | 0.45 | - | dict | institution |  | Union Cabinet | Union Cabinet |

## Vijayendra Pal Singh: Discussion on the Passport (entry into India) Amendment Bill,2000 .(Bill passed)

2000-11-28, 547 words, state `speech`. Speech id 401361.

**Summary.** Supports the Passport Entry into India Amendment Bill while suggesting improvements in computerization, passport photograph security, and travel documentation for non-resident Indians.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Passport regulation and security | Passport (Entry into India) Amendment Bill, 2000 |
| yes | 0.67 | - | llm | topic |  | Passport computerization | computerisation |
| yes | 0.40 | - | llm | topic |  | NRI travel documentation | Orange Card |
| no | 0.01 | - | recognised (1, 0.34) | law |  | Citizenship (Amendment) Bill, 2015 | Proposed legislation to merge the Person of Indian Origin and Overseas Citizen of India categories. |
| no | 0.71 | - | recognised (2, 0.37) | law |  | Immigration Control | Government regulation of foreign nationals entering and residing in India. |
| yes | 0.98 | - | recognised (3, 0.38) | law |  | Passports | Travel documents identifying citizens. |
| no | 0.09 | - | recognised (4, 0.38) | law |  | Photo Identity Cards | Official documents with photographs identifying individuals for security purposes. |
| no | 0.01 | - | recognised (5, 0.38) | law |  | Aadhaar and Other Laws (Amendment) Act | An Indian act amending laws to allow voluntary use of Aadhaar for identity verification and address privacy concerns. |
| no | 0.20 | - | recognised (6, 0.39) | topic |  | Overseas Citizen of India | Immigration status granting foreign citizens of Indian origin multiple-entry, lifelong visas and residency rights. |
| no | 0.06 | - | recognised (7, 0.39) | law |  | E-VISA | Electronic travel permit. |
| no | 0.01 | - | recognised (8, 0.39) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.01 | - | recognised (9, 0.39) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.34 | - | recognised (10, 0.39) | topic |  | Indian Citizens | Persons holding citizenship of India |
| no | 0.01 | - | recognised (11, 0.40) | law |  | National Investigation Agency (Amendment) Act | Act expanding the National Investigation Agency's jurisdiction to investigate offences committed outside India. |
| no | 0.01 | - | recognised (12, 0.40) | law |  | Taxation Laws (Amendment) Bill | Legislative bill introduced in the Indian parliament to amend existing income tax and financial statutes. |
| yes | 0.68 | - | llm | law |  | Passport (Entry into India) Amendment Act | Passport (Entry into India) Amendment Bill, 2000 |
| no | 0.35 | - | llm | law |  | Passport Act, 1967 | Passport Bill of 1967 |
| yes | 0.98 | - | llm | institution |  | Ministry of External Affairs | Ministry of External Affairs |
| yes | 1.00 | - | llm | institution |  | Ministry of Home Affairs | Ministry of Home |
| yes | 0.98 | - | dict | group |  | Non-Resident Indians | NRIs |
| no | 0.56 | - | dict | place |  | Chennai | Chennai |
| no | 0.24 | - | dict | place |  | Mumbai | Mumbai |
| no | 0.29 | - | dict | place |  | Delhi | Delhi |

## Laxminarayan Pandey: Discussion regarding loss of lives and property due to floods, drought and other natural calamities in various parts of the country.

2000-11-30, 534 words, state `speech`. Speech id 401111.

**Summary.** Urges the government to ensure timely distribution and proper implementation of relief funds allocated to states affected by droughts, floods, and natural calamities.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Natural calamities relief | प्राकृतिक आपदा |
| yes | 0.63 | - | llm | topic |  | Agricultural drought | सूखे |
| no | 0.28 | - | recognised (1, 0.32) | scheme |  | National Calamity Contingency Fund (NECF) | Central government emergency fund for relief after a natural disaster. |
| no | 0.48 | - | recognised (2, 0.33) | scheme |  | State Disaster Response Fund (SDRF) | Government fund, run by each state, that pays for disaster relief. Formerly the Calamity Relief Fund. |
| yes | 0.95 | - | recognised (3, 0.33) | topic |  | Drought Relief | Government assistance to areas affected by drought conditions. |
| no | 0.76 | - | recognised (4, 0.34) | topic |  | Flood Relief | Government assistance to flooded areas. |
| no | 0.37 | - | recognised (5, 0.34) | scheme |  | National Disaster Relief Fund | Government fund that provides financial aid for natural disaster recovery. |
| yes | 0.93 | - | recognised (6, 0.35) | topic |  | Disaster Relief Funds | Financial reserves and budgetary allocations dedicated to emergency relief, rehabilitation, and disaster recovery. |
| yes | 0.94 | - | recognised (7, 0.35) | topic |  | Flood and Drought Management | Policies, preventive measures, and relief actions to manage extreme excess or scarcity of water. |
| yes | 0.97 | - | recognised (8, 0.36) | topic |  | Natural Calamities | Destructive natural events such as floods, earthquakes, and cyclones. |
| yes | 0.97 | - | recognised (9, 0.36) | topic |  | Natural Disaster Relief | General government assistance given to people affected by a disaster. |
| no | 0.18 | - | recognised (10, 0.36) | scheme |  | Prime Minister's National Relief Fund | Government fund controlled by the prime minister for emergency relief. |
| yes | 0.91 | - | recognised (11, 0.37) | topic |  | National Calamity | Natural disaster and emergency response. |
| no | 0.02 | - | recognised (12, 0.37) | scheme |  | PM-CARES Fund | Prime minister's relief fund set up for national emergencies. |
| yes | 1.00 | - | llm | place |  | Madhya Pradesh | मध्य प्रदेश |
| no | 0.11 | - | llm | place |  | Tamil Nadu | तमिलनाडु |
| no | 0.06 | - | llm | place |  | West Bengal | वैस्ट बंगाल |
| no | 0.01 | - | llm | place |  | Himachal Pradesh | हिमाचल प्रदेश |
| no | 0.02 | - | llm | place |  | Orissa | उड़ीसा |
| yes | 0.95 | - | dict | place |  | Khargone | खरगौन |
| yes | 0.83 | - | dict | place |  | Khandwa | खंडवा |
| no | 0.20 | - | dict | place |  | Sagar | सागर |
| no | 0.10 | - | dict | place |  | Khajuraho | खजुराहो |
| no | 0.17 | - | dict | place |  | Barh | बाढ़ |
| yes | 1.00 | - | dict | role |  | District Collector | कलेक्टर |
| no | 0.05 | - | dict | place |  | Mandsaur | मंदसौर |

## V. Saroja: Request the Government to fix the support price for purchasing of beetlenut (supari).

2000-12-01, 128 words, state `speech`. Speech id 401012.

**Summary.** Raises issues regarding flood damage to a bridge connecting Kolli Hills and financial irregularities in scholarship funds for Scheduled Castes, Scheduled Tribes, and backward classes.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| no | 0.29 | - | llm | topic |  | Bridge construction and repair | bridge, which is connecting the Kolli Hills |
| yes | 0.42 | - | llm | topic |  | Educational grants and scholarships | अनुसूचित जातियों, जनजातियों और पिछड़े वगा् के छात्रों को वजीफा और सुविधाएं |
| no | 0.37 | - | recognised (1, 0.35) | topic |  | Scholarships for Backward Classes | Government financial assistance schemes supporting students belonging to Other Backward Classes in pursuing education. |
| no | 0.37 | - | recognised (2, 0.36) | topic |  | Scholarships for Scheduled Castes | Government financial grants and welfare aid supporting students from Scheduled Castes in schooling and higher education. |
| no | 0.39 | - | recognised (3, 0.37) | topic |  | Educational Support for Backward Classes | Scholarships, fee waivers, hostels, and specialized schemes for students from socially and educationally backward communities. |
| no | 0.39 | - | recognised (4, 0.37) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.31 | - | recognised (5, 0.40) | scheme |  | Minority Scholarships | Government financial aid programmes supporting students from religious minority communities for schooling and higher education. |
| no | 0.48 | - | recognised (6, 0.40) | topic |  | Social Problems | Issues affecting society and welfare |
| no | 0.37 | - | recognised (7, 0.40) | topic |  | Scheduled Castes and Scheduled Tribes | The two groups of communities that India officially recognises as disadvantaged. |
| no | 0.28 | - | recognised (8, 0.40) | topic |  | Backward Classes | Communities that are socially and economically disadvantaged. |
| no | 0.19 | - | recognised (9, 0.40) | institution |  | Committee on the Welfare of Scheduled Castes and Scheduled Tribes | Parliamentary committee overseeing the implementation of constitutional safeguards and welfare measures for SCs and STs. |
| no | 0.07 | - | recognised (10, 0.40) | topic |  | Scs & Sts Atrocities | Crimes against scheduled castes and tribes. |
| no | 0.47 | - | recognised (11, 0.40) | topic |  | Welfare Schemes | General government programs that improve the well-being of citizens. |
| no | 0.18 | - | recognised (12, 0.41) | law |  | SCs & STs lists | Lists of scheduled castes and scheduled tribes. |
| yes | 0.91 | - | llm | place |  | Sendhamangalam | Sendhamangalam |
| yes | 0.87 | - | llm | place |  | Kolli Hills | Kolli Hills |
| yes | 0.89 | - | llm | group |  | Scheduled Castes | अनुसूचित जातियों |
| yes | 0.87 | - | llm | group |  | Scheduled Tribes | जनजातियों |
| no | 0.68 | - | dict | person |  | Mulayam Singh Yadav | मुलायम सिंह यादव |
| no | 0.00 | - | dict | scheme |  | Aadhaar | आधार |
| yes | 0.91 | - | dict | group |  | Students | छात्रों |
| no | 0.76 | - | dict | group |  | Other Backward Classes | पिछड़े |

## Murli Manohar Joshi: Further discussion regarding ‘Saffronisation’ of education initiated by Shri Somnath Chatterjee on 16.8.2001. (Concluded)

2001-08-20, 170 words, state `speech`. Speech id 397266.

**Summary.** Defends NCERT educational documents against allegations of saffronisation, challenging critics to identify any content contrary to national educational policies.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.93 | - | llm | topic |  | Educational policy | एन.सी.ई.आर.टी. के डॉक्यूमेंटस |
| yes | 0.90 | - | recognised (1, 0.33) | topic |  | Saffronisation | Alleged promotion of Hindu nationalist ideology |
| yes | 0.90 | - | recognised (2, 0.34) | institution |  | National Council for Educational Research and Training (NCERT) | Authority developing curriculum and textbooks |
| no | 0.57 | - | recognised (3, 0.37) | law |  | National Education Policy | Comprehensive education policy framework |
| no | 0.02 | - | recognised (4, 0.38) | scheme |  | PM SHRI | Central initiative upgrading select schools to showcase exemplary education under the National Education Policy 2020. |
| no | 0.02 | - | recognised (5, 0.40) | scheme |  | Samagra Shiksha Abhiyan | Centrally sponsored overarching programme for the school education sector from preschool to class twelve. |
| no | 0.02 | - | recognised (6, 0.40) | topic |  | Medical Education Reform | Policy changes and initiatives aimed at improving the quality and accessibility of medical training in India. |
| no | 0.01 | - | recognised (7, 0.40) | scheme |  | PM POSHAN | Central scheme providing free hot cooked mid-day meals to school children across India. |
| no | 0.14 | - | recognised (8, 0.40) | law |  | National Council for Teacher Education Act | Indian act establishing a statutory council to oversee and maintain standards in teacher education. |
| no | 0.69 | - | recognised (9, 0.41) | topic |  | School Curriculum | The subjects and content that schools teach students. |
| no | 0.09 | - | recognised (10, 0.41) | institution |  | Department of Higher Education | A central government department overseeing university education, policy formulation, and academic institutes of national importance. |
| no | 0.37 | - | recognised (11, 0.41) | topic |  | Minority Education | Educational access, institutions, and policies for religious and linguistic minority groups in India. |
| no | 0.12 | - | recognised (12, 0.41) | institution |  | Standing Committee on Human Resource Development | Parliamentary body that examined policies, legislation, and budgets related to education and human resource development in India. |
| yes | 1.00 | - | llm | institution |  | National Council of Educational Research and Training | एन.सी.ई.आर.टी. |

## Chandra Vijay Singh: Need to construct a road connecting Pakbada at National Highway No. 24, Moradabad with National Highway at Kashipur, U.P. and declare it as a National Highway.

2002-03-20, 134 words, state `speech`. Speech id 394255.

**Summary.** Urges the construction of a new National Highway connecting Pakbada at National Highway No. 24 to Kashipur via a new bridge over the Ramganga river to reduce distance and enhance security.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Road construction | राषट्रीय राजमार्ग की स्थापना |
| yes | 0.96 | - | llm | topic |  | Regional connectivity | दिल्ली से दूरी कम करने |
| yes | 0.63 | - | llm | topic |  | National security | भारत की सुरक्षा |
| yes | 0.94 | - | recognised (1, 0.38) | topic |  | Highway Construction and Safety | Building and widening national highways alongside engineering measures to prevent road accidents. |
| no | 0.78 | - | recognised (2, 0.39) | place |  | National Highway 24 | National highway in Uttar Pradesh connecting Delhi with Lucknow. |
| yes | 0.96 | - | recognised (3, 0.39) | topic |  | National Highway Expansion | Widening, upgrading, and acquiring land for India's national highway network. |
| no | 0.08 | - | recognised (4, 0.39) | scheme |  | National Highways Development Project | Major government project aimed at upgrading and widening key national highways across India. |
| no | 0.03 | - | recognised (5, 0.40) | scheme |  | Bharatmala Pariyojana | Government program that builds and connects national highways. |
| no | 0.08 | - | recognised (6, 0.40) | institution |  | National Highways Authority of India (NHAI) | The government body that builds and manages India's national highways. |
| yes | 0.84 | - | recognised (7, 0.41) | place |  | National Highways | Major roads managed by the central government connecting different regions. |
| no | 0.01 | - | recognised (8, 0.41) | scheme |  | Delhi-Mumbai Expressway | A major access-controlled expressway connecting India's national capital Delhi with its financial hub Mumbai. |
| no | 0.09 | - | recognised (9, 0.41) | topic |  | Rail Connectivity and Overbridge Construction | Expansion of railway networks and building overbridges or underpasses to improve road and rail traffic. |
| no | 0.50 | - | recognised (10, 0.41) | institution |  | Ministry of Road Transport and Highways | Indian union ministry responsible for the development and maintenance of national highways and road transport systems. |
| yes | 0.98 | - | recognised (11, 0.41) | topic |  | Road Construction | Building or improving roads and highways. |
| no | 0.02 | - | recognised (12, 0.42) | place |  | National Highway 19 | Major national highway in India connecting Delhi and Kolkata. |
| yes | 0.99 | - | llm | law |  | National Highway No. 24 | राषट्रीय राजमार्ग 24 |
| yes | 1.00 | - | llm | place |  | Pakbada | पाकबड़ा |
| yes | 1.00 | - | llm | place |  | Moradabad | मुरादाबाद |
| yes | 1.00 | - | llm | place |  | Kashipur | काशीपुर |
| yes | 1.00 | - | llm | place |  | Ramganga River | राम गंगा नदी |
| yes | 1.00 | - | llm | place |  | Uttaranchal | उत्तरांचल |
| no | 0.71 | - | dict | group |  | Petrol | पैट्रोल |
| no | 0.76 | - | dict | group |  | Diesel | डीजल |
| yes | 0.99 | - | dict | place |  | Kumaon | कुमाऊं |
| yes | 0.99 | - | dict | place |  | Delhi | दिल्ली |
| yes | 0.98 | - | dict | place |  | Haridwar | हरिद्वार |

## Dr. Kirit Somaiya: Combined discussion on the Budget (Railways) for the year 2002-2003, Demands for Grants on Account Nos. 1 to 16 in respect of Budget (Railways) for 2001-2002 and Demands for Supplementary Grants Nos. 12, 15 and 16 in respect of Budget (Railways) for the year 2001-2002.

2002-03-21, 511 words, state `speech`. Speech id 394084.

**Summary.** Requests improved passenger amenities and better suburban railway facilities for ten railway stations in Mumbai's Central Railway division.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Suburban railway passenger amenities | passenger amenities needed for various Railway Stations |
| yes | 0.90 | - | recognised (1, 0.34) | institution |  | Central Railway | One of the zones of Indian Railways, headquartered at Chhatrapati Shivaji Maharaj Terminus in Mumbai. |
| no | 0.04 | - | recognised (2, 0.36) | scheme |  | Adarsh Station Scheme | An Indian Railways programme to modernise and upgrade passenger amenities at selected railway stations. |
| no | 0.05 | - | recognised (3, 0.38) | institution |  | Western Railway | Zonal division of Indian Railways headquartered at Churchgate, Mumbai. |
| no | 0.02 | - | recognised (4, 0.39) | scheme |  | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| yes | 0.98 | - | recognised (5, 0.39) | topic |  | Railway Passenger Amenities | Facilities and services provided to railway passengers. |
| no | 0.10 | - | recognised (6, 0.39) | topic |  | Railway Cleanliness | Hygiene, sanitation, and waste management initiatives on trains and across railway stations in India. |
| no | 0.69 | - | recognised (7, 0.39) | topic |  | Rail Connectivity and Overbridge Construction | Expansion of railway networks and building overbridges or underpasses to improve road and rail traffic. |
| no | 0.04 | - | recognised (8, 0.39) | scheme |  | Mumbai Urban Transport Project | Joint government project improving suburban rail, roads, and mass transit infrastructure in the Mumbai metropolitan region. |
| no | 0.39 | - | recognised (9, 0.40) | topic |  | Railway Modernisation | Upgrading rail infrastructure, rolling stock, signaling, and technology across Indian Railways. |
| yes | 0.97 | - | recognised (10, 0.40) | topic |  | Railway Station Infrastructure | Physical facilities, amenities, platforms, and passenger buildings at railway stations. |
| yes | 0.90 | - | recognised (11, 0.40) | place |  | Mumbai Suburban | District in Maharashtra, India. |
| no | 0.02 | - | recognised (12, 0.41) | institution |  | South Central Railway | Zone of Indian Railways headquartered at Secunderabad, serving parts of Telangana, Andhra Pradesh, and nearby states. |
| yes | 0.99 | - | llm | institution |  | Central Railway | Central Railway |
| yes | 1.00 | - | llm | place |  | Mumbai | Mumbai |
| yes | 0.96 | - | llm | institution |  | Rakesh Mohan Committee | Rakesh Mohan Committee |
| yes | 0.96 | - | llm | place |  | Mulund | Mulund |
| yes | 0.94 | - | llm | place |  | Ghatkopar | Ghatkopar |
| yes | 0.92 | - | llm | place |  | Chembur | Chembur |
| yes | 0.98 | - | dict | place |  | Govandi | Govandi |
| no | 0.29 | - | dict | place |  | Nag River | Nagar |
| yes | 0.94 | - | dict | place |  | Mankhurd | Mankhurd |
| yes | 0.99 | - | dict | group |  | Employers | employer |
| yes | 0.99 | - | dict | law |  | Railway Budget | Railway Budget |
| no | 0.00 | - | dict | scheme |  | Graduate Aptitude Test in Engineering | GATE |
| yes | 0.95 | - | dict | place |  | Bhandup | Bhandup |
| no | 0.41 | - | dict | place |  | Vikhroli | Vikhroli |

## Vinay Kumar Sorake: Need to take steps to protect the interests of local fishermen in Dakshin Kannada - Laid.

2002-05-02, 185 words, state `speech`. Speech id 393356.

**Summary.** Asks the Central Government to protect traditional fishermen by restricting deep-sea trawlers and providing a survival package and infrastructure assistance.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Fishermen welfare and deep-sea trawling | fishermen community |
| yes | 0.98 | - | recognised (1, 0.36) | topic |  | Fishermen Welfare | Government support for people who work in fishing. |
| yes | 0.95 | - | recognised (2, 0.36) | topic |  | Fishermen Security | Protection of fishers from maritime disputes, coastal piracy, and detention by neighbouring countries. |
| no | 0.26 | - | recognised (3, 0.37) | institution |  | Department of Fisheries | A central government department responsible for developing, managing, and regulating fisheries and aquaculture in India. |
| no | 0.04 | - | recognised (4, 0.37) | scheme |  | Pradhan Mantri Matsya Sampada Yojana | Government scheme that supports fish farming and fishing communities. |
| no | 0.12 | - | recognised (5, 0.37) | topic |  | Coastal Regulation Zone | Regulatory classification of coastal stretches in India to protect marine ecology and control development. |
| yes | 0.87 | - | recognised (6, 0.38) | topic |  | Fishermen Safety | Protection and emergency rescue measures for individuals engaged in marine and inland fishing. |
| no | 0.02 | - | recognised (7, 0.38) | scheme |  | Kuttanad Package | Government rehabilitation programme to support wetland farming, flood management, and ecological development in Kuttanad, Kerala. |
| no | 0.33 | - | recognised (8, 0.38) | institution |  | Ministry of Fisheries, Animal Husbandry and Dairying | Union ministry overseeing livestock development, dairy farming, and marine and inland fisheries in India. |
| no | 0.02 | - | recognised (9, 0.38) | group |  | Nishad Community | Traditional river-dependent and fishing community in India. |
| yes | 0.97 | - | recognised (10, 0.39) | topic |  | Coastal Fishing | Marine resources harvesting. |
| yes | 0.92 | - | recognised (11, 0.39) | topic |  | Deep Sea Fishing | Ocean fishing far from shore. |
| no | 0.01 | - | recognised (12, 0.39) | topic |  | Special Category Status for Andhra Pradesh | Demand for preferential central financial assistance and tax concessions for Andhra Pradesh post-bifurcation. |
| yes | 1.00 | - | llm | place |  | Dakshin Kannada | Dakshin Kannada |
| yes | 0.84 | - | llm | place |  | Malpe | Malpe |
| yes | 1.00 | - | dict | group |  | Fishermen | fishermen |
| no | 0.79 | - | dict | place |  | Udupi | Udupi |

## Subodh Mohite: Discussion on the Patents (Amendment) Bill, 2002 (Bill passed).

2002-05-14, 1126 words, state `speech`. Speech id 392699.

**Summary.** Supports the Patents Amendment Bill while emphasizing that patent laws must safeguard national security, public interest, affordable life-saving drugs, and food security against multinational dominance.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Patent law and intellectual property | पेटेंट विधेयक |
| yes | 0.97 | - | llm | topic |  | Multinational corporations influence | मल्टीनेशनल कम्पनियों *(not in text)* |
| yes | 0.96 | - | llm | topic |  | Public health and life-saving drugs | लाइफ सेविंग ड्रग्स |
| yes | 0.83 | - | llm | topic |  | National interest and security | national interest |
| no | 0.09 | - | recognised (1, 0.36) | law |  | Health Security se National Security Cess Bill | Proposed law to levy a special tax for funding healthcare infrastructure and national security initiatives. |
| no | 0.01 | - | recognised (3, 0.38) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.01 | - | recognised (4, 0.39) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.02 | - | recognised (5, 0.39) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.02 | - | recognised (6, 0.39) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.01 | - | recognised (7, 0.40) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.01 | - | recognised (8, 0.40) | law |  | National Anti-Doping (amendment) Bill 2025 | Legislative amendment to anti-doping regulations |
| no | 0.01 | - | recognised (9, 0.40) | law |  | Aadhaar and Other Laws (Amendment) Act | An Indian act amending laws to allow voluntary use of Aadhaar for identity verification and address privacy concerns. |
| no | 0.01 | - | recognised (10, 0.41) | law |  | Insurance Laws (Amendment) Act | Indian act amending insurance legislation to permit increased foreign direct investment and update regulations. |
| no | 0.77 | - | recognised (11, 0.41) | law |  | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| no | 0.06 | - | recognised (12, 0.41) | law |  | NATIONAL FOOD SECURITY ACT | Law guaranteeing subsidized food for poor households |
| no | 0.01 | - | recognised (13, 0.41) | law |  | Taxation Laws (Amendment) Bill | Legislative bill introduced in the Indian parliament to amend existing income tax and financial statutes. |
| yes | 1.00 | - | llm | law |  | Patents (Amendment) Bill, 2002 | पेटेंट विधेयक |
| yes | 0.99 | - | dict | group |  | Developing countries | developing countries |
| no | 0.01 | - | dict | institution |  | PepsiCo | पेप्सी कोला |
| yes | 0.93 | - | dict | group |  | Multinational corporations | multi-national companies |
| no | 0.13 | - | dict | person |  | Murasoli Maran | मुरासोली मारन |
| no | 0.59 | - | dict | person |  | Mani Shankar Aiyar | मणि शंकर जी |

## Radha Mohan Singh: Need to include Tharu caste in Bihar in the list of Scheduled Tribe.

2002-05-15, 228 words, state `speech`. Speech id 392545.

**Summary.** Requests the inclusion of the Tharu community in Bihar in the list of Scheduled Tribes, similar to their status in Uttar Pradesh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Scheduled Tribe status for Tharu community | थारु जाति |
| yes | 0.89 | - | llm | topic |  | Constitutional equality | भारतीय संविधान के अनुच्छेद 14 तथा 15 |
| yes | 0.99 | - | recognised (1, 0.34) | group |  | Tharu | Indigenous community living predominantly in the Terai plains of Nepal and northern India. |
| no | 0.62 | - | recognised (2, 0.34) | law |  | Constitution (Scheduled Tribes) Order Amendment Bill | Proposed legislation to modify the official list of Scheduled Tribes in Indian states and union territories. |
| yes | 0.94 | - | recognised (3, 0.34) | topic |  | SCs and STs welfare | Support for scheduled communities |
| yes | 0.98 | - | recognised (4, 0.34) | topic |  | Scheduled Tribe Status | Official constitutional recognition of historically disadvantaged indigenous tribal communities in India. |
| yes | 0.94 | - | recognised (5, 0.35) | law |  | SCs & STs lists | Lists of scheduled castes and scheduled tribes. |
| yes | 0.97 | - | recognised (6, 0.35) | topic |  | Scheduled Tribes | Communities of India officially recognised as indigenous tribal groups. |
| yes | 0.96 | - | recognised (7, 0.35) | topic |  | Scheduled Tribes Representation | Participation and representation of Scheduled Tribes in political bodies, public offices, and administrative systems. |
| no | 0.16 | - | recognised (8, 0.35) | law |  | Constitution (Scheduled Castes) Order (Amendment) Act | Legislation amending the official list of recognized Scheduled Castes for specific states and union territories. |
| yes | 0.97 | - | recognised (9, 0.36) | topic |  | Scheduled Castes and Scheduled Tribes | The two groups of communities that India officially recognises as disadvantaged. |
| no | 0.66 | - | recognised (10, 0.36) | law |  | Constitution (Scheduled Tribes) Order | Presidential order specifying the communities recognised as Scheduled Tribes across Indian states and union territories. |
| no | 0.02 | - | recognised (11, 0.36) | group |  | Nishad Community | Traditional river-dependent and fishing community in India. |
| no | 0.52 | - | recognised (12, 0.36) | law |  | Constitution (Scheduled Tribes) Order (Amendment) Act | Indian legislation amending the list of recognised Scheduled Tribes in specific states. |
| yes | 1.00 | - | llm | group |  | Tharu | थारु जाति |
| yes | 1.00 | - | llm | place |  | Bihar | बिहार |
| yes | 0.63 | - | llm | place |  | Uttar Pradesh | उत्तर प्रदेश |
| yes | 0.99 | - | llm | law |  | Article 14 of the Constitution | अनुच्छेद 14 |
| yes | 0.97 | - | llm | law |  | Article 15 of the Constitution | अनुच्छेद 15 *(not in text)* |
| yes | 1.00 | - | dict | group |  | Scheduled Tribes | अनुसूचित जनजातियों |
| yes | 0.99 | - | dict | law |  | Constitution of India | संविधान |
| no | 0.78 | - | dict | group |  | Other Backward Classes | पिछड़े |
| no | 0.74 | - | dict | place |  | Bagaha | बगहा |
| no | 0.21 | - | dict | place |  | Pilibhit | पीलीभीत |
| no | 0.13 | - | dict | place |  | Kheri | खीरी |
| yes | 0.99 | - | dict | place |  | West Champaran | पश्चिम चम्पारण |
| no | 0.73 | - | dict | place |  | Ramnagar | रामनगर |

## M.O.H. Farook: Discussion on the Haj Committee Bill, 2002. (Bill passed)

2002-05-16, 783 words, state `speech`. Speech id 392445.

**Summary.** Supports the Haj Committee Bill, 2002 and asks the government to expedite rules, organize State Haj Committees, and consider establishing a committee presence or office in Saudi Arabia.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Haj pilgrimage management | Haj Committee Bill *(not in text)* |
| yes | 0.98 | - | llm | topic |  | Haj committee operations | Haj Committee |
| no | 0.03 | - | recognised (1, 0.39) | institution |  | All India Muslim Personal Law Board | A non-governmental organization in India that advocates for the protection and application of Muslim personal laws. |
| no | 0.03 | - | recognised (2, 0.39) | institution |  | Sachar Committee | A government committee that studied the condition of Muslim communities in India. |
| no | 0.01 | - | recognised (3, 0.40) | law |  | Citizenship (Amendment) Bill, 2015 | Proposed legislation to merge the Person of Indian Origin and Overseas Citizen of India categories. |
| no | 0.01 | - | recognised (4, 0.41) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.05 | - | recognised (5, 0.41) | institution |  | Bezbaruah Committee | Committee established to examine concerns and recommend safety measures for people from Northeast India living nationwide. |
| no | 0.02 | - | recognised (6, 0.41) | institution |  | Central Wakf Council | A government body that oversees Muslim charitable religious trusts across India. |
| yes | 0.99 | - | recognised (7, 0.41) | topic |  | Haj Pilgrimage | The annual Islamic pilgrimage that Muslims make to the city of Mecca. |
| no | 0.02 | - | recognised (8, 0.42) | institution |  | Srikrishna Committee | Expert committee appointed by the central government, notably examining the Telangana statehood or data protection issues. |
| no | 0.01 | - | recognised (9, 0.42) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.73 | - | recognised (10, 0.42) | topic |  | Islam | Religious faith with millions of followers in India |
| no | 0.02 | - | recognised (11, 0.42) | institution |  | Standing Committee on Human Resource Development | Parliamentary body that examined policies, legislation, and budgets related to education and human resource development in India. |
| no | 0.01 | - | recognised (12, 0.42) | law |  | Senior Citizens (Provision of Geriatric and Dementia Care) Bill | Proposed law to provide specialised healthcare, geriatric services, and dementia care for elderly persons in India. |
| yes | 1.00 | - | llm | law |  | Haj Committee Bill, 2002 | Haj Committee Bill, 2002 *(not in text)* |
| yes | 1.00 | - | llm | place |  | Saudi Arabia | Saudi Arabia |
| yes | 1.00 | - | llm | place |  | Mumbai | Mumbai |
| yes | 0.85 | - | llm | institution |  | State Haj Committees | State Haj Committees |
| no | 0.60 | - | dict | group |  | Haj pilgrims | Haj Pilgrims |
| yes | 0.85 | - | dict | group |  | Ministers | Ministers |
| no | 0.00 | - | dict | place |  | Theni | Theni |
| no | 0.42 | - | dict | group |  | Muslims | Muslim |

## Sriprakash Jaiswal: Regarding death of two villagers caused in Navgarh Block, Chandauli in Uttar Pradesh.

2002-07-31, 344 words, state `speech`. Speech id 391370.

**Summary.** Urges the government to immediately open food grain storehouses and provide relief in Uttar Pradesh, highlighting severe drought and reported starvation deaths.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Drought and agricultural crisis | पूर्वी उत्तर प्रदेश में सूखे की स्थिति *(not in text)* |
| yes | 0.99 | - | llm | topic |  | Starvation and food security | मौत भूख से होने का समाचार |
| yes | 0.97 | - | recognised (1, 0.38) | topic |  | Famine | Severe food shortage and starvation crisis. |
| no | 0.65 | - | recognised (2, 0.38) | institution |  | Food Corporation of India (FCI) | The government corporation that buys, stores, and distributes food grain in India. |
| no | 0.53 | - | recognised (3, 0.38) | institution |  | Department of Food and Public Distribution | A central government department responsible for the procurement, storage, and subsidised distribution of food grains. |
| yes | 0.99 | - | recognised (4, 0.39) | topic |  | Starvation | Severe food deprivation and hunger |
| yes | 0.94 | - | recognised (5, 0.39) | topic |  | Foodgrains | Cereal and other grain crops grown and stored for people to eat. |
| no | 0.51 | - | recognised (6, 0.39) | scheme |  | Public Distribution System (PDS) | Government system that supplies subsidised food grains to poor families. |
| no | 0.43 | - | recognised (7, 0.39) | institution |  | Ministry of Consumer Affairs, Food and Public Distribution | Union ministry overseeing consumer protection, food grains procurement, and public distribution systems. |
| yes | 0.99 | - | recognised (8, 0.39) | topic |  | Hunger | Condition of not having sufficient food for adequate nutrition. |
| yes | 0.95 | - | recognised (9, 0.39) | topic |  | Drought Relief | Government assistance to areas affected by drought conditions. |
| no | 0.03 | - | recognised (10, 0.40) | scheme |  | Pradhan Mantri Garib Kalyan Anna Yojana (PM-GKAY) | Government scheme that gave free food grains to poor families. |
| yes | 0.97 | - | recognised (11, 0.40) | place |  | Uttar Pradesh | Northern Indian state. |
| no | 0.06 | - | recognised (12, 0.40) | law |  | NATIONAL FOOD SECURITY ACT | Law guaranteeing subsidized food for poor households |
| yes | 1.00 | - | llm | place |  | Uttar Pradesh | उत्तर प्रदेश |
| yes | 0.98 | - | llm | institution |  | Food Corporation of India | एफ.सी.आई. |
| no | 0.77 | - | dict | place |  | Chandauli | चन्दौली |
| yes | 0.97 | - | dict | group |  | Farmers | किसान |

## Shivraj V. Patil: Discussion regarding disinvestment of Public Sector Undertakings. (Not concluded).

2002-08-01, 119 words, state `speech`. Speech id 391213.

**Summary.** Requests the House to accommodate members to continue the debate on public sector undertaking disinvestment despite the late hour.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.45 | - | llm | topic |  | Public sector undertakings disinvestment | disinvestment of Public Sector Undertakings *(not in text)* |
| no | 0.07 | - | recognised (1, 0.38) | topic |  | Adjournment Motions | A procedure to stop normal business and discuss an urgent matter. |
| no | 0.04 | - | recognised (2, 0.38) | law |  | Rule 193 | Lok Sabha procedural rule allowing members to raise discussions on matters of urgent public importance without formal voting. |
| no | 0.06 | - | recognised (3, 0.41) | topic |  | Parliamentary Zero Hour | A period in a parliament session for raising urgent matters. |
| no | 0.08 | - | recognised (4, 0.41) | topic |  | Privatisation of Visakhapatnam Steel Plant | Proposed sale of government equity and ownership in the public sector steel plant in Visakhapatnam. |
| no | 0.22 | - | recognised (5, 0.41) | topic |  | Public Sector Undertakings Revival | Financial restructuring and turnaround efforts for sick or loss-making government-owned enterprises. |
| no | 0.01 | - | recognised (6, 0.42) | topic |  | Special Category Status for Andhra Pradesh | Demand for preferential central financial assistance and tax concessions for Andhra Pradesh post-bifurcation. |
| no | 0.35 | - | recognised (7, 0.42) | topic |  | Short Duration Discussion | A brief parliamentary debate on one specific issue. |
| no | 0.07 | - | recognised (8, 0.42) | institution |  | Committee on Public Undertakings | Parliamentary committee that examines the reports, accounts, and operational efficiency of public sector enterprises. |
| no | 0.06 | - | recognised (9, 0.42) | topic |  | Parliamentary Disruptions | Interruptions, protests, and adjournments that halt official proceedings in legislative houses. |
| no | 0.02 | - | recognised (10, 0.43) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.09 | - | recognised (12, 0.43) | topic |  | Rule 184 | A specific rule that allows a parliamentary discussion with a vote. |
| no | 0.02 | - | recognised (13, 0.43) | topic |  | Development of North East | Socio-economic progress, connectivity enhancement, and infrastructure growth in India's northeastern states. |

## Shivraj V. Patil: Discussion on the Motion for Adjournment on the issue of failure of the Government in curbing the communal elements in the country, specially in Gujarat.

2002-11-18, 233 words, state `speech`. Speech id 390939.

**Summary.** Responds to incorrect facts presented in the House regarding communal issues and denies allegations against the party.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.90 | - | llm | topic |  | Communal situation | communal elements *(not in text)* |
| no | 0.03 | - | recognised (1, 0.40) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| yes | 0.87 | - | recognised (2, 0.40) | topic |  | Communalism | Politics based on religion. |
| yes | 0.86 | - | recognised (3, 0.41) | topic |  | Communal Riots | Violent conflict or tension between groups of different religions. |
| no | 0.03 | - | recognised (4, 0.41) | place |  | Ram Janma-bhumi Babri Masjid | Religious site disputed between communities |
| no | 0.51 | - | recognised (5, 0.41) | topic |  | Religious Minorities | Non-Hindu religious communities |
| no | 0.01 | - | recognised (6, 0.41) | topic |  | Naxalities | Violent communist movements operating in rural areas of India. |
| no | 0.01 | - | recognised (7, 0.41) | topic |  | Citizenship Amendment Act Protests | Nationwide public demonstrations and protests against the Citizenship (Amendment) Act of 2019. |
| no | 0.02 | - | recognised (8, 0.41) | topic |  | Manipur Violence | Incidents of ethnic conflict, social unrest, and displacement occurring among communities in Manipur. |
| no | 0.04 | - | recognised (9, 0.41) | institution |  | Janata Dal (United) | Indian political party primarily active in the state of Bihar. |
| yes | 0.80 | - | recognised (10, 0.42) | topic |  | Communal Harmony | Peace between different religious groups |
| no | 0.02 | - | recognised (11, 0.42) | topic |  | Sikhs | Sikh population and community issues |
| no | 0.02 | - | recognised (12, 0.42) | institution |  | Muslim League | Indian political party primarily based in Kerala, officially known as the Indian Union Muslim League. |
| yes | 1.00 | - | dict | place |  | Gujarat | Gujarat |

## Nawal Kishore Rai: Discussion on the Indian Medicine Central Council (Amendment) Bill, 2002. (Bill passed)

2002-11-26, 538 words, state `speech`. Speech id 390360.

**Summary.** Supports the Indian Medicine Central Council (Amendment) Bill, 2002, and urges the government to protect traditional Indian medicine systems and prevent the biopiracy of medicinal herbs.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Traditional medicine systems | भारतीय चिकित्सा पrति |
| yes | 0.89 | - | llm | topic |  | Biopiracy and patenting of medicinal herbs | पेटेन्टीकरण |
| no | 0.33 | - | recognised (1, 0.32) | law |  | National Commission for Indian System of Medicine Act | Indian act providing for the regulation of education and practice in traditional Indian medicine systems. |
| yes | 0.97 | - | recognised (2, 0.33) | institution |  | Central Council of Indian Medicine | Former statutory body that regulated higher education in Ayurveda, Siddha, Unani, and Sowa-Rigpa systems of medicine. |
| yes | 0.87 | - | recognised (3, 0.33) | law |  | Indian Medical Council (Amendment) Act | Indian act amending medical council legislation to reform governance and regulation of medical education. |
| no | 0.70 | - | recognised (4, 0.35) | topic |  | Ayurveda Education | Academic training, college standards, and syllabus development for the traditional Indian system of Ayurvedic medicine. |
| no | 0.75 | - | recognised (5, 0.35) | topic |  | Ayurveda | Traditional Indian system of medicine and wellness |
| no | 0.44 | - | recognised (6, 0.36) | law |  | Homoeopathy Central Council Act | Indian law regulating higher education, professional standards, and central registration for homoeopathic medical practice. |
| no | 0.79 | - | recognised (7, 0.36) | law |  | Indian Medical Council Act | Indian act establishing the Medical Council of India to regulate medical education and professional practice. |
| no | 0.21 | - | recognised (8, 0.36) | institution |  | AYUSH | System for traditional medicine |
| no | 0.64 | - | recognised (9, 0.36) | topic |  | Ayurveda Education and Research | Academic instruction, clinical training, and scientific investigation in the traditional Indian system of Ayurveda. |
| no | 0.15 | - | recognised (10, 0.36) | law |  | National Medical Commission Bill | Legislation regulating medical doctors and practice. |
| no | 0.04 | - | recognised (11, 0.36) | scheme |  | National AYUSH Mission | Central government scheme aimed at upgrading and promoting traditional systems of medicine across India. |
| yes | 0.97 | - | recognised (12, 0.36) | topic |  | Traditional Medicine | Medical practices based on indigenous knowledge systems |
| yes | 1.00 | - | llm | law |  | Indian Medicine Central Council (Amendment) Bill, 2002 | भारतीय चिकित्सा केन्pीय परिषद संशोधन विधेयक, 2002 |
| no | 0.09 | - | llm | person |  | Raj Narain | राज नारायण |
| no | 0.13 | - | dict | person |  | Akhilesh Yadav | अखिलेश जी |
| no | 0.13 | - | dict | group |  | Ayurveda | आयुर्वेद |
| no | 0.01 | - | dict | scheme |  | Aadhaar | आधार |

## Prahlad Singh Patel: Further consideration and passing of the Control of National Highways (Land And Traffic) Bill, 2002 moved by Maj. Gen. (Retd.) B.C. Khanduri, AVSM on 13 December, 2002 (Concluded).

2002-12-16, 430 words, state `speech`. Speech id 388980.

**Summary.** Supports the Control of National Highways (Land and Traffic) Bill, 2002, praising national highway expansion while highlighting issues regarding maintenance, signboards, and state government accountability.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | National highways maintenance and management | राषट्रीय राजमागा् पर |
| yes | 0.85 | - | recognised (1, 0.35) | topic |  | National Highway Expansion | Widening, upgrading, and acquiring land for India's national highway network. |
| no | 0.70 | - | recognised (2, 0.37) | institution |  | National Highways Authority of India (NHAI) | The government body that builds and manages India's national highways. |
| yes | 0.95 | - | recognised (3, 0.37) | topic |  | Highway Construction and Safety | Building and widening national highways alongside engineering measures to prevent road accidents. |
| no | 0.73 | - | recognised (4, 0.37) | institution |  | Ministry of Road Transport and Highways | Indian union ministry responsible for the development and maintenance of national highways and road transport systems. |
| no | 0.20 | - | recognised (5, 0.38) | scheme |  | National Highways Development Project | Major government project aimed at upgrading and widening key national highways across India. |
| yes | 0.89 | - | recognised (6, 0.38) | place |  | National Highways | Major roads managed by the central government connecting different regions. |
| no | 0.04 | - | recognised (7, 0.41) | place |  | National Highway 66 | Major national highway running parallel to India's western coast from Maharashtra to Tamil Nadu. |
| no | 0.03 | - | recognised (8, 0.41) | scheme |  | Delhi-Mumbai Expressway | A major access-controlled expressway connecting India's national capital Delhi with its financial hub Mumbai. |
| no | 0.03 | - | recognised (9, 0.41) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.79 | - | recognised (10, 0.41) | topic |  | Road Safety and Traffic Congestion | Measures to prevent traffic accidents and manage vehicular congestion on roads. |
| no | 0.03 | - | recognised (11, 0.41) | place |  | National Highway 16 | Major national highway running along the east coast of India from West Bengal to Tamil Nadu. |
| no | 0.02 | - | recognised (12, 0.42) | scheme |  | Bharatmala Pariyojana | Government program that builds and connects national highways. |
| yes | 1.00 | - | llm | law |  | Control of National Highways (Land and Traffic) Bill, 2002 | राषट्रीय राजमार्ग नियंत्रण विधेयक |
| yes | 0.74 | - | llm | place |  | Madhya Pradesh | मध्य प्रदेश |

## Mulayam Singh Yadav: Regarding delay in releasing MPLAD funds by the District Magistrate, Itawah, Uttar Pradesh.

2002-12-16, 249 words, state `speech`. Speech id 389057.

**Summary.** Complains about the delay in releasing MPLAD funds by the District Magistrate of Etawah and requests the matter be referred to the Privileges Committee.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | MPLAD funds release delay | सांसद एवं विधायक निधि रिलीज नहीं करेंगे |
| yes | 0.95 | - | recognised (1, 0.38) | place |  | Etawah | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.94 | - | recognised (2, 0.39) | scheme |  | MPLADS | Government scheme giving each member of parliament funds for local projects. |
| no | 0.36 | - | recognised (3, 0.40) | place |  | Etah | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.81 | - | recognised (4, 0.40) | topic |  | Question of Privilege | A formal complaint that parliament's rights have been breached. |
| no | 0.70 | - | recognised (5, 0.40) | institution |  | Privileges Committee | The Lok Sabha committee that handles breaches of a member's privilege. |
| no | 0.02 | - | recognised (6, 0.42) | place |  | Jhansi | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.04 | - | recognised (7, 0.42) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| yes | 0.86 | - | recognised (8, 0.42) | topic |  | Public Grievances | Complaints from citizens |
| no | 0.02 | - | recognised (9, 0.42) | place |  | Prayagraj | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Allahabad. |
| no | 0.03 | - | recognised (10, 0.42) | place |  | Lucknow | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.02 | - | recognised (11, 0.42) | place |  | Firozabad | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.02 | - | recognised (12, 0.42) | place |  | Pratapgarh (Uttar Pradesh) | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 1.00 | - | dict | place |  | Etawah | इटावा |
| yes | 0.95 | - | dict | role |  | Members of Legislative Assembly | विधायक |
| yes | 1.00 | - | dict | role |  | District Magistrate | डी.एम. |
| yes | 1.00 | - | dict | institution |  | Privilege Committee | विशेषाधिकार समिति |
| no | 0.01 | - | dict | institution |  | Election Commission of India | कमीशन |

## M. Jagannath: General discussion on the Budget (Railways)- 2003-2004, Demands for Grants on Account (Railways)- 2003-2004, Grants on Account (Railways)- 2003-2004, Supplementary Demand for Grants (Railways)- 2002-2003 and Demands for Excess Grants (Railways) for 2000-2001. (Not concluded)

2003-03-05, 1396 words, state `speech`. Speech id 387066.

**Summary.** Supports the Railway Budget while calling for increased financial allocations for railway safety improvements, unmanned railway crossings, and new lines in Andhra Pradesh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Railway safety | avoid accidents from taking place |
| yes | 0.98 | - | llm | topic |  | Railway budget allocations | allocations made by the Railways |
| yes | 0.97 | - | recognised (1, 0.33) | law |  | Railway Budget | Annual government allocation for railway operations and development. |
| no | 0.05 | - | recognised (2, 0.36) | topic |  | Railway Budget Merger | Decision taken in 2016 to merge the separate railway budget into the general Union budget. |
| no | 0.03 | - | recognised (3, 0.36) | topic |  | Special Category Status for Andhra Pradesh | Demand for preferential central financial assistance and tax concessions for Andhra Pradesh post-bifurcation. |
| yes | 0.96 | - | recognised (4, 0.37) | institution |  | South Central Railway | Zone of Indian Railways headquartered at Secunderabad, serving parts of Telangana, Andhra Pradesh, and nearby states. |
| no | 0.70 | - | recognised (5, 0.37) | topic |  | Railway Finances | Financial management, capital expenditure, budget allocation, and funding of Indian Railways. |
| no | 0.06 | - | recognised (6, 0.37) | institution |  | Standing Committee on Railways | Parliamentary body that examines policies, budgets, and operational performance of the Indian Railways. |
| no | 0.70 | - | recognised (7, 0.37) | topic |  | Rail Connectivity and Overbridge Construction | Expansion of railway networks and building overbridges or underpasses to improve road and rail traffic. |
| no | 0.15 | - | recognised (8, 0.37) | institution |  | South Coast Railway Zone | Proposed zone of Indian Railways to be headquartered in Visakhapatnam, Andhra Pradesh. |
| no | 0.04 | - | recognised (9, 0.38) | scheme |  | Rashtriya Rail Sanraksha Kosh | Dedicated government fund created to finance safety-related works across Indian Railways. |
| no | 0.42 | - | recognised (10, 0.38) | topic |  | Railway Modernisation | Upgrading rail infrastructure, rolling stock, signaling, and technology across Indian Railways. |
| yes | 0.97 | - | recognised (11, 0.39) | topic |  | Railway Safety | Measures to ensure safe railway operations. |
| no | 0.02 | - | recognised (12, 0.40) | scheme |  | Kavach | Indigenous automatic train protection system developed by Indian Railways to prevent collisions. |
| yes | 0.99 | - | llm | place |  | Andhra Pradesh | Andhra Pradesh |
| yes | 1.00 | - | llm | institution |  | South Central Railway Zone | South Central Railway Zone |
| no | 0.50 | - | dict | law |  | Union Budget | Budget |
| yes | 1.00 | - | dict | place |  | Raichur | Raichur |
| yes | 0.86 | - | dict | institution |  | Ministry of Railways | Railway Minister |
| yes | 1.00 | - | dict | place |  | Nalgonda | Nalgonda |
| yes | 1.00 | - | dict | place |  | Kacheguda | Kacheguda |
| yes | 1.00 | - | dict | institution |  | South Central Railway | South Central Railway |
| yes | 0.98 | - | dict | place |  | Gadwal | Gadwal |
| yes | 1.00 | - | dict | place |  | Kurnool | Kurnool |

## Maheshwar Singh: General discussion on the Budget (Railways)- 2003-2004, Demands for Grants on Account (Railways)- 2003-2004, Grants on Account (Railways)- 2003-2004, Supplementary Demand for Grants (Railways)- 2002-2003 and Demands for Excess Grants (Railways) for 2000-2001. (Not concluded)

2003-03-05, 1291 words, state `speech`. Speech id 387083.

**Summary.** Supports the Railway Budget and urges the government to expedite railway projects, gauge conversion, and overbridge construction in Himachal Pradesh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Rail connectivity | रेल लाइन |
| yes | 0.98 | - | llm | topic |  | Railway budget | रेल बजट |
| yes | 0.89 | - | llm | topic |  | Gauge conversion | आमान परिवर्तन |
| yes | 0.93 | - | llm | topic |  | Railway overbridge | उपरिगामी पुल |
| no | 0.31 | - | llm | topic |  | Alternative fuels | वैकल्पिक ईंधन |
| yes | 0.94 | - | recognised (1, 0.33) | law |  | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.97 | - | recognised (2, 0.34) | topic |  | Rail Connectivity and Overbridge Construction | Expansion of railway networks and building overbridges or underpasses to improve road and rail traffic. |
| no | 0.05 | - | recognised (3, 0.35) | topic |  | Railway Budget Merger | Decision taken in 2016 to merge the separate railway budget into the general Union budget. |
| no | 0.03 | - | recognised (4, 0.37) | institution |  | Standing Committee on Railways | Parliamentary body that examines policies, budgets, and operational performance of the Indian Railways. |
| no | 0.64 | - | recognised (5, 0.38) | topic |  | Railway Finances | Financial management, capital expenditure, budget allocation, and funding of Indian Railways. |
| no | 0.44 | - | recognised (6, 0.38) | topic |  | Railway Modernisation | Upgrading rail infrastructure, rolling stock, signaling, and technology across Indian Railways. |
| no | 0.08 | - | recognised (7, 0.39) | topic |  | Development of North East | Socio-economic progress, connectivity enhancement, and infrastructure growth in India's northeastern states. |
| no | 0.32 | - | recognised (8, 0.39) | place |  | Shimla | District and Lok Sabha constituency in Himachal Pradesh, India. |
| no | 0.04 | - | recognised (9, 0.39) | place |  | Hamirpur (Himachal Pradesh) | District and Lok Sabha constituency in Himachal Pradesh, India. |
| no | 0.09 | - | recognised (10, 0.39) | place |  | Kangra | District and Lok Sabha constituency in Himachal Pradesh, India. |
| yes | 0.96 | - | recognised (11, 0.40) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| yes | 0.94 | - | recognised (12, 0.40) | topic |  | Rail and Road Connectivity | Expansion and coordination of railway networks and road systems to improve transportation. |
| yes | 1.00 | - | llm | place |  | Himachal Pradesh | हिमाचल |
| no | 0.24 | - | llm | institution |  | NTPC | एन.टी.पी.सी. |
| yes | 0.60 | - | llm | institution |  | Indian Oil Corporation | इण्डियन ऑयल कारपोरेशन |
| yes | 1.00 | - | llm | place |  | Joginder Nagar | जोगेन्p नगर |
| yes | 1.00 | - | llm | place |  | Pathankot | पठानकोट |
| yes | 0.75 | - | llm | place |  | Kalka | कालका |
| no | 0.19 | - | llm | place |  | Shimla | शिमला |
| no | 0.10 | - | llm | place |  | Nabinagar | नवीनगर |
| yes | 0.95 | - | dict | person |  | Nitish Kumar | नीतीश कुमार |
| no | 0.18 | - | dict | scheme |  | Pragati | प्रगति |
| yes | 0.96 | - | dict | place |  | Manali | मनाली |
| yes | 0.81 | - | dict | person |  | Digvijaya Singh | दिग्विजय सिंह |
| yes | 0.97 | - | dict | institution |  | Ministry of Railways | रेल मंत्री |
| yes | 0.99 | - | dict | group |  | Government officials | अधिकारियों |
| yes | 1.00 | - | dict | institution |  | Public Works Department | लोक निर्माण विभाग |
| yes | 0.98 | - | dict | place |  | Firozpur | फिरोजपुर |

## Shivraj V. Patil: Need to pass a unanimous resolution to make India’s stand clear on the issue of waging a war by the U.S.A. and the U.K. againt Iraq.

2003-03-10, 585 words, state `speech`. Speech id 386740.

**Summary.** Asks the Government of India to make an unambiguous statement and clarify its stand on the impending war against Iraq.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | International relations | waging a war by the U.S.A. and the U.K. againt Iraq *(not in text)* |
| yes | 0.99 | - | llm | topic |  | Foreign policy | stand of the Government of India |
| no | 0.56 | - | recognised (1, 0.39) | topic |  | Indo-Iraq Relations | Relations between India and Iraq. |
| no | 0.70 | - | recognised (2, 0.41) | topic |  | Non-alignment | A policy of staying independent from military and political blocs. |
| no | 0.68 | - | recognised (3, 0.42) | institution |  | Non Aligned Movement (NAM) | Group of nations not allied to major powers. |
| no | 0.01 | - | recognised (4, 0.42) | person |  | Rajiv Gandhi | Former Prime Minister of India |
| no | 0.61 | - | recognised (6, 0.42) | institution |  | Non-Aligned Movement | A group of countries that stay independent of major power blocs. |
| yes | 0.98 | - | recognised (7, 0.42) | topic |  | Foreign Relations | The state of diplomatic contact between India and other countries. |
| no | 0.39 | - | recognised (8, 0.42) | place |  | Middle East | Region west of India that includes the Gulf countries and nearby nations. |
| no | 0.07 | - | recognised (9, 0.42) | law |  | Rule 193 | Lok Sabha procedural rule allowing members to raise discussions on matters of urgent public importance without formal voting. |
| no | 0.39 | - | recognised (10, 0.43) | institution |  | Ministry Of External Affairs | Indian government ministry that manages relations with other countries. |
| no | 0.03 | - | recognised (12, 0.43) | law |  | Bilateral Agreements | Treaties between India and other nations |
| no | 0.04 | - | recognised (13, 0.43) | institution |  | Standing Committee on External Affairs | Parliamentary body that examines policies, legislation, and budgets related to India's foreign affairs. |
| no | 0.02 | - | recognised (14, 0.43) | law |  | Nehru-Liaquat Pact | Bilateral treaty between India and Pakistan regarding the rights and protection of religious minorities. |
| yes | 0.95 | - | dict | place |  | Malaysia | Malaysia |
| yes | 0.98 | - | dict | institution |  | United Nations | United Nations |
| yes | 0.99 | - | dict | group |  | Ministers | Ministers |
| yes | 1.00 | - | dict | place |  | Iraq | Iraq |

## Renu Kumari Singh: Notice of question of privilege against the Director General of Police, Bihar, for his alleged discourteous behaviour towards the Member Smt. Renu Kumari.

2003-03-13, 182 words, state `speech`. Speech id 386275.

**Summary.** Raises a question of privilege against the Bihar Director General of Police for discourteous behavior towards a Member of Parliament.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Privilege motion against police official | विशेषाधिकार हनन का नोटिस |
| yes | 0.98 | - | recognised (1, 0.39) | topic |  | Question of Privilege | A formal complaint that parliament's rights have been breached. |
| no | 0.05 | - | recognised (2, 0.41) | place |  | Darbhanga | District and Lok Sabha constituency in Bihar, India. |
| no | 0.10 | - | recognised (3, 0.41) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| no | 0.12 | - | recognised (4, 0.42) | law |  | Rule 374 | Lok Sabha procedural rule empowering the Speaker to suspend members who disregard the authority of the Chair. |
| no | 0.16 | - | recognised (5, 0.42) | institution |  | Privileges Committee | The Lok Sabha committee that handles breaches of a member's privilege. |
| no | 0.05 | - | recognised (6, 0.42) | place |  | Bhagalpur | District and Lok Sabha constituency in Bihar, India. |
| no | 0.05 | - | recognised (7, 0.42) | place |  | West Champaran | District and Lok Sabha constituency in Bihar, India. The constituency is listed as Paschim Champaran. |
| no | 0.04 | - | recognised (8, 0.42) | place |  | Gopalganj | District and Lok Sabha constituency in Bihar, India. |
| no | 0.68 | - | recognised (9, 0.42) | topic |  | MP(s) Conduct | Behavior and ethics of parliament members |
| no | 0.03 | - | recognised (10, 0.42) | place |  | Patna Sahib | Lok Sabha constituency in Bihar, India. |
| no | 0.05 | - | recognised (11, 0.42) | place |  | Aurangabad (Bihar) | District and Lok Sabha constituency in Bihar, India. |
| no | 0.04 | - | recognised (12, 0.42) | place |  | Muzaffarpur | District and Lok Sabha constituency in Bihar, India. |
| yes | 1.00 | - | llm | person |  | D. P. Ojha | श्री डी.पी. ओझा |
| yes | 1.00 | - | llm | place |  | Bihar | बिहार |
| yes | 0.96 | - | dict | group |  | Police | पुलिस |
| no | 0.15 | - | dict | institution |  | Supreme Court | कोर्ट |

## Mulayam Singh Yadav: Regarding suspension of Question Hour to discuss the situation in Iraq and pass a unanimous resolution condemning the military action on Iraq by the USA – led coalition forces.

2003-04-08, 599 words, state `speech`. Speech id 386102.

**Summary.** Condemns the US-led military action against Iraq, expresses serious concern over threats to India, and urges the government to send humanitarian aid to Iraq through the United Nations.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Military action against Iraq | इराक पर अमरीका द्वारा जो हमला हुआ |
| yes | 0.92 | - | llm | topic |  | Indian foreign policy and national security | विदेश नीति |
| no | 0.48 | - | recognised (1, 0.41) | topic |  | Indo-Iraq Relations | Relations between India and Iraq. |
| no | 0.02 | - | recognised (2, 0.42) | person |  | Rajiv Gandhi | Former Prime Minister of India |
| yes | 0.85 | - | recognised (3, 0.43) | place |  | India | Sovereign nation in South Asia |
| no | 0.01 | - | recognised (4, 0.43) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.04 | - | recognised (5, 0.43) | institution |  | United Progressive Alliance | Coalition of Indian political parties formed in 2004 and led by the Indian National Congress. |
| no | 0.04 | - | recognised (6, 0.43) | institution |  | INDIA Alliance | Coalition of Indian opposition political parties formed to contest national elections against the ruling alliance. |
| yes | 0.98 | - | recognised (8, 0.43) | place |  | Iraq | Middle Eastern country. |
| no | 0.01 | - | recognised (9, 0.44) | topic |  | Operation Ganga | Government evacuation that brought Indian citizens home from Ukraine. |
| no | 0.01 | - | recognised (10, 0.44) | law |  | Nehru-Liaquat Pact | Bilateral treaty between India and Pakistan regarding the rights and protection of religious minorities. |
| no | 0.03 | - | recognised (11, 0.44) | institution |  | Standing Committee on External Affairs | Parliamentary body that examines policies, legislation, and budgets related to India's foreign affairs. |
| no | 0.07 | - | recognised (13, 0.44) | place |  | New Delhi | District and Lok Sabha constituency in Delhi, India. |
| no | 0.01 | - | recognised (14, 0.44) | institution |  | Standing Committee on Human Resource Development | Parliamentary body that examined policies, legislation, and budgets related to education and human resource development in India. |
| yes | 1.00 | - | llm | place |  | Iraq | इराक |
| yes | 1.00 | - | llm | place |  | United States | अमरीका |
| yes | 0.99 | - | llm | place |  | Pakistan | पाकिस्तान |
| yes | 0.92 | - | llm | place |  | Jammu and Kashmir | जम्मू-काश्मीर |
| yes | 0.97 | - | llm | institution |  | United Nations | संयुक्त राषठ्र संघ |
| yes | 1.00 | - | dict | group |  | Opposition | विपक्ष |
| no | 0.02 | - | dict | institution |  | Aaj Tak | आज तक |
| no | 0.67 | - | dict | person |  | Vijay Kumar Malhotra | विजय कुमार मल्होत्रा |

## Somnath Chatterjee: Regarding notices of motion for adjournment on the issue of filing of charge-sheet by CBI in Ayodhya case (The Speaker disallowed the notices and gave his ruling).

2003-07-23, 67 words, state `speech`. Speech id 384066.

**Summary.** Argues that the proviso about the Speaker lacking full facts does not apply, so the adjournment notices should not have been disallowed on that basis.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.95 | - | llm | topic |  | Disallowing of adjournment notices | This proviso does not apply here. |
| yes | 0.84 | - | recognised (1, 0.38) | topic |  | Adjournment Motions | A procedure to stop normal business and discuss an urgent matter. |
| no | 0.44 | - | recognised (3, 0.41) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| no | 0.45 | - | recognised (4, 0.41) | topic |  | Rule 184 | A specific rule that allows a parliamentary discussion with a vote. |
| no | 0.51 | - | recognised (5, 0.41) | law |  | Rule 193 | Lok Sabha procedural rule allowing members to raise discussions on matters of urgent public importance without formal voting. |
| no | 0.41 | - | recognised (6, 0.42) | law |  | Rule 56 | Parliamentary procedure rule |
| no | 0.01 | - | recognised (7, 0.42) | topic |  | Demands For Grants | A parliamentary process for approving government spending plans. |
| no | 0.05 | - | recognised (8, 0.42) | topic |  | Parliamentary Zero Hour | A period in a parliament session for raising urgent matters. |
| no | 0.53 | - | recognised (11, 0.43) | topic |  | Speaker's Impartiality | Principle requiring the presiding officer of the Lok Sabha to act fairly and without political bias. |
| no | 0.43 | - | recognised (12, 0.43) | law |  | Rule 374 | Lok Sabha procedural rule empowering the Speaker to suspend members who disregard the authority of the Chair. |
| no | 0.44 | - | recognised (13, 0.43) | topic |  | Observation | A formal note made by parliament on a matter. |
| no | 0.36 | - | recognised (14, 0.43) | topic |  | Parliamentary Disruptions | Interruptions, protests, and adjournments that halt official proceedings in legislative houses. |
| no | 0.02 | - | recognised (15, 0.43) | topic |  | Bills Pending | Proposed laws still waiting for a decision by parliament. |

## Priya Ranjan Dasmunsi: Notices of Adjourment motion and suspension of Question Hour on the issue of the Prime Minister’s statement at Ayodhya on 1 August, 2003 regarding construction of Ram Temple to which the Prime Minister responded (Motion rejected by the Speaker).

2003-08-04, 1017 words, state `speech`. Speech id 383274.

**Summary.** Criticises the Prime Minister for making a statement regarding the construction of the Ram Temple at Ayodhya during the session of the House, questioning the credibility of government statements.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Ram Temple construction and Ayodhya dispute | Ram Janmabhoomi will have the temple |
| yes | 0.93 | - | llm | topic |  | Government policy credibility | durability and credibility of the Prime Minister’s statement *(not in text)* |
| yes | 0.96 | - | recognised (1, 0.39) | place |  | Ayodhya | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Faizabad. |
| no | 0.05 | - | recognised (2, 0.40) | law |  | Rule 353 | Lok Sabha procedural rule regarding advance notice required before making defamatory allegations against individuals. |
| no | 0.05 | - | recognised (3, 0.40) | law |  | Rule 193 | Lok Sabha procedural rule allowing members to raise discussions on matters of urgent public importance without formal voting. |
| yes | 0.92 | - | recognised (4, 0.41) | place |  | Ram Janma-bhumi Babri Masjid | Religious site disputed between communities |
| no | 0.01 | - | recognised (6, 0.41) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| yes | 0.92 | - | recognised (7, 0.42) | place |  | Ram Temple | Religious shrine and pilgrimage site in Ayodhya. |
| no | 0.02 | - | recognised (9, 0.42) | place |  | Gorakhpur | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.52 | - | recognised (12, 0.42) | topic |  | Parliamentary Questions | Questions that members ask the government about its work. |
| no | 0.02 | - | recognised (13, 0.42) | topic |  | Mann Ki Baat | Monthly radio address delivered by the Prime Minister of India to engage citizens on national matters. |
| no | 0.03 | - | recognised (14, 0.42) | institution |  | Liberhan Commission | Commission investigating riots in Ayodhya. |
| no | 0.06 | - | recognised (16, 0.43) | topic |  | Parliamentary Zero Hour | A period in a parliament session for raising urgent matters. |
| no | 0.01 | - | recognised (17, 0.43) | topic |  | Citizenship Amendment Act Protests | Nationwide public demonstrations and protests against the Citizenship (Amendment) Act of 2019. |
| yes | 1.00 | - | llm | place |  | Ayodhya | Ayodhya |
| yes | 0.97 | - | llm | person |  | Mahant Ramachandra Das Paramhans | Mahant Ramachandra Das Paramhans |
| no | 0.02 | - | llm | person |  | Graham Steins | Graham Steins |
| yes | 0.50 | - | llm | institution |  | Bharatiya Janata Party | BJP |
| yes | 0.59 | - | llm | institution |  | National Democratic Alliance | NDA |
| yes | 1.00 | - | dict | role |  | Leader of the House | Leader of the House |
| yes | 1.00 | - | dict | place |  | Ram Janmabhoomi | Ram Janmabhoomi |
| no | 0.02 | - | dict | group |  | Unemployed youth | unemployed youth |
| no | 0.18 | - | dict | group |  | Terrorists | terrorists |
| no | 0.02 | - | dict | group |  | Farmers | farming community |
| no | 0.11 | - | dict | place |  | Gujarat | Gujarat |
| no | 0.56 | - | dict | institution |  | Supreme Court | court |

## Gulam Mehmood Banatwalla: Regarding imposition of common test on the minority educational institutions for admissions by U.G.C.

2003-12-15, 190 words, state `speech`. Speech id 380875.

**Summary.** Opposes the imposition of common entrance tests by the UGC on minority educational institutions, arguing it violates minority rights protected by the Constitution.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Minority education rights | minority educational institutions |
| yes | 0.97 | - | llm | topic |  | University admissions | admission of the students |
| yes | 0.93 | - | recognised (1, 0.35) | topic |  | Religious Minorities | Non-Hindu religious communities |
| no | 0.05 | - | recognised (2, 0.35) | institution |  | Minorities Commission | A government body that protects the rights of minority communities in India. |
| yes | 0.92 | - | recognised (3, 0.35) | topic |  | Minority Welfare | Socio-economic development, constitutional rights, and protective measures for recognized minority communities in India. |
| yes | 0.98 | - | recognised (4, 0.36) | topic |  | Minority Education | Educational access, institutions, and policies for religious and linguistic minority groups in India. |
| no | 0.58 | - | recognised (5, 0.36) | law |  | Minorities Protection | Laws protecting minority community rights |
| no | 0.07 | - | recognised (6, 0.37) | law |  | Right to Education | Constitutional right to education. |
| no | 0.02 | - | recognised (7, 0.37) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.07 | - | recognised (8, 0.37) | institution |  | Ministry of Minority Affairs | Indian union ministry responsible for programmes and policies benefiting religious minority communities. |
| yes | 0.97 | - | recognised (9, 0.38) | institution |  | Minority Institutions | Schools managed by minority religious groups |
| no | 0.01 | - | recognised (10, 0.38) | law |  | Citizens Amendment Act (CAA) | Law amending citizenship provisions for religious minorities from neighboring countries. |
| no | 0.02 | - | recognised (11, 0.38) | scheme |  | Minority Scholarships | Government financial aid programmes supporting students from religious minority communities for schooling and higher education. |
| no | 0.02 | - | recognised (12, 0.38) | institution |  | Ranganath Misra Commission | National Commission for Religious and Linguistic Minorities set up in 2004. |
| yes | 1.00 | - | llm | institution |  | University Grants Commission | University Grants Commission |
| yes | 0.77 | - | llm | institution |  | Aligarh Muslim University | Aligarh Muslim University |
| yes | 1.00 | - | llm | law |  | Article 30 of the Constitution of India | article 30 of the Constitution |
| yes | 0.97 | - | dict | group |  | Students | students |

## Digvijay Singh: Motion for considerationof the amendments made by Rajya Sabha to the Indian Council of World Affairs (Amendment) Bill, 2003. (Motion adopted and the amendments made by Rajya Sabha were agreed to).

2003-12-22, 710 words, state `speech`. Speech id 380004.

**Summary.** Supports the amendments made by Rajya Sabha to the Indian Council of World Affairs (Amendment) Bill, 2003.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.94 | - | llm | topic |  | Foreign policy and international relations | विदेश नीति |
| no | 0.79 | - | recognised (2, 0.37) | institution |  | Rajya Sabha | Upper chamber of Indian parliament representing states. |
| no | 0.01 | - | recognised (3, 0.37) | law |  | National Investigation Agency (Amendment) Act | Act expanding the National Investigation Agency's jurisdiction to investigate offences committed outside India. |
| no | 0.01 | - | recognised (4, 0.37) | law |  | Indian Medical Council (Amendment) Act | Indian act amending medical council legislation to reform governance and regulation of medical education. |
| no | 0.01 | - | recognised (5, 0.38) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.01 | - | recognised (6, 0.38) | law |  | Arbitration and Conciliation (Amendment) Act | Indian amending legislation updating arbitration and conciliation procedures to ensure speedy dispute resolution and attract investment. |
| no | 0.02 | - | recognised (8, 0.38) | law |  | Constitution (One Hundred and Thirty-First Amendment) Bill | Proposed amendment to the Constitution of India introduced in parliament. |
| no | 0.01 | - | recognised (9, 0.38) | law |  | Central Universities (Amendment) Act | Act amending legislation that governs the establishment and operation of central universities across India. |
| no | 0.01 | - | recognised (10, 0.38) | law |  | Land Acquisition Act, Fair Compensation and Transparency | Proposed legislative amendment to modify consent requirements and procedures for acquiring land in India. |
| no | 0.01 | - | recognised (11, 0.38) | law |  | Insurance Laws (Amendment) Act | Indian act amending insurance legislation to permit increased foreign direct investment and update regulations. |
| no | 0.01 | - | recognised (12, 0.38) | law |  | New Delhi International Arbitration Centre Act | Act establishing an autonomous institution to facilitate institutional arbitration and conciliation. |
| no | 0.01 | - | recognised (13, 0.38) | law |  | Delhi Special Police Establishment (Amendment) Act | An Indian act amending the tenure and appointment provisions for the Central Bureau of Investigation director. |
| no | 0.03 | - | recognised (14, 0.39) | law |  | Bilateral Agreements | Treaties between India and other nations |
| yes | 0.99 | - | llm | law |  | Indian Council of World Affairs (Amendment) Bill, 2003 | इंडियन काऊंसिल ऑफ वर्ल्ड अफेयर्स |
| yes | 0.48 | - | llm | institution |  | Supreme Court | सुप्रीम कोर्ट |
| yes | 0.96 | - | llm | institution |  | Rajya Sabha | राज्य सभा |
| no | 0.02 | - | dict | person |  | Jawaharlal Nehru | पंडित जवाहर लाल नेहरु |
| yes | 0.95 | - | dict | institution |  | Ministry of External Affairs | Ministry of External Affairs |
| yes | 0.82 | - | dict | role |  | Director | Director |
| no | 0.07 | - | dict | scheme |  | Disha | दिशा |
| no | 0.64 | - | dict | place |  | Asia | एशिया |
| no | 0.37 | - | dict | group |  | Judges | न्यायाधीश |

