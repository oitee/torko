# Relevance check review: LS17_sample30

Model `jev-1.13.0`, questions `q5`, written on 2026-10-17. 30 speeches. For a topic or a recognised tag, `P(keep)` is P(a main or supporting subject). For a named item, `P(keep)` is P(part of the member's point). An `llm` item is kept at 0.4, a `dict` or `recognised` item at 0.8. `P(refers)` and `Model type` exist only for rows that question version q4 judged. `Source`: `llm` = the extraction, `dict` = the entity dictionary found the words in the text, `recognised` = a recognised tag, near the summary in meaning (its rank and distance in brackets). Write keep or drop in the `review` column of `LS17_sample30_jev-1.13.0_q5_2026-10-17.tsv`. 0 items carry an earlier manual mark already.

## Vinod Kumar Sonkar: Regarding need to frame a national policy for impounded vehicles kept in police stations for violation of traffic rules-laid

2023-12-20, 198 words, state `speech`. Speech id 311914.

**Summary.** Demands a national policy for the disposal and release of impounded vehicles rotting in police stations across the country.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Impounded vehicles policy | जब्त किए गए वाहनों के संबंध में राष्ट्रीय नीति |
| yes | 0.88 | - | llm | topic |  | Resource waste management | देश की बहुत बड़ी संपत्ति बर्बाद हो रही है |
| no | 0.02 | - | recognised (1, 0.41) | law |  | Drug Policy | Laws on drugs. |
| yes | 0.89 | - | recognised (2, 0.41) | topic |  | Goods Seized | Merchandise confiscated in law enforcement |
| no | 0.58 | - | recognised (3, 0.41) | topic |  | Police reforms | Changes to law enforcement practices. |
| no | 0.14 | - | recognised (4, 0.41) | topic |  | Hoarding | Stockpiling goods unfairly |
| no | 0.02 | - | recognised (5, 0.41) | topic |  | Police Atrocities | Excessive or illegal use of force by police. |
| no | 0.56 | - | recognised (6, 0.41) | law |  | National Design Policy | Government framework for industrial design standards |
| no | 0.76 | - | recognised (7, 0.42) | topic |  | Police Custody | Detention of persons by police pending investigation or legal proceedings. |
| no | 0.03 | - | recognised (8, 0.42) | scheme |  | Voluntary Auto Scrapping Policy | Government incentive that encourages recycling old vehicles to cut emissions. |
| no | 0.02 | - | recognised (9, 0.42) | topic |  | Police Brutality | Excessive force by law enforcement. |
| no | 0.12 | - | recognised (10, 0.43) | topic |  | Obsolete Law | Laws no longer enforced or relevant. |
| no | 0.28 | - | recognised (11, 0.43) | law |  | Motor Vehicles Act | Law regulating vehicle operation, safety, and traffic rules. |
| yes | 0.93 | - | recognised (12, 0.43) | institution |  | Police Stations | Local law enforcement outposts. |

## Nama Nageswara Rao: Motion of No-Confidence in the Council of Ministers- Contd.

2023-08-09, 372 words, state `speech`. Speech id 315393.

**Summary.** Criticises the Home Minister for making false claims regarding infrastructural projects and political alliances in Bihar and Jammu and Kashmir.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.96 | - | llm | topic |  | Infrastructural development claims | मेडिकल कॉलेज |
| yes | 0.73 | - | llm | topic |  | Political alliances | गठबंधन |
| no | 0.03 | - | recognised (1, 0.36) | institution |  | Hurriyat Conference | An alliance of separatist political groups based in Jammu and Kashmir. |
| no | 0.02 | - | recognised (2, 0.39) | place |  | Udhampur | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.52 | - | recognised (3, 0.40) | place |  | Jammu | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.04 | - | recognised (4, 0.40) | institution |  | National Conference | Political party in Kashmir and Jammu region |
| no | 0.05 | - | recognised (5, 0.40) | place |  | Srinagar | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.67 | - | recognised (6, 0.40) | place |  | Jammu & Kashmir | State in the northern region of India. |
| no | 0.03 | - | recognised (7, 0.41) | place |  | Anantnag–Rajouri | Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.02 | - | recognised (8, 0.41) | place |  | Muzaffarpur | District and Lok Sabha constituency in Bihar, India. |
| no | 0.02 | - | recognised (9, 0.41) | place |  | Kathua | District in Jammu and Kashmir, India. |
| yes | 0.94 | - | recognised (10, 0.41) | topic |  | Development Projects | Government initiatives for infrastructure. |
| no | 0.03 | - | recognised (11, 0.41) | topic |  | Fake Encounters | Falsely reported violent confrontations causing death during law enforcement. |
| no | 0.02 | - | recognised (12, 0.41) | place |  | Hajipur | Lok Sabha constituency in Bihar, India. |
| yes | 0.92 | - | llm | place |  | Jammu and Kashmir | जम्मू - कश्मीर |
| yes | 0.99 | - | llm | place |  | Bihar | बिहार |
| yes | 0.98 | - | llm | person |  | Mehbooba Mufti | महबूबा मुफ्ती |
| yes | 0.99 | - | dict | place |  | Munger | मुंगेर |
| yes | 1.00 | - | dict | person |  | Narendra Modi | मोदी जी |
| yes | 0.95 | - | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| yes | 0.98 | - | dict | place |  | Lakhisarai | लखीसराय |
| yes | 0.99 | - | dict | scheme |  | Jal Jeevan Mission | हर घर नल से जल |
| yes | 0.93 | - | dict | place |  | Jammu | जम्मू |
| yes | 0.95 | - | dict | place |  | Purnia | पूर्णिया |
| no | 0.68 | - | dict | person |  | Lalu Prasad Yadav | लालू जी |

## Nishikant Dubey: Motion of Thanks on the President's Address

2023-02-07, 182 words, state `speech`. Speech id 320101.

**Summary.** Questions the opposition parties about past corruption cases and political vendetta.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.88 | - | llm | topic |  | Political corruption | घोटाला |
| no | 0.10 | - | recognised (1, 0.39) | topic |  | CBI Inquiry | Investigation by Central Bureau of Investigation. |
| no | 0.06 | - | recognised (2, 0.40) | institution |  | CBI | India's federal agency that investigates serious and corruption-related crimes. |
| no | 0.07 | - | recognised (3, 0.40) | topic |  | 2G Spectrum Scam | Corruption in wireless spectrum allocation. |
| no | 0.55 | - | recognised (4, 0.42) | topic |  | Criminalisation of Politics | Involvement of persons with criminal records in political activities. |
| no | 0.77 | - | recognised (5, 0.42) | topic |  | Corruption | Illegal and unethical conduct by government officials or public servants. |
| no | 0.03 | - | recognised (6, 0.42) | institution |  | Lokpal | Ombudsman investigating corruption. |
| no | 0.16 | - | recognised (7, 0.42) | topic |  | Cash-for-vote Scam | Corruption in voting. |
| no | 0.08 | - | recognised (8, 0.42) | topic |  | Parliamentary Questions | Questions that members ask the government about its work. |
| yes | 0.94 | - | recognised (9, 0.42) | topic |  | Political Opposition | Parties and groups opposing government. |
| no | 0.03 | - | recognised (10, 0.42) | topic |  | Operation Green Hunt | Counterinsurgency campaign against Maoist militants |
| no | 0.06 | - | recognised (11, 0.43) | institution |  | Liberhan Commission | Commission investigating riots in Ayodhya. |
| no | 0.03 | - | recognised (12, 0.43) | institution |  | Lokayuktas | Anti-corruption authority in states |
| yes | 0.77 | - | llm | scheme |  | Bofors scandal | बोफोर्स का घोटाला |
| no | 0.76 | - | dict | institution |  | Supreme Court | कोर्ट |
| no | 0.69 | - | dict | person |  | Mahatma Gandhi | गांधी |

## Gopal Chinayya Shetty: Regarding High Petro/Diesel Prices in Sri Ganga Nagar, Rajasthan.

2022-12-20, 1640 words, state `speech`. Speech id 321953.

**Summary.** Supports government initiatives to combat drug abuse and urges community involvement and de-addiction efforts rather than relying solely on penal measures.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Drug abuse | मादक द्रव्यों के सेवन |
| yes | 0.94 | - | llm | topic |  | Law enforcement | स्वापक नियंत्रण ब्यूरो |
| yes | 0.80 | - | llm | topic |  | De-addiction | नशामुक्त करने |
| yes | 0.85 | - | recognised (1, 0.34) | topic |  | Drug De-addiction | Treatment programs for persons dependent on addictive substances. |
| no | 0.71 | - | recognised (2, 0.36) | law |  | Drug Policy | Laws on drugs. |
| yes | 0.97 | - | recognised (3, 0.37) | topic |  | Drug Addiction | Harmful, repeated use of drugs and the resulting dependence. |
| no | 0.71 | - | recognised (4, 0.39) | topic |  | Rehabilitation | Support programs to help people recover from disasters or other hardships. |
| yes | 0.98 | - | recognised (5, 0.39) | topic |  | Narcotics | Illegal drugs and substance abuse control measures. |
| no | 0.02 | - | recognised (6, 0.40) | topic |  | SCs and STs welfare | Support for scheduled communities |
| yes | 0.88 | - | recognised (7, 0.40) | institution |  | Anti Narcotic Task Force | Organization combating illegal drug production and trafficking. |
| yes | 0.84 | - | recognised (8, 0.40) | institution |  | Narcotics Control Bureau | Agency enforcing drug control and prevention. |
| no | 0.30 | - | recognised (9, 0.40) | topic |  | Decriminalisation | Removal of criminal penalties |
| yes | 0.97 | - | recognised (10, 0.40) | topic |  | Drug Menace | Problem of illegal drug use and trafficking |
| no | 0.02 | - | recognised (11, 0.41) | scheme |  | Nirbhaya Fund | Government fund that supports the safety and security of women. |
| no | 0.44 | - | recognised (12, 0.41) | topic |  | Narco Terrorism | Criminal drug trafficking and violence |
| yes | 0.89 | - | llm | law |  | NDPS Act | एनडीपीएस अधिनियम 1985 |
| yes | 0.46 | - | llm | institution |  | Narco Coordination Centre | नार्को समन्वय केंद्र |
| yes | 0.82 | - | llm | person |  | Amit Shah | अमित शाह जी |
| no | 0.21 | - | llm | person |  | Narendra Modi | नरेन्द्र मोदी जी |
| yes | 0.77 | - | llm | institution |  | Anti-Narcotics Task Force | एंटी - नारकोटिक्स टास्क फोर्स |
| no | 0.61 | - | dict | group |  | Police | पुलिस |
| yes | 0.93 | - | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| no | 0.62 | - | dict | place |  | Chandigarh | चंडीगढ़ |
| no | 0.18 | - | dict | place |  | Gandhinagar | गांधीनगर |
| yes | 0.91 | - | dict | group |  | Bharatiya Janata Party | भारतीय जनता पार्टी |
| no | 0.18 | - | dict | place |  | Guwahati | गुवाहाटी |
| yes | 1.00 | - | dict | group |  | Youth | नौजवानों |
| no | 0.01 | - | dict | scheme |  | PRAGATI | प्रगति |

## Adv. A. M. Ariff: Supplementary Demands For Grants First Batch, 2022-2023 and Demands for excess grants, 2019-2020- Contd.,

2022-12-13, 1125 words, state `speech`. Speech id 323072.

**Summary.** Criticises the Supplementary Demands for Grants, citing excess expenditure by the Ministry of Finance, lack of pandemic relief, privatization of public assets, and reduction of MGNREGA funds.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Public expenditure and excess grants | Excesses over Voted Grants and Charged Appropriations |
| yes | 0.83 | - | llm | topic |  | Privatization | privatization of Railways |
| yes | 0.96 | - | llm | topic |  | Economic relief and inflation | stimulus and relief package |
| yes | 0.95 | - | recognised (1, 0.35) | topic |  | Supplementary Demands For Grants | A government request to parliament for extra money after it approved the yearly budget. |
| yes | 0.94 | - | recognised (2, 0.38) | topic |  | Demands For Excess Grants | Parliamentary approval for spending beyond budgeted amount |
| yes | 0.96 | - | recognised (3, 0.40) | topic |  | Demands For Grants | A parliamentary process for approving government spending plans. |
| no | 0.41 | - | recognised (4, 0.40) | topic |  | Demands For Grants On Account | Parliamentary approval for interim budget spending |
| no | 0.05 | - | recognised (5, 0.42) | law |  | Money Bills | Financial legislation concerning revenue and government spending. |
| yes | 0.95 | - | recognised (6, 0.43) | topic |  | Budget | India's yearly financial plan, showing the government's planned income and spending. |
| no | 0.38 | - | recognised (7, 0.43) | topic |  | C&AG Reports | Reports that check how the government spent public money. |
| no | 0.35 | - | recognised (8, 0.43) | topic |  | Deficit | Government spending exceeding income. |
| no | 0.05 | - | recognised (9, 0.43) | topic |  | Health Budget | Financial allocation for healthcare |
| no | 0.21 | - | recognised (10, 0.43) | topic |  | Non-plan Expenditure | Government spending outside the five-year plan schemes. |
| no | 0.09 | - | recognised (11, 0.43) | topic |  | Non-Plan Allocation | Government spending outside five-year planning framework |
| no | 0.05 | - | recognised (12, 0.44) | topic |  | Surpluses | Excess supply beyond demand. |
| yes | 0.99 | - | llm | institution |  | Public Accounts Committee | Public Accounts Committee |
| yes | 1.00 | - | llm | institution |  | Ministry of Finance | Ministry of Finance |
| yes | 0.97 | - | llm | law |  | Mahatma Gandhi National Rural Employment Guarantee Act | MGNREGA scheme |
| yes | 0.96 | - | llm | institution |  | Air India | Air India |
| yes | 0.84 | - | llm | place |  | Kerala | Kerala |
| yes | 0.88 | - | dict | scheme |  | COVID-19 | COVID-19 |
| yes | 1.00 | - | dict | scheme |  | Atmanirbhar Bharat | Atmanirbhar Bharat |
| yes | 0.96 | - | dict | institution |  | Department of Revenue | Department of Revenue |
| yes | 0.90 | - | dict | institution |  | Central universities | Central Universities |
| yes | 0.88 | - | dict | group |  | Traders | traders |
| yes | 0.90 | - | dict | group |  | Minorities | minorities |
| no | 0.75 | - | dict | group |  | Labourers | labourers |
| yes | 0.98 | - | dict | group |  | Poor | poor |

## Sudip Bandyopadhyay: Supplementary Demand for Grants-First Batch,2022-2023 and Demand for excess grants,2019-2020 (discussion not concluded).

2022-12-12, 35 words, state `speech`. Speech id 323153.

**Summary.** Notes that issues regarding West Bengal have been resolved following a meeting with the Minister.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.52 | - | llm | topic |  | Inter-governmental relations | All the issues have been resolved now |
| no | 0.56 | - | recognised (1, 0.37) | place |  | West Bengal | State in eastern India |
| no | 0.06 | - | recognised (2, 0.39) | topic |  | Operation Ganga | Government evacuation that brought Indian citizens home from Ukraine. |
| no | 0.20 | - | recognised (3, 0.39) | topic |  | Inter-State Disputes | Disagreements between provinces |
| no | 0.03 | - | recognised (4, 0.39) | law |  | Shimla Agreement | Agreement between India and Pakistan on the border after the 1971 war. |
| no | 0.09 | - | recognised (5, 0.39) | place |  | North 24 Parganas | District in West Bengal, India. |
| no | 0.08 | - | recognised (6, 0.40) | place |  | South 24 Parganas | District in West Bengal, India. |
| no | 0.11 | - | recognised (7, 0.40) | place |  | Kolkata | District in West Bengal, India. |
| no | 0.08 | - | recognised (8, 0.40) | scheme |  | One Nation One Ration Card Yojana | Government policy that lets a ration card be used anywhere in India. |
| no | 0.06 | - | recognised (9, 0.40) | scheme |  | Vivad Se Vishwas Scheme | Government scheme that settles tax disputes between taxpayers and the government. |
| no | 0.10 | - | recognised (10, 0.40) | place |  | Gorkhaland | Proposed state in Darjeeling region of West Bengal |
| no | 0.05 | - | recognised (11, 0.40) | institution |  | Inter-State Council | Body facilitating cooperation and coordination between state governments. |
| no | 0.04 | - | recognised (12, 0.40) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| yes | 0.96 | - | llm | place |  | West Bengal | West Bengal |

## Manish Tewari: Introduction of the Electricity (Amendment) Bill, 2022

2022-08-08, 417 words, state `speech`. Speech id 324686.

**Summary.** Opposes the introduction of the Electricity (Amendment) Bill, 2022, arguing it infringes on state powers and weakens consumer protection.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.95 | - | llm | topic |  | Electricity distribution privatisation | Electricity (Amendment) Bill, 2022 |
| no | 0.01 | - | recognised (1, 0.39) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.65 | - | recognised (2, 0.41) | law |  | Power Sector Reforms | Government policy changes modernizing electricity generation and distribution. |
| yes | 0.97 | - | recognised (3, 0.41) | law |  | Law Amendment | Change to existing legislation |
| no | 0.01 | - | recognised (4, 0.42) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.01 | - | recognised (5, 0.42) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.36 | - | recognised (6, 0.43) | law |  | Union List | List of powers reserved for central government |
| no | 0.01 | - | recognised (7, 0.43) | law |  | Constitution (One Hundred And Thirtieth Amendment) Bill, 2025 | Proposed amendment to India Constitution number 130 |
| no | 0.04 | - | recognised (8, 0.43) | institution |  | Central Electricity Authority | Agency regulating electricity sector |
| no | 0.61 | - | recognised (9, 0.43) | institution |  | State Legislatures | Elected assemblies that represent and govern individual Indian states. |
| no | 0.03 | - | recognised (10, 0.43) | law |  | Ninth Schedule | A list in India's constitution that protects certain laws from being challenged in court. |
| no | 0.64 | - | recognised (11, 0.43) | law |  | State List | Constitutional subjects under state jurisdiction. |
| no | 0.15 | - | recognised (12, 0.43) | institution |  | Electricity Boards | Agencies responsible for power generation and distribution. |
| yes | 1.00 | - | llm | law |  | Electricity (Amendment) Bill, 2022 | Electricity (Amendment) Bill, 2022 |
| yes | 1.00 | - | llm | law |  | Electricity Act, 2003 | Electricity Act, 2003 |
| yes | 1.00 | - | dict | group |  | Consumers | consumers |
| yes | 0.90 | - | dict | group |  | Companies | companies |
| yes | 0.96 | - | dict | group |  | Poor | poor |
| yes | 0.84 | - | dict | law |  | Constitution of India | Constitution |

## Pralhad Joshi: Regarding renovation of Ahilyasthan Temple in Madhubani Parliamentary Constituency.

2022-04-06, 142 words, state `speech`. Speech id 328034.

**Summary.** Appeals to members to participate in the parliamentary debate on the situation in Ukraine and listen to the government's detailed replies.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.79 | - | llm | topic |  | Foreign policy and international crises | यूक्रेन |
| no | 0.20 | - | recognised (2, 0.40) | topic |  | Parliamentary Questions | Questions that members ask the government about its work. |
| no | 0.12 | - | recognised (4, 0.41) | topic |  | Rule 184 | A specific rule that allows a parliamentary discussion with a vote. |
| no | 0.02 | - | recognised (5, 0.41) | topic |  | Parliamentary Committees | A group of parliament members that studies a specific issue in depth. |
| no | 0.05 | - | recognised (6, 0.41) | topic |  | Parliamentary Zero Hour | A period in a parliament session for raising urgent matters. |
| no | 0.34 | - | recognised (7, 0.41) | topic |  | Speeches | Formal remarks made by a member of parliament. |
| no | 0.37 | - | recognised (9, 0.41) | topic |  | Observation | A formal note made by parliament on a matter. |
| no | 0.73 | - | recognised (11, 0.42) | topic |  | Parliamentary Proceedings | The official record and conduct of a parliament session. |
| no | 0.06 | - | recognised (12, 0.42) | topic |  | Recommendation | Advice given by a parliamentary committee. |
| no | 0.22 | - | recognised (13, 0.42) | topic |  | Short Duration Discussion | A brief parliamentary debate on one specific issue. |
| no | 0.04 | - | recognised (14, 0.43) | topic |  | Parliamentary Delagation | A group of parliament members who travel together for talks. Correct spelling: Delegation. |
| no | 0.04 | - | recognised (15, 0.43) | topic |  | Operation Ganga | Government evacuation that brought Indian citizens home from Ukraine. |
| no | 0.03 | - | recognised (16, 0.43) | law |  | Rule 56 | Parliamentary procedure rule |
| yes | 0.89 | - | llm | place |  | Ukraine | यूक्रेन |
| yes | 0.80 | - | llm | person |  | Hardeep Singh Puri | माननीय हरदीप सिंह पुरी |
| yes | 0.85 | - | dict | institution |  | Ministry of External Affairs | विदेश मंत्री |

## Kuldeep Rai Sharma: Further general discussion on the Union Budget for 2022-2023 (Discussion concluded).

2022-02-10, 574 words, state `speech`. Speech id 328995.

**Summary.** Puts forward extensive demands for the holistic development, increased budget, infrastructure, and welfare measures in the Andaman and Nicobar Islands.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Regional development | Andaman & Nicobar Islands |
| yes | 0.95 | - | llm | topic |  | Tourism development | tourism |
| yes | 0.97 | - | llm | topic |  | Employment generation | employment |
| yes | 0.99 | - | recognised (1, 0.38) | place |  | Andaman & N Islands | Union territory comprising islands in Bay of Bengal |
| no | 0.09 | - | recognised (2, 0.40) | place |  | North and Middle Andaman | District in Andaman and Nicobar Islands, India. |
| no | 0.23 | - | recognised (3, 0.41) | topic |  | Demands For Excess Grants | Parliamentary approval for spending beyond budgeted amount |
| no | 0.11 | - | recognised (4, 0.42) | topic |  | SCs and STs welfare | Support for scheduled communities |
| yes | 0.93 | - | recognised (5, 0.42) | topic |  | Development Planning | Strategy for economic and social growth |
| no | 0.03 | - | recognised (6, 0.42) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.05 | - | recognised (7, 0.42) | topic |  | Agitation | Organized protests and demonstrations by groups demanding change. |
| no | 0.19 | - | recognised (8, 0.42) | topic |  | Tribal Development | Improvement for tribal communities. |
| yes | 0.93 | - | recognised (9, 0.42) | topic |  | Development Plans | Strategic initiatives for progress |
| no | 0.02 | - | recognised (10, 0.42) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.33 | - | recognised (11, 0.42) | topic |  | Demands For Grants On Account | Parliamentary approval for interim budget spending |
| no | 0.10 | - | recognised (12, 0.43) | topic |  | Supplementary Demands For Grants | A government request to parliament for extra money after it approved the yearly budget. |
| yes | 1.00 | - | llm | place |  | Andaman and Nicobar Islands | Andaman & Nicobar Islands |
| yes | 0.99 | - | llm | place |  | Port Blair | Port Blair |
| yes | 0.97 | - | llm | place |  | Madurai | Madurai |
| yes | 0.98 | - | llm | place |  | Kochi | Kochi |
| no | 0.76 | - | dict | law |  | Union Budget | Budget |
| yes | 0.98 | - | dict | group |  | Women | women |
| yes | 0.99 | - | dict | place |  | Diglipur | Diglipur |
| yes | 0.99 | - | dict | institution |  | Andaman and Nicobar Administration | Andaman and Nicobar Administration |
| yes | 0.98 | - | dict | group |  | Tourists | tourists |
| yes | 0.98 | - | dict | group |  | ASHA | ASHA |
| yes | 0.98 | - | dict | group |  | Patients | patients |
| no | 0.11 | - | dict | place |  | Puducherry | Puducherry |

## Doddalahalli Kempegowda Suresh: Motion of Thanks on the President’s Address-Contd.

2022-02-03, 1093 words, state `speech`. Speech id 329571.

**Summary.** Opposes the Motion of Thanks on the President's Address, criticizing the government's economic policies, rising unemployment, agricultural crisis, and inadequate funding for classical languages like Kannada.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Unemployment and economic crisis | employment crisis caused by the pandemic |
| yes | 0.98 | - | llm | topic |  | Agricultural distress and MSP | farm crisis |
| yes | 0.84 | - | llm | topic |  | Promotion of classical languages | classical languages |
| yes | 0.92 | - | recognised (1, 0.42) | topic |  | Kannada Language | Official language of Karnataka state |
| no | 0.03 | - | recognised (2, 0.43) | scheme |  | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| yes | 0.98 | - | recognised (3, 0.43) | topic |  | Economic Crisis | Severe economic disruption or recession affecting the nation |
| yes | 0.99 | - | recognised (4, 0.43) | topic |  | Economy | Economic conditions productivity and growth. |
| yes | 0.81 | - | recognised (5, 0.44) | topic |  | Regional Disparity | Economic inequalities between different regions of India |
| yes | 0.97 | - | recognised (6, 0.44) | topic |  | Agricultural Distress | Serious economic hardship faced by farmers and the farming sector. |
| no | 0.78 | - | recognised (7, 0.44) | place |  | Karnataka | Southern state of India |
| yes | 0.95 | - | recognised (8, 0.44) | topic |  | President Address | The speech the President gives when a parliament session opens. |
| yes | 0.88 | - | recognised (9, 0.45) | topic |  | Poverty | State of living with insufficient income. |
| yes | 0.93 | - | recognised (10, 0.45) | scheme |  | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| no | 0.02 | - | recognised (11, 0.45) | place |  | Mysuru | District and Lok Sabha constituency in Karnataka, India. The constituency is listed as Mysore. |
| no | 0.16 | - | recognised (12, 0.45) | law |  | Development Policy | Government strategy for economic growth. |
| yes | 0.90 | - | llm | scheme |  | Pradhan Mantri Fasal Bima Yojana | Pradhan Mantri Fasal Bima Yojana |
| yes | 0.97 | - | llm | scheme |  | Pradhan Mantri Bharatiya Janaushadhi Pariyojana | Pradhan Mantri Bhartiya Janaushadhi Pariyojana |
| yes | 0.75 | - | llm | scheme |  | PM SVANidhi | Prime Minister's Street Vendor's AatmaNirbhar Nidhi (PM SVANidhi) scheme |
| yes | 0.97 | - | llm | group |  | Kannada | Kannada |
| yes | 1.00 | - | dict | group |  | Farmers | farmers |
| no | 0.58 | - | dict | group |  | Sanskrit | Sanskrit |
| yes | 1.00 | - | dict | group |  | Poor | poor |
| yes | 0.99 | - | dict | person |  | Narendra Modi | Modi |
| no | 0.05 | - | dict | group |  | Odia | Odia |
| no | 0.08 | - | dict | group |  | Malayalam | Malayalam |
| no | 0.02 | - | dict | group |  | Telugu | Telugu |
| yes | 1.00 | - | dict | scheme |  | Minimum Support Price | Minimum Support Price |

## Bhola Singh: Introduction of the Mahatma Gandhi National Rural Employment Guarantee (Amendment) Bill, 2019 (Amendment of Schedule 1).

2021-12-03, 218 words, state `speech`. Speech id 331396.

**Summary.** Introduces private member bills on stubble management policy to prevent pollution and population control and management.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.88 | - | llm | topic |  | Stubble burning | burning of stubble |
| yes | 0.91 | - | llm | topic |  | Stubble management | stubble management policy |
| yes | 0.61 | - | llm | topic |  | Population control | stabilizing the population |
| yes | 0.66 | - | llm | topic |  | Family planning | family planning |
| yes | 0.72 | - | llm | topic |  | Climate change | climate change |
| no | 0.53 | - | recognised (1, 0.34) | topic |  | Private Members Bills | A bill introduced by a member who is not a minister. |
| no | 0.56 | - | recognised (2, 0.36) | topic |  | Population Control | Government regulation and strategy to control population growth. |
| no | 0.13 | - | recognised (3, 0.36) | law |  | Private Members Resolution | Parliamentary proposal from individual lawmakers |
| yes | 0.89 | - | recognised (4, 0.37) | topic |  | Stubble Burning | Burning of crop residue after harvest, a major cause of air pollution. |
| yes | 0.82 | - | recognised (5, 0.38) | topic |  | Pollution Control | Government action to reduce and prevent pollution of air, water, or land. |
| no | 0.60 | - | recognised (7, 0.38) | topic |  | Population Explosion | Rapid population growth. |
| no | 0.02 | - | recognised (8, 0.38) | law |  | Minimum Support Prices | Price floor for agricultural commodities |
| no | 0.02 | - | recognised (9, 0.39) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.02 | - | recognised (11, 0.39) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.02 | - | recognised (13, 0.39) | topic |  | Sikhs | Sikh population and community issues |
| no | 0.04 | - | recognised (14, 0.39) | law |  | National Population Register(NPR) | Government census of population with personal identification details. |
| yes | 0.93 | - | recognised (15, 0.39) | topic |  | Bills Introduction | The step where a new bill is presented to parliament. |
| no | 0.35 | - | llm | law |  | Population (Control and Management) Bill, 2021 | Population (Control and Management) Bill, 2021 |
| no | 0.04 | - | llm | law |  | Climate Change (Net Zero Carbon) Bill, 2021 | Climate Change (Net Zero Carbon) Bill, 2021 |
| yes | 0.85 | - | llm | institution |  | Population Planning Agency | Population Planning Agency |
| yes | 0.92 | - | llm | group |  | Girls | girl child |

## Manoj Kishorbhai Kotak: The Speaker made an observation on Covid-19 pandemic. Discussion on COVID-19 pandemic and various aspects relating to it were taken up. (Discussion not concluded).

2021-12-02, 1042 words, state `speech`. Speech id 331565.

**Summary.** Discusses the COVID-19 pandemic situation, praising the massive vaccination drive, free vaccine distribution, and preparedness against the Omicron variant.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | COVID-19 vaccination drive and healthcare | COVID-19 vaccine |
| yes | 0.98 | - | llm | topic |  | Pandemic preparedness and new variants | new variant of Coronavirus named Omicron |
| no | 0.27 | - | llm | topic |  | Economic recovery post-pandemic | Our economy also has started growing |
| yes | 0.99 | - | recognised (1, 0.38) | topic |  | Novel Coronavirus (COVID -19) | The COVID-19 disease and the virus that causes it. |
| no | 0.28 | - | recognised (2, 0.39) | topic |  | Corona Warriors | Healthcare workers fighting pandemic |
| yes | 0.99 | - | recognised (3, 0.39) | topic |  | Vaccination Programme | General government effort that gives vaccines to prevent disease. |
| no | 0.02 | - | recognised (4, 0.41) | scheme |  | Vande Bharat Mission | Government program that brought Indian citizens home from abroad. |
| yes | 0.99 | - | recognised (5, 0.41) | topic |  | Pandemic Disease | A disease that spreads quickly across a large population. |
| no | 0.05 | - | recognised (6, 0.41) | topic |  | Free Medical Tests | Testing without cost. |
| no | 0.04 | - | recognised (7, 0.41) | scheme |  | Pradhan Mantri Garib Kalyan Anna Yojana (PM-GKAY) | Government scheme that gave free food grains to poor families. |
| no | 0.03 | - | recognised (8, 0.42) | scheme |  | National Health Protection Scheme (Ayushman Bharat) | Government scheme that pays hospital bills for poor and vulnerable families. |
| no | 0.13 | - | recognised (9, 0.42) | topic |  | Sabka Sath Sabka Vikas | Government slogan for growth that includes and benefits everyone. |
| no | 0.01 | - | recognised (10, 0.42) | scheme |  | Indradhanush Scheme | Named government health scheme. |
| no | 0.13 | - | recognised (11, 0.42) | scheme |  | Universal Immunisation Programme | Government program that vaccinates children against preventable diseases. |
| yes | 0.99 | - | recognised (12, 0.42) | topic |  | Vaccination | Giving a substance to protect a person from a disease. |
| yes | 0.53 | - | llm | place |  | Karnataka | Karnataka |
| yes | 0.98 | - | dict | scheme |  | COVID-19 | COVID-19 |
| yes | 0.96 | - | dict | person |  | Narendra Modi | Modi |
| yes | 1.00 | - | dict | group |  | Citizens | citizens |
| yes | 0.94 | - | dict | group |  | Omicron | Omicron |
| no | 0.23 | - | dict | group |  | Nurses | nurses |
| no | 0.56 | - | dict | group |  | Poor | poor |
| no | 0.22 | - | dict | group |  | Doctors | doctors |
| no | 0.62 | - | dict | group |  | Bharatiya Janata Party | Bhartiya Janata Party |

## Sanghamitra Maurya: Need to preserve the original Ashoka Pillar in Badaun Parliamentary Constituency, Uttar Pradesh.

2021-03-24, 224 words, state `speech`. Speech id 332818.

**Summary.** Asks the Government to preserve the original Ashoka pillar in Badaun Parliamentary Constituency and protect its archaeological site.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Archaeological site preservation | पुरातात्विक स्थान को संरक्षित |
| no | 0.72 | - | recognised (1, 0.37) | institution |  | Archaeological Survey of India (ASI) | Government body responsible for archaeological sites and heritage preservation |
| no | 0.23 | - | recognised (2, 0.38) | place |  | Budaun | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Badaun. |
| no | 0.01 | - | recognised (3, 0.39) | place |  | Ayodhya | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Faizabad. |
| yes | 0.98 | - | recognised (4, 0.39) | topic |  | Preservation of Cultural Heritage | Protecting and repairing historical sites, art, and traditions for future generations. |
| no | 0.02 | - | recognised (5, 0.40) | place |  | Prayagraj | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Allahabad. |
| no | 0.02 | - | recognised (6, 0.40) | place |  | Kushinagar | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Kushi Nagar. |
| no | 0.02 | - | recognised (7, 0.41) | place |  | Pataliputra | Lok Sabha constituency in Bihar, India. |
| yes | 0.97 | - | recognised (8, 0.41) | place |  | Heritage Sites | Historic monuments protected as cultural property |
| no | 0.02 | - | recognised (9, 0.41) | place |  | Agra | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.01 | - | recognised (10, 0.41) | place |  | Varanasi | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.90 | - | recognised (11, 0.41) | place |  | Protected Monuments | Heritage structures under government protection |
| no | 0.02 | - | recognised (12, 0.41) | place |  | Firozabad | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.81 | - | llm | law |  | Ashoka Pillar | सम्राट अशोक महान के मूल स्तम्भ |
| no | 0.24 | - | llm | place |  | Badaun | Badaun *(not in text)* |
| yes | 1.00 | - | dict | group |  | Tourists | पर्यटकों |
| yes | 1.00 | - | dict | person |  | Ashoka | सम्राट अशोक |
| no | 0.31 | - | dict | place |  | Pali | पाली |
| yes | 0.95 | - | dict | institution |  | Archaeological Survey of India | भारतीय पुरातत्व सर्वेक्षण |

## Annpurna Devi: Need to set up Central Govrnment Health Scheme (CGHS) Dispensary in Kodarma Parliamentary Constituency, Jharkand.

2021-03-19, 102 words, state `speech`. Speech id 333286.

**Summary.** Demands the establishment of a Central Government Health Scheme dispensary in the Koderma parliamentary constituency to assist government employees and elderly citizens.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Government health dispensary services | केंद्रीय सरकार स्वास्थ्य योजना की डिस्पेंसरी |
| yes | 0.97 | - | recognised (1, 0.34) | scheme |  | CGHS | Government health insurance for central government employees, pensioners, and families. |
| yes | 0.97 | - | recognised (2, 0.37) | institution |  | Dispensaries | Facilities providing basic medical services. |
| no | 0.02 | - | recognised (3, 0.38) | scheme |  | Jan Aushadhi Scheme | Government-run stores that sell generic medicines at low prices. |
| yes | 0.95 | - | recognised (4, 0.38) | place |  | Koderma | District and Lok Sabha constituency in Jharkhand, India. |
| no | 0.05 | - | recognised (5, 0.38) | scheme |  | National Health Mission | Government programme that provides healthcare services across the country. |
| no | 0.07 | - | recognised (6, 0.39) | institution |  | Primary Health Centres | Basic healthcare facilities |
| yes | 0.82 | - | recognised (7, 0.39) | institution |  | Health Centres | Facilities providing medical services |
| no | 0.33 | - | recognised (8, 0.39) | topic |  | Old Age Benefits | Support for elderly. |
| no | 0.09 | - | recognised (9, 0.39) | institution |  | Community Health Centres | Basic healthcare facilities in communities |
| no | 0.38 | - | recognised (10, 0.39) | institution |  | Government Hospitals | Public medical facilities providing healthcare |
| no | 0.02 | - | recognised (11, 0.39) | scheme |  | Pradhan Mantri Swasthya Suraksha Bima Yojana | Government health insurance scheme for poor families. |
| no | 0.27 | - | recognised (12, 0.39) | topic |  | Health For All Scheme | General government aim to give every citizen access to healthcare. |
| yes | 1.00 | - | dict | place |  | Koderma | कोडरमा |
| yes | 0.99 | - | dict | place |  | Hazaribagh | हजारीबाग |
| yes | 1.00 | - | dict | institution |  | Ministry of Health and Family Welfare | स्वास्थ्य मंत्रालय |

## Raksha Nikhil Khadse: Further discussion on the Demand for Grant No. 84 under the control of the Ministry of Railways (Discussion concluded and Demand voted in full)

2021-03-16, 1400 words, state `speech`. Speech id 333847.

**Summary.** Supports railway grants, requesting a POH workshop at Bhusawal, gauge conversion and extension of the Pachora-Jamner line, rail connectivity from Bhusawal to Aurangabad, and new train services.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Railway infrastructure and projects | Demands of Grants related to Railways |
| yes | 0.98 | - | llm | topic |  | Railway gauge conversion and tourism connectivity | conversion from NG to Board gauge |
| yes | 0.97 | - | llm | topic |  | New train services and stoppages | operate a special train from Bhusawal to Mumbai |
| yes | 0.67 | - | llm | topic |  | Railway asset monetisation | monetisation of the assets |
| yes | 0.97 | - | recognised (1, 0.39) | topic |  | Rail Budget | Annual financial allocation for railway services |
| yes | 0.95 | - | recognised (2, 0.39) | law |  | Railway Budget | Annual government allocation for railway operations and development. |
| no | 0.16 | - | recognised (3, 0.39) | place |  | Chhatrapati Sambhajinagar | District and Lok Sabha constituency in Maharashtra, India. The constituency is listed as Aurangabad. |
| yes | 0.99 | - | recognised (4, 0.39) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| no | 0.03 | - | recognised (5, 0.39) | scheme |  | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| yes | 0.91 | - | recognised (6, 0.40) | topic |  | New Railway Line | Construction of new railway routes and tracks. |
| yes | 0.96 | - | recognised (7, 0.40) | topic |  | Gauge Conversion | Changing the distance between railway tracks to improve compatibility. |
| no | 0.03 | - | recognised (8, 0.40) | scheme |  | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.03 | - | recognised (9, 0.40) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.02 | - | recognised (10, 0.41) | law |  | Railway Freight Exemptions | Relief from transport taxes for certain rail cargo. |
| yes | 0.98 | - | recognised (11, 0.41) | institution |  | Indian Railways | Government rail organization. |
| yes | 0.83 | - | recognised (12, 0.41) | place |  | Railway Station | Facility where trains stop for passengers and cargo operations. |
| yes | 1.00 | - | llm | place |  | Bhusawal | Bhusawal |
| yes | 1.00 | - | llm | place |  | Ajanta Caves | Ajanta caves |
| yes | 1.00 | - | llm | scheme |  | Pachora-Jamner NG line | Pachora-Jamner NG line |
| no | 0.04 | - | dict | person |  | Nirmala Sitharaman | Nirmala Sitharaman |
| yes | 0.81 | - | dict | institution |  | Ministry of Railways | Railway Minister |
| yes | 1.00 | - | dict | place |  | Mumbai | Mumbai |
| yes | 1.00 | - | dict | institution |  | Central Railway | Central Railway |
| yes | 1.00 | - | dict | place |  | Pune | Pune |
| no | 0.37 | - | dict | law |  | Union Budget | Budget |
| no | 0.15 | - | dict | person |  | Narendra Modi | Modi |
| yes | 1.00 | - | dict | place |  | Aurangabad | Aurangabad |

## Tapir Gao: Regarding restoring of democracy in Myanmar.

2021-02-13, 280 words, state `speech`. Speech id 334457.

**Summary.** Urges the Government of India to lead efforts in restoring democracy in Myanmar and protect bilateral relations and regional stability.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.98 | - | llm | topic |  | Democracy restoration | restoring democracy in Myanmar |
| yes | 0.96 | - | recognised (1, 0.33) | topic |  | Indo-Myanmar Relations | Relations between India and Myanmar. |
| no | 0.41 | - | recognised (2, 0.37) | place |  | China | Neighboring country with bilateral relations with India |
| yes | 0.98 | - | recognised (3, 0.38) | place |  | Myanmar | Southeast Asian country. |
| yes | 0.90 | - | recognised (4, 0.38) | topic |  | Bilateral Relations | Relations between India and one other country. |
| no | 0.39 | - | recognised (5, 0.39) | topic |  | Indo-China Relation | Relations between India and China. |
| no | 0.07 | - | recognised (6, 0.39) | law |  | Bilateral Agreements | Treaties between India and other nations |
| no | 0.23 | - | recognised (7, 0.40) | place |  | South Asia | Geographic region including India and neighbors |
| no | 0.02 | - | recognised (8, 0.40) | topic |  | Indo-Bangladesh Relation | Relations between India and Bangladesh. |
| no | 0.34 | - | recognised (9, 0.40) | institution |  | Ministry Of External Affairs | Indian government ministry that manages relations with other countries. |
| no | 0.07 | - | recognised (10, 0.40) | institution |  | NSCN(IM) | Armed group operating in northeast India |
| no | 0.57 | - | recognised (11, 0.40) | place |  | Neighbouring Countries | Nations sharing borders with India |
| no | 0.02 | - | recognised (13, 0.41) | topic |  | Indo-Srilanka Relation | Relations between India and Sri Lanka. |
| yes | 1.00 | - | llm | place |  | Myanmar | Myanmar |
| yes | 1.00 | - | llm | person |  | Aung San Suu Kyi | Aung San Suu Kyi |
| yes | 1.00 | - | llm | place |  | India | India |
| yes | 0.57 | - | llm | place |  | Arunachal Pradesh | Arunachal Pradesh |
| yes | 0.43 | - | llm | place |  | Nagaland | Nagaland |
| no | 0.25 | - | llm | place |  | Manipur | Manipur |
| no | 0.34 | - | llm | place |  | Mizoram | Mizoram |
| no | 0.65 | - | dict | institution |  | Indian Army | Indian Army |
| yes | 0.94 | - | dict | scheme |  | Act East Policy | Act East Policy |
| yes | 0.90 | - | dict | place |  | China | Chinese |

## Kaushalendra Kumar: General discussion on the Union Budget for 2021-2022 (Discussion not concluded).

2021-02-11, 1024 words, state `speech`. Speech id 335003.

**Summary.** Supports the Union Budget 2021-2022, praising its focus on agriculture, infrastructure, and healthcare, and requests an airport in Nalanda and operationalization of ordnance factory units.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Union Budget 2021-2022 support and evaluation | वर्ष 2021-22 के बजट पर बोलने का अवसर |
| yes | 0.90 | - | llm | topic |  | Development and infrastructure in Nalanda | हमारे क्षेत्र नालंदा में |
| no | 0.12 | - | recognised (1, 0.38) | law |  | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.99 | - | recognised (2, 0.38) | topic |  | Budget | India's yearly financial plan, showing the government's planned income and spending. |
| yes | 0.92 | - | recognised (3, 0.38) | place |  | Nalanda | District and Lok Sabha constituency in Bihar, India. |
| yes | 0.89 | - | recognised (4, 0.40) | topic |  | Health Budget | Financial allocation for healthcare |
| yes | 0.92 | - | recognised (5, 0.40) | law |  | General Budget | Annual government financial plan detailing revenue and expenditure allocations. |
| no | 0.56 | - | recognised (6, 0.41) | institution |  | Nalanda University | Historic Buddhist university revived in modern India |
| no | 0.03 | - | recognised (7, 0.41) | place |  | Darbhanga | District and Lok Sabha constituency in Bihar, India. |
| no | 0.53 | - | recognised (8, 0.41) | topic |  | Sabka Sath Sabka Vikas | Government slogan for growth that includes and benefits everyone. |
| no | 0.10 | - | recognised (9, 0.41) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.04 | - | recognised (10, 0.41) | scheme |  | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| no | 0.03 | - | recognised (11, 0.41) | scheme |  | UDAAN Scheme | Government scheme that supports small and medium businesses. |
| no | 0.14 | - | recognised (12, 0.41) | place |  | Nawada | District and Lok Sabha constituency in Bihar, India. |
| yes | 1.00 | - | llm | place |  | Nalanda | नालंदा |
| yes | 0.66 | - | llm | person |  | Narendra Modi | माननीय प्रधानमंत्री जी |
| no | 0.05 | - | llm | person |  | Atal Bihari Vajpayee | अटल बिहारी वाजपेयी |
| yes | 0.99 | - | llm | person |  | Anurag Singh Thakur | श्री अनुराग ठाकुर जी |
| yes | 0.99 | - | dict | institution |  | Sainik School | सैनिक स्कूल |
| yes | 0.87 | - | dict | institution |  | Ministry of Finance | वित्त मंत्री |
| yes | 0.99 | - | dict | group |  | Farmers | किसानों |
| yes | 1.00 | - | dict | group |  | Traders | व्यापारियों |
| yes | 0.97 | - | dict | group |  | Poor | गरीब |
| no | 0.09 | - | dict | place |  | Kalyan | कल्याण |
| no | 0.74 | - | dict | scheme |  | Atmanirbhar Bharat | आत्मनिर्भर भारत |
| yes | 0.98 | - | dict | group |  | National Democratic Alliance | एनडीए |

## Bharati Pravin Pawar: Combined Discussion on Statutory Resolution regarding Disapproval of Homoeopathy Central Council (Amendment) Ordinance, 2020 (Ordinance No. 6 of 2020) and Homoeopathy Central Council (Amendment) Bill, 2020 (As Passed By Rajya Sabha) and Statutory Resolution regarding Disapproval of Indian Medicine Central Council (Amendment) Ordinance, 2020 (Ordinance No 7 of 2020) and Indian Medicine Central Council (Amendment) Bill, 2020 (As Passed By Rajya Sabha) (Statutory Resolution - Negatived and Government Bill - Passd).

2020-09-21, 274 words, state `speech`. Speech id 336464.

**Summary.** Supports the National Commission for the Indian System of Medicine Bill, 2020, highlighting its promotion of research and quality education in indigenous medicine.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Traditional medicine | indigenous medicine system |
| yes | 0.86 | - | llm | topic |  | Medical education reform | क्वालिटेटिव एजुकेशन |
| no | 0.35 | - | recognised (1, 0.34) | law |  | National Medical Commission Bill | Legislation regulating medical doctors and practice. |
| no | 0.59 | - | recognised (2, 0.36) | topic |  | Ayurveda | Traditional Indian system of medicine and wellness |
| no | 0.31 | - | recognised (3, 0.37) | institution |  | AYUSH | System for traditional medicine |
| no | 0.03 | - | recognised (4, 0.37) | institution |  | National Ayurveda University | Higher education institution for traditional Indian medicine |
| yes | 0.96 | - | recognised (5, 0.38) | topic |  | Traditional Medicine | Medical practices based on indigenous knowledge systems |
| no | 0.03 | - | recognised (6, 0.38) | institution |  | Indian Council of Medical Research (ICMR) | Medical and health research organization. |
| no | 0.03 | - | recognised (7, 0.39) | institution |  | National Institute of Medicinal Plants | Research organization for medicinal plant studies |
| no | 0.08 | - | recognised (8, 0.39) | institution |  | Medical Council of India | Body regulating medical professionals |
| no | 0.02 | - | recognised (9, 0.39) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.04 | - | recognised (10, 0.40) | topic |  | Siddha | Traditional medicine system practiced in India. |
| no | 0.03 | - | recognised (11, 0.40) | scheme |  | Vocal for Local | Promoting Indian-made goods and local businesses |
| no | 0.02 | - | recognised (12, 0.40) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| yes | 0.97 | - | llm | law |  | National Commission for the Indian System of Medicine Bill, 2020 | Indian System of Medicine Bill, 2020 |
| yes | 0.91 | - | llm | law |  | Indian Medicine Central Council Act | Indian Medicine Central Council Act |
| yes | 0.80 | - | dict | person |  | Narendra Modi | Narendra Modi |
| no | 0.41 | - | dict | person |  | Harsh Vardhan | हर्ष वर्धन जी |

## Adv. A. M. Ariff: Combined Disscussion on statutory resolution regarding disapproval of essential commodities (amendment) ordinance, 2020 and passing of essential commodities (amendment) bill, 2020. (Statutory resolution negatived and Bill Passed)

2020-09-15, 459 words, state `speech`. Speech id 337288.

**Summary.** Opposes the Essential Commodities (Amendment) Bill, 2020, arguing that it favors corporate hoarding and harms farmers and consumers.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.96 | - | llm | topic |  | Agricultural market regulation | Essential Commodities (Amendment) Bill, 2020 |
| yes | 0.98 | - | llm | topic |  | Food storage and hoarding | store and hoard *(not in text)* |
| yes | 0.98 | - | recognised (1, 0.37) | law |  | Essential Commodities Act | Law regulating supply. |
| no | 0.04 | - | recognised (2, 0.38) | law |  | Minimum Support Prices | Price floor for agricultural commodities |
| no | 0.02 | - | recognised (3, 0.40) | institution |  | Swaminathan Commission Report | Report from a government commission that recommended higher crop support prices. |
| no | 0.04 | - | recognised (4, 0.40) | scheme |  | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| no | 0.02 | - | recognised (5, 0.41) | institution |  | Food Corporation of India (FCI) | The government corporation that buys, stores, and distributes food grain in India. |
| no | 0.05 | - | recognised (6, 0.41) | law |  | NATIONAL FOOD SECURITY ACT | Law guaranteeing subsidized food for poor households |
| yes | 0.99 | - | recognised (7, 0.41) | topic |  | Essential Commodities | Basic goods needed by people |
| no | 0.01 | - | recognised (8, 0.41) | law |  | Land Ceiling | Limits on maximum land holdings. |
| no | 0.23 | - | recognised (9, 0.42) | law |  | Farm Laws | Laws that govern how farming and agricultural trade are carried out. |
| no | 0.25 | - | recognised (10, 0.42) | topic |  | Farmers' Agitation | Farm worker protests and demonstrations. |
| no | 0.01 | - | recognised (11, 0.42) | institution |  | KRIBHCO | Cooperative fertilizer producer owned by farmers. |
| yes | 0.98 | - | recognised (12, 0.43) | topic |  | Hoarding | Stockpiling goods unfairly |
| yes | 1.00 | - | llm | law |  | Essential Commodities (Amendment) Bill, 2020 | Essential Commodities (Amendment) Bill, 2020 |
| yes | 1.00 | - | llm | law |  | Essential Commodities Act | Essential Commodities Act |
| yes | 0.93 | - | llm | group |  | Adani Group | Adanis |
| yes | 0.83 | - | llm | institution |  | Adani Wilmar | Adani Wilmar |
| no | 0.15 | - | llm | group |  | Reliance | Reliance |
| no | 0.01 | - | llm | group |  | Food Corporation of India | Food Producer Organisation |
| yes | 1.00 | - | dict | group |  | Companies | companies |
| yes | 1.00 | - | dict | group |  | Farmers | farmers |
| no | 0.49 | - | dict | place |  | Africa | Africa |
| yes | 0.97 | - | dict | group |  | Citizens | citizens |
| yes | 0.94 | - | dict | group |  | Traders | traders |
| no | 0.50 | - | dict | place |  | Bangladesh | Bangladesh |

## Hibi Eden: Request government to clear the Public Investment Board (PIB ) clearance for the scond phase of the Kochi Metro Rail.

2020-03-17, 143 words, state `speech`. Speech id 338107.

**Summary.** Requests the Central Government and Ministry of Urban Development to grant Public Investment Board clearance for the second phase of the Kochi Metro Rail.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Metro rail connectivity | Kochi Metro Rail |
| yes | 0.92 | - | recognised (1, 0.41) | institution |  | Public Investment Board | Authority evaluating government investment proposals |
| yes | 0.94 | - | recognised (2, 0.41) | topic |  | Metro Railway Development | Rapid transit system development in cities. |
| yes | 0.94 | - | recognised (3, 0.41) | topic |  | Central Government Clearance | Approval by central government. |
| yes | 0.80 | - | recognised (4, 0.41) | topic |  | Detailed Project Report (DPR) | A detailed document that plans and justifies a government infrastructure project before its approval. |
| no | 0.12 | - | recognised (5, 0.41) | place |  | Ernakulam | District and Lok Sabha constituency in Kerala, India. |
| no | 0.02 | - | recognised (6, 0.42) | place |  | Thrissur | District and Lok Sabha constituency in Kerala, India. |
| no | 0.66 | - | recognised (7, 0.42) | topic |  | Central Projects | Government infrastructure projects at national level |
| no | 0.03 | - | recognised (9, 0.42) | topic |  | Environmental Clearance | Official approval required before a project can affect the environment. |
| no | 0.20 | - | recognised (10, 0.43) | topic |  | Metro Corporation | A government company that builds and runs a city's metro rail system. |
| no | 0.02 | - | recognised (11, 0.43) | law |  | Public Interest Litigation (PIL) | A court case filed by a citizen to protect the public interest. |
| no | 0.03 | - | recognised (12, 0.43) | scheme |  | Atal Mission for Rejuvenation and Urban Transformation (AMRUT) | Government program that improves basic infrastructure in cities. |
| no | 0.54 | - | recognised (13, 0.43) | institution |  | Metro Railways | Urban rapid rail transit systems. |
| yes | 1.00 | - | llm | scheme |  | Kochi Metro Rail | Kochi Metro Rail |
| yes | 1.00 | - | llm | institution |  | Public Investment Board | Public Investment Board |
| yes | 1.00 | - | llm | institution |  | Ministry of Urban Development | Ministry of Urban Development |
| yes | 1.00 | - | llm | place |  | Jawaharlal Nehru Stadium | Jawaharlal Nehru Stadium |
| yes | 1.00 | - | llm | place |  | Infopark | Infopark |
| yes | 0.98 | - | dict | scheme |  | Kochi Metro | Kochi Metro |
| yes | 0.89 | - | dict | group |  | Employees | employees |

## E T Mohammed Basheer: Discussion on the Demands for Grants Nos. 92 and 93 under the control of the Ministry of Social Justice and Empowerment (Discussion not concluded).

2020-03-13, 671 words, state `speech`. Speech id 338639.

**Summary.** Criticises the Government for widening social inequalities, discrimination, and handling of minorities and marginalized groups.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Social justice | social justice |
| yes | 0.98 | - | llm | topic |  | Minority rights | religious minorities |
| yes | 0.98 | - | recognised (1, 0.35) | topic |  | Minority Groups | Religious and ethnic minorities requiring protection and welfare |
| no | 0.43 | - | recognised (2, 0.36) | topic |  | Harijan Atrocities | Violence and discrimination against scheduled castes. |
| yes | 0.97 | - | recognised (3, 0.36) | topic |  | Discrimination | Unfair treatment based on identity |
| yes | 0.98 | - | recognised (4, 0.36) | topic |  | Social Inequality | Disparity in wealth, power, and opportunity. |
| yes | 0.98 | - | recognised (5, 0.36) | topic |  | Religious Minorities | Non-Hindu religious communities |
| yes | 0.87 | - | recognised (6, 0.37) | topic |  | Downtrodden | Marginalized and oppressed sections of society. |
| no | 0.56 | - | recognised (7, 0.37) | topic |  | Scs & Sts Atrocities | Crimes against scheduled castes and tribes. |
| yes | 0.98 | - | recognised (8, 0.37) | topic |  | Minorities | Communities that are religious, ethnic, or linguistic minorities. |
| no | 0.09 | - | recognised (9, 0.37) | topic |  | SCs and STs welfare | Support for scheduled communities |
| yes | 0.97 | - | recognised (10, 0.37) | topic |  | Inequality | Disparity in income, opportunity, or status among groups |
| yes | 0.82 | - | recognised (11, 0.37) | topic |  | Weaker Sections | Economically disadvantaged population groups. |
| no | 0.03 | - | recognised (12, 0.37) | institution |  | Sachar Committee | A government committee that studied the condition of Muslim communities in India. |
| yes | 0.96 | - | llm | institution |  | Supreme Court of India | Supreme Court of India |
| yes | 0.95 | - | llm | institution |  | Delhi Minority Commission | Minority Commission of Delhi |
| yes | 0.66 | - | llm | law |  | Citizenship Amendment Act | Citizenship Amendment Act |
| yes | 1.00 | - | llm | group |  | Muslims | Muslims |
| yes | 1.00 | - | dict | group |  | Minorities | minorities |
| yes | 0.89 | - | dict | place |  | Delhi | Delhi |
| no | 0.37 | - | dict | group |  | Islam | Islam |
| yes | 1.00 | - | dict | group |  | Religious minorities | religious minorities |
| no | 0.42 | - | dict | law |  | Rule 193 | Rule 193 |
| no | 0.24 | - | dict | institution |  | United Nations Human Rights Council | UNHRC |
| yes | 1.00 | - | dict | institution |  | Delhi Police | Delhi Police |
| no | 0.14 | - | dict | place |  | Ganga | Ganga |

## Dharmendra Kumar Kashyap: Discussion on the Demands for Grants No. 83 under the control of Ministry of Railway for Financial Year 2020-21 (Discussion not concluded).

2020-03-12, 569 words, state `speech`. Speech id 338869.

**Summary.** Supports the railway demands for grants, highlighting local transit issues, railway crossing overbridges, and station development in Aonla and Bareilly.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Rail connectivity | रेल अनुदान की मांगों |
| yes | 0.97 | - | llm | topic |  | Railway station development | उच्चीकरण |
| yes | 0.92 | - | recognised (1, 0.37) | place |  | Bareilly | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.80 | - | recognised (2, 0.37) | law |  | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.89 | - | recognised (3, 0.38) | topic |  | Rail Budget | Annual financial allocation for railway services |
| no | 0.61 | - | recognised (4, 0.38) | topic |  | Demands For Grants On Account | Parliamentary approval for interim budget spending |
| no | 0.04 | - | recognised (5, 0.39) | topic |  | Demands For Excess Grants | Parliamentary approval for spending beyond budgeted amount |
| yes | 0.95 | - | recognised (6, 0.39) | place |  | Aonla | Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.96 | - | recognised (7, 0.40) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| no | 0.05 | - | recognised (8, 0.40) | scheme |  | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| no | 0.02 | - | recognised (9, 0.40) | law |  | Railway Freight Exemptions | Relief from transport taxes for certain rail cargo. |
| yes | 0.93 | - | recognised (10, 0.40) | topic |  | Demands For Grants | A parliamentary process for approving government spending plans. |
| yes | 0.95 | - | recognised (11, 0.41) | topic |  | Railway Projects | Development and implementation of railway infrastructure and services. |
| yes | 0.96 | - | recognised (12, 0.41) | topic |  | Railway Crossings | Intersections where railway lines cross roads or other tracks. |
| yes | 1.00 | - | llm | place |  | Aonla | आंवला |
| yes | 1.00 | - | llm | place |  | Bareilly | बरेली |
| yes | 1.00 | - | llm | institution |  | Ministry of Railways | रेल विभाग |
| yes | 1.00 | - | dict | place |  | Chandausi | चंदौसी |
| yes | 1.00 | - | dict | place |  | Lucknow | लखनऊ |
| yes | 1.00 | - | dict | place |  | Delhi | दिल्ली |
| no | 0.00 | - | dict | institution |  | Ministry of Road Transport and Highways | विभाग |
| yes | 1.00 | - | dict | place |  | Tilhar | तिलहर |
| yes | 1.00 | - | dict | group |  | Farmers | किसानों |

## Syed Imtiaz Jaleel, Shri: Demand to construct a super express way between Aurangabad and Shridi.

2019-11-20, 187 words, state `speech`. Speech id 342838.

**Summary.** Asks for the construction of a super expressway between Aurangabad and Shridi to ease travel for pilgrims.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| no | 0.02 | - | llm | topic |  | Rail connectivity | सुपर एक्सप्रैस - वे |
| yes | 0.97 | - | recognised (1, 0.36) | place |  | Shirdi | Lok Sabha constituency in Maharashtra, India. |
| no | 0.12 | - | recognised (2, 0.38) | place |  | Chhatrapati Sambhajinagar | District and Lok Sabha constituency in Maharashtra, India. The constituency is listed as Aurangabad. |
| no | 0.03 | - | recognised (3, 0.38) | scheme |  | Swadesh Darshan Scheme | Government program that develops tourism and pilgrimage infrastructure. |
| no | 0.04 | - | recognised (4, 0.39) | scheme |  | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.03 | - | recognised (5, 0.39) | scheme |  | PRASAD Scheme | Government scheme that develops pilgrimage and heritage sites for tourism. |
| no | 0.03 | - | recognised (6, 0.39) | scheme |  | Golden Quadrilateral Project | Government highway project connecting four major Indian cities. |
| no | 0.08 | - | recognised (7, 0.39) | scheme |  | Bharatmala Pariyojana | Government program that builds and connects national highways. |
| no | 0.02 | - | recognised (8, 0.39) | scheme |  | Sagarmala Project | Government plan to develop coastal ports and facilities. |
| no | 0.08 | - | recognised (9, 0.40) | institution |  | National Highways Authority of India (NHAI) | The government body that builds and manages India's national highways. |
| no | 0.02 | - | recognised (10, 0.40) | scheme |  | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.05 | - | recognised (11, 0.41) | topic |  | Detailed Project Report (DPR) | A detailed document that plans and justifies a government infrastructure project before its approval. |
| no | 0.02 | - | recognised (12, 0.41) | place |  | Nashik | District and Lok Sabha constituency in Maharashtra, India. |
| yes | 1.00 | - | llm | place |  | Aurangabad | औरंगाबाद |
| yes | 1.00 | - | llm | place |  | Shridi | शिरडी |
| yes | 1.00 | - | dict | place |  | Shirdi | शिरडी |
| yes | 1.00 | - | dict | group |  | Pilgrims | श्रद्धालुओं |

## Vinayak Bhaurao Raut: Regarding taking up listed items no. 9 (Transgender Persons (Protection of Rights) Bill, 2019) in the House.

2019-08-05, 1199 words, state `speech`. Speech id 343733.

**Summary.** Supports increasing the number of judges in the Supreme Court, suggests raising retirement ages for judges, and requests setting up a High Court bench in Kolhapur.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Judicial backlog and reforms | लाखों की संख्या में मामले न्याय व्यवस्था के पास कई वर्षों से लंबित हैं *(not in text)* |
| yes | 0.95 | - | llm | topic |  | Judicial appointments and retirement age | सुप्रीम कोर्ट के न्यायाधीश की जो आयु सीमा है, उसे 65 वर्ष से बढ़ाकर 70 वर्ष किया जा सकता है |
| yes | 0.81 | - | llm | topic |  | High Court bench establishment | कोल्हापुर हाई कोर्ट की डिमांड पिछले 15 साल से लंबित है |
| yes | 0.97 | - | recognised (1, 0.37) | topic |  | Judicial Reforms | Changes made to improve the courts and legal process. |
| no | 0.13 | - | recognised (2, 0.37) | institution |  | Indian Judicial Service | Proposed civil service that would recruit judges through an all-India exam. |
| yes | 0.92 | - | recognised (3, 0.37) | institution |  | Supreme Court | Highest judicial authority in India. |
| no | 0.09 | - | recognised (4, 0.37) | law |  | Collegium System | Judge selection method. |
| no | 0.05 | - | recognised (5, 0.39) | topic |  | Old Age Benefits | Support for elderly. |
| yes | 0.91 | - | recognised (6, 0.39) | institution |  | High Courts | Senior courts at the state level in the Indian court system. |
| no | 0.03 | - | recognised (7, 0.39) | institution |  | National Judicial Appointment Commission | Body selecting judges for higher courts. |
| no | 0.64 | - | recognised (8, 0.39) | place |  | Kolhapur | District and Lok Sabha constituency in Maharashtra, India. |
| yes | 0.87 | - | recognised (9, 0.39) | topic |  | Judicial Activism | Proactive role of courts in addressing social issues |
| no | 0.03 | - | recognised (10, 0.39) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.02 | - | recognised (11, 0.39) | topic |  | Senior Citizens | Elderly people and their welfare needs. |
| no | 0.77 | - | recognised (12, 0.40) | topic |  | Judicial Appointment | Selection and placement of judges in courts |
| yes | 1.00 | - | llm | institution |  | Supreme Court | सुप्रीम कोर्ट |
| yes | 0.99 | - | llm | institution |  | Bombay High Court | बॉम्बे हाई कोर्ट |
| yes | 1.00 | - | llm | institution |  | Kolhapur High Court | कोल्हापुर हाई कोर्ट |
| no | 0.30 | - | llm | person |  | B. R. Ambedkar | बाबा साहेब अम्बेडकर |
| no | 0.12 | - | llm | person |  | Bal Thackeray | बाला साहेब ठाकरे |
| no | 0.01 | - | llm | law |  | Transgender Persons (Protection of Rights) Bill, 2019 | Transgender Persons (Protection of Rights) Bill, 2019 *(not in text)* |
| yes | 0.95 | - | dict | institution |  | High Court | हाई कोर्ट |
| yes | 0.99 | - | dict | institution |  | Mumbai High Court | मुम्बई हाई कोर्ट |
| no | 0.08 | - | dict | place |  | Kalyan | कल्याण |
| yes | 0.97 | - | dict | place |  | Mumbai | मुम्बई |
| yes | 1.00 | - | dict | group |  | Judges | न्यायाधीश |
| no | 0.06 | - | dict | group |  | Marathi | मराठी |
| no | 0.13 | - | dict | person |  | Balasaheb Thackeray | बाला साहेब ठाकरे जी |
| yes | 0.98 | - | dict | place |  | Konkan | कोंकण |

## Anubhav Mohanty: The motion for the consideration of the Protection of Children from Sexual Offences (Amendment) Bill, 2019 as passed by Rajya Sabha (Bill Passed).

2019-08-01, 223 words, state `speech`. Speech id 344188.

**Summary.** Urges the Ministry to include a robust aftercare program in the POCSO Act to properly rehabilitate child victims.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.96 | - | llm | topic |  | Aftercare for child victims under the POCSO Act | aftercare |
| yes | 0.91 | - | recognised (1, 0.38) | topic |  | Rehabilitation | Support programs to help people recover from disasters or other hardships. |
| no | 0.02 | - | recognised (2, 0.39) | scheme |  | Nirbhaya Fund | Government fund that supports the safety and security of women. |
| no | 0.03 | - | recognised (3, 0.40) | institution |  | Ministry of Social Justice and Empowerment | The government department that works for disadvantaged communities. |
| no | 0.03 | - | recognised (4, 0.40) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| yes | 0.85 | - | recognised (5, 0.41) | topic |  | Child Care | Support for children |
| yes | 0.95 | - | recognised (6, 0.41) | topic |  | Child Welfare | Programs for children. |
| yes | 0.97 | - | recognised (7, 0.41) | topic |  | Child Abuse | Harm to children |
| no | 0.01 | - | recognised (8, 0.41) | topic |  | Drug De-addiction | Treatment programs for persons dependent on addictive substances. |
| no | 0.02 | - | recognised (9, 0.41) | law |  | Child Adoption | Legal process for assuming guardianship and parenthood of a child. |
| no | 0.02 | - | recognised (10, 0.41) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.02 | - | recognised (11, 0.41) | scheme |  | Integrated Child Development Services (ICDS) | Government program that gives nutrition, health, and early education to young children. |
| yes | 0.98 | - | recognised (12, 0.42) | topic |  | Child Protection | Safeguarding of minors from harm. |
| yes | 0.99 | - | llm | law |  | Protection of Children from Sexual Offences Act | POCSO Act |
| yes | 0.97 | - | llm | institution |  | Ministry of Women and Child Development | Ministry of Women and Child Development |
| yes | 0.68 | - | llm | institution |  | Parliamentary Standing Committee on Human Resource Development | Parliamentary Standing Committee on Human Resource Development |
| yes | 1.00 | - | dict | group |  | Children | children |

## Adhir Ranjan Chowdhury: Motion for consideration of the Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019 (Bill passed).

2019-07-31, 1199 words, state `speech`. Speech id 344500.

**Summary.** Discusses the Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019, sharing personal experiences of housing troubles and administrative discrepancies.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Government residential accommodation | residential accommodation |
| yes | 0.98 | - | llm | topic |  | Eviction procedures and rules | notice for eviction, order of eviction and payment of damages |
| no | 0.01 | - | recognised (1, 0.38) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.03 | - | recognised (2, 0.41) | law |  | Lal Dora | Delhi law protecting agricultural land from urban spread. |
| no | 0.03 | - | recognised (3, 0.41) | topic |  | Migrant Problems | Issues faced by migrant workers and displaced persons |
| no | 0.64 | - | recognised (4, 0.41) | law |  | Housing Policy | Government decisions on residential provision |
| no | 0.24 | - | recognised (5, 0.42) | topic |  | Homeless | People without housing or shelter. |
| no | 0.02 | - | recognised (6, 0.42) | topic |  | Short Stay Homes | Facilities that give short-term shelter to people in distress. |
| no | 0.01 | - | recognised (7, 0.42) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.10 | - | recognised (8, 0.42) | topic |  | Land Encroachment | Illegal occupation of land. |
| no | 0.48 | - | recognised (9, 0.42) | topic |  | Encroachment | Illegal occupation of land |
| no | 0.01 | - | recognised (10, 0.42) | scheme |  | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| no | 0.02 | - | recognised (11, 0.42) | law |  | Reservation Bill | Legislation providing affirmative action quotas |
| no | 0.07 | - | recognised (12, 0.42) | topic |  | Indian Citizens | Persons holding citizenship of India |
| yes | 1.00 | - | llm | law |  | Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019 | Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019 *(not in text)* |
| yes | 0.99 | - | llm | institution |  | Directorate of Estates | Directorate of Estates |
| yes | 0.97 | - | llm | institution |  | Central Public Works Department | CPWD |
| no | 0.00 | - | dict | institution |  | Directorate General of Shipping | Director-General |
| no | 0.69 | - | dict | institution |  | Ministry of Urban Development | Ministry of Urban Development |
| no | 0.76 | - | dict | institution |  | Central Reserve Police Force | CRPF |
| yes | 0.84 | - | dict | institution |  | High Court | High Court |
| no | 0.78 | - | dict | place |  | Delhi | Delhi |

## Rajendra Dhedya Gavit: Motion for consideration of the Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019 (Bill passed).

2019-07-31, 795 words, state `speech`. Speech id 344510.

**Summary.** Supports the public premises eviction amendment bill, asking for faster and transparent housing allotment for MPs and strict action against illegal occupation of government properties.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Government property management | सरकारी परिसम्पत्तियां |
| yes | 0.99 | - | llm | topic |  | Eviction of unauthorized occupants | अप्राधिकृत अधिभोगियों की बेदखली |
| yes | 0.83 | - | llm | topic |  | Housing allotment | आवास आबंटित |
| no | 0.01 | - | recognised (1, 0.38) | law |  | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| yes | 0.98 | - | recognised (2, 0.39) | law |  | Law Amendment | Change to existing legislation |
| no | 0.52 | - | recognised (4, 0.40) | law |  | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| no | 0.01 | - | recognised (5, 0.40) | law |  | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.04 | - | recognised (7, 0.41) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.03 | - | recognised (9, 0.41) | scheme |  | Pradhan Mantri Awaas Yojana | Government scheme that helps poor families build or buy a home. |
| no | 0.02 | - | recognised (10, 0.41) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.05 | - | recognised (11, 0.41) | law |  | The Repealing and Amending Bill | Legislation that removes or updates laws that are no longer needed. |
| no | 0.38 | - | recognised (12, 0.41) | law |  | Housing Policy | Government decisions on residential provision |
| no | 0.05 | - | recognised (13, 0.41) | law |  | Private Members Resolution | Parliamentary proposal from individual lawmakers |
| no | 0.02 | - | recognised (14, 0.41) | law |  | Anti-Defection Law | Law that removes an elected member who switches political party. |
| no | 0.76 | - | recognised (15, 0.41) | topic |  | MP(s) Conduct | Behavior and ethics of parliament members |
| yes | 1.00 | - | llm | law |  | Public Premises (Eviction of Unauthorized Occupants) Amendment Bill, 2019 | सरकारी स्थान ( अप्राधिकृत अधिभोगियों की बेदखली ) संशोधन विधेयक, 2019 |
| yes | 0.82 | - | llm | place |  | Palghar | पालघर |
| yes | 0.94 | - | llm | place |  | Vasai-Virar-Nalasopara | वसई - विरार - नालासोपारा |
| yes | 0.56 | - | llm | place |  | Mumbai | मुंबई |
| yes | 0.95 | - | dict | place |  | Vasai-Virar | वसई-विरार |
| no | 0.03 | - | dict | scheme |  | Pradhan Mantri Awas Yojana | आवास |
| no | 0.03 | - | dict | institution |  | Public Works Department | पीडब्ल्यूडी |
| yes | 0.96 | - | dict | group |  | Government employees | सरकारी कर्मचारी |
| yes | 0.94 | - | dict | group |  | Police | पुलिस |
| no | 0.42 | - | dict | group |  | Companies | कम्पनियों |
| no | 0.30 | - | dict | group |  | Doctors | डॉक्टर्स |
| no | 0.15 | - | dict | group |  | Scheduled Tribes | आदिवासी |

## Suresh Kumar Pujari: Need to install the statue of Veer Surendra Sai, a freedom fighter, inside the Parliament premises.

2019-07-29, 180 words, state `speech`. Speech id 344955.

**Summary.** Asks to install a statue of freedom fighter Veer Surendra Sai inside the Parliament premises.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Freedom fighters commemoration | heroic sacrifices of all the unsung heroes of India |
| no | 0.06 | - | recognised (1, 0.38) | place |  | Sundargarh | District and Lok Sabha constituency in Odisha, India. |
| no | 0.07 | - | recognised (2, 0.38) | place |  | Sambalpur | District and Lok Sabha constituency in Odisha, India. |
| no | 0.05 | - | recognised (3, 0.38) | place |  | Kendujhar | District and Lok Sabha constituency in Odisha, India. The constituency is listed as Keonjhar. |
| no | 0.05 | - | recognised (4, 0.38) | place |  | Kalahandi | District and Lok Sabha constituency in Odisha, India. |
| no | 0.05 | - | recognised (5, 0.38) | place |  | Kandhamal | District and Lok Sabha constituency in Odisha, India. |
| no | 0.06 | - | recognised (6, 0.39) | place |  | Mayurbhanj | District and Lok Sabha constituency in Odisha, India. |
| no | 0.06 | - | recognised (7, 0.39) | place |  | Balangir | District and Lok Sabha constituency in Odisha, India. The constituency is listed as Bolangir. |
| no | 0.04 | - | recognised (8, 0.39) | place |  | Balasore | District and Lok Sabha constituency in Odisha, India. |
| no | 0.04 | - | recognised (9, 0.39) | place |  | Berhampur | Lok Sabha constituency in Odisha, India. |
| no | 0.04 | - | recognised (10, 0.39) | place |  | Kendrapara | District and Lok Sabha constituency in Odisha, India. |
| no | 0.03 | - | recognised (11, 0.39) | place |  | Puri | District and Lok Sabha constituency in Odisha, India. |
| no | 0.05 | - | recognised (12, 0.39) | place |  | Cuttack | District and Lok Sabha constituency in Odisha, India. |
| no | 0.20 | - | llm | person |  | Mahatma Gandhi | Mahatma Gandhi |
| yes | 1.00 | - | llm | person |  | Veer Surendra Sai | सुरेन्द्र साई |
| no | 0.01 | - | dict | role |  | President of India | राष्ट्रपति |
| no | 0.77 | - | dict | group |  | British | अं ग्रेजों |

## Anurag Singh Thakur: Combined discussion on Statutory Resolution regarding Disapproval of Banning of Unregulated Deposit Schemes, Ordinance 2019 (No. 7 of 2019) and Banning of Unregulated Deposit Schemes Bill, 2019. (Resolution negatived and Bill Passed).

2019-07-24, 779 words, state `speech`. Speech id 345373.

**Summary.** Moves the Banning of Unregulated Deposit Schemes Bill, 2019 for consideration and passage to protect poor depositors from fraudulent schemes.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Unregulated deposit schemes | Banning of Unregulated Deposit Schemes Bill, 2019 *(not in text)* |
| yes | 0.98 | - | recognised (1, 0.38) | topic |  | Unregulated Deposit | Unsecured deposits collected illegally without government oversight or insurance. |
| no | 0.02 | - | recognised (2, 0.41) | law |  | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.29 | - | recognised (3, 0.41) | topic |  | Bank Frauds | Fraudulent schemes in banking sector. |
| yes | 0.93 | - | recognised (4, 0.41) | topic |  | Scams | Fraudulent schemes to deceive and defraud people. |
| no | 0.38 | - | recognised (5, 0.42) | topic |  | Chit Fund Scheme | Informal savings and credit arrangement among groups |
| no | 0.02 | - | recognised (6, 0.42) | topic |  | Beggars & Begging | Persons seeking financial assistance and regulation of solicitation practices. |
| no | 0.76 | - | recognised (7, 0.42) | topic |  | Fraudulent Practice | Deliberate deception or dishonest schemes carried out to gain money or unfair advantage. |
| no | 0.36 | - | recognised (8, 0.42) | institution |  | Chit Fund Companies | Organizations managing rotating savings schemes. |
| no | 0.58 | - | recognised (9, 0.43) | topic |  | Bank Deposits | Money placed in bank accounts |
| no | 0.01 | - | recognised (10, 0.43) | law |  | Securities Markets Code Bill, 2025 | Financial market regulation legislation |
| no | 0.02 | - | recognised (12, 0.43) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.06 | - | recognised (13, 0.43) | institution |  | Securities and Exchange Board of India (SEBI) | Regulatory body for stock market and securities regulation |
| yes | 0.46 | - | llm | law |  | Banning of Unregulated Deposit Schemes Act | Banning of Unregulated Deposit Schemes Bill, 2019 *(not in text)* |
| yes | 0.95 | - | llm | institution |  | Standing Committee on Finance | Standing Committee for Finance *(not in text)* |
| yes | 0.92 | - | llm | institution |  | Parliament | लोक सभा |
| yes | 0.91 | - | dict | institution |  | Standing Committee | स्टैंडिंग कमेटी |
| yes | 1.00 | - | dict | group |  | Poor | गरीब |
| yes | 0.89 | - | dict | role |  | President of India | राष्ट्रपति |
| no | 0.07 | - | dict | person |  | Nirmala Sitharaman | Nirmala Sitharaman |
| yes | 1.00 | - | dict | group |  | Depositors | depositors |

## Uday Pratap Singh: Need to include Kaurav Samaj in OBC List.

2019-06-26, 276 words, state `speech`. Speech id 348920.

**Summary.** Requests the inclusion of the Kaurav community in the Central Other Backward Classes list.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Inclusion in OBC list | अन्य पिछड़ा वर्ग की सूची में शामिल हो |
| yes | 0.98 | - | recognised (1, 0.32) | topic |  | Other Backward Classes (OBCs) | A group of communities that India officially recognises as socially disadvantaged. |
| yes | 0.98 | - | recognised (2, 0.35) | topic |  | Backward Classes | Communities that are socially and economically disadvantaged. |
| yes | 0.96 | - | recognised (3, 0.35) | law |  | O.B.C. | Law providing reservations for other backward classes. |
| no | 0.05 | - | recognised (4, 0.36) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.05 | - | recognised (5, 0.36) | law |  | SCs List | Official listing of scheduled castes. |
| no | 0.79 | - | recognised (6, 0.36) | topic |  | Central List | An official government list, such as the list of backward classes eligible for reservation benefits. |
| no | 0.04 | - | recognised (7, 0.36) | topic |  | Scheduled Castes | Communities of India officially recognised as a disadvantaged group. |
| no | 0.08 | - | recognised (8, 0.37) | law |  | SCs & STs lists | Lists of scheduled castes and scheduled tribes. |
| no | 0.09 | - | recognised (9, 0.37) | institution |  | National Commission for Backward Classes | A government body that works for social justice for backward communities. |
| no | 0.01 | - | recognised (10, 0.37) | topic |  | Banjara Community | Historically nomadic community |
| yes | 0.91 | - | recognised (11, 0.38) | topic |  | Classification | The sorting of people or castes into official government categories, often for reservation benefits. |
| no | 0.08 | - | recognised (12, 0.38) | law |  | Mandal Commission Report | Document recommending reservation for backward castes. |
| yes | 1.00 | - | llm | group |  | Kaurav | कौरव समाज |
| no | 0.21 | - | llm | group |  | Anjana | अंजना समाज |
| yes | 0.72 | - | llm | place |  | Narsinghpur | नरसिंहपुर |
| yes | 0.72 | - | llm | place |  | Hoshangabad | होशंगाबाद |
| no | 0.15 | - | llm | place |  | Ujjain | उज्जैन |
| yes | 1.00 | - | dict | group |  | Other Backward Classes | पिछड़ा वर्ग |
| no | 0.01 | - | dict | place |  | Kalyan | कल्याण |
| no | 0.40 | - | dict | law |  | Mahabharata | महाभारत |
| yes | 1.00 | - | dict | group |  | Children | बच्चों |
| no | 0.01 | - | dict | scheme |  | PRAGATI | प्रगति |
| no | 0.70 | - | dict | place |  | Raisen | रायसेन |
| no | 0.77 | - | dict | place |  | Bhind | भिंड |
| no | 0.33 | - | dict | place |  | Rajasthan | राजस्थान |

