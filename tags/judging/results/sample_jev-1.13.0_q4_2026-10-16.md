# Relevance check review: sample

Model `jev-1.13.0`, questions `q4`, written on 2026-10-16. 15 speeches. For a topic, `P(keep)` is P(central or supporting), kept at 0.6. For a named item, `P(keep)` is P(part of the member's point), kept at 0.6 together with `P(refers)` at 0.6. `Model type` shows the model's type only when it differs from the extraction type. `Source`: `llm` = the extraction, `dict` = the entity dictionary found the words in the text, `summary` = a tag near the summary (its rank and distance in brackets). Write keep or drop in the `review` column of `sample_jev-1.13.0_q4_2026-10-16.tsv`. 363 items carry an earlier manual mark already.

## Rajendra Agrawal: Need to make Kali river, a tributary of river Ganga, pollution free - Laid

2019-01-07, 184 words, state `speech`. Speech id 260741.

**Summary.** Requests the government to prioritize anti-pollution projects to clean the Kali river, a tributary of the Ganga.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | River Pollution | प्रदूषण |
| yes | 0.99 | - | llm | topic |  | River Cleaning | प्रदूषण मुक्त करने |
| yes | 0.98 | - | summary (1, 0.35) | scheme | ? | Namami Ganga Mission | Government mission to clean and restore the Ganga river. Formerly the Ganga Action Plan. |
| yes | 0.99 | - | summary (2, 0.37) | topic |  | River Cleaning | Efforts to remove pollution and waste from rivers. |
| no | 0.04 | - | summary (3, 0.38) | institution | ? | National Ganga River Basin Authority | A government body set up to clean and manage the Ganga river. |
| no | 0.00 | - | summary (4, 0.39) | place | ? | Bhagirathi River | River in Himalayas, source of Ganges River |
| yes | 0.98 | - | summary (5, 0.39) | place | ? | Ganga River | Major river in India |
| yes | 0.99 | - | summary (6, 0.39) | topic |  | River Conservation | General government effort to protect and restore rivers. |
| yes | 0.99 | - | summary (7, 0.40) | topic |  | River Pollution | Contamination of rivers with waste or harmful substances. |
| no | 0.00 | - | summary (8, 0.41) | place | ? | Haridwar | District and Lok Sabha constituency in Uttarakhand, India. |
| no | 0.00 | - | summary (9, 0.41) | place | ? | Uttarkashi | District in Uttarakhand, India. |
| no | 0.00 | - | summary (10, 0.41) | place | ? | Damodar River | River in eastern India used for irrigation and power |
| no | 0.01 | - | summary (11, 0.42) | scheme | ? | Swachh Bharat Abhiyan | Government mission to improve sanitation and cleanliness across India. |
| yes | 0.99 | - | summary (12, 0.42) | topic |  | Pollution Control | Government action to reduce and prevent pollution of air, water, or land. |
| yes | 1.00 | 0.61 | llm | place |  | Kali River | काली नदी |
| yes | 1.00 | 0.89 | llm | place |  | Ganga River | गंगा |
| yes | 1.00 | 0.89 | llm | scheme |  | Namami Gange Programme | नमामि गंगे |
| yes | 0.97 | 0.90 | llm | institution | scheme | National Mission for Clean Ganga | नेशनल मिशन फॉर क्लीन गंगा (NMCG) |
| yes | 1.00 | 0.91 | llm | place |  | Uttar Pradesh | उत्तर प्रदेश |
| yes | 0.98 | 0.87 | llm | place |  | Muzaffarnagar | मुजफफरनगर |
| yes | 0.80 | 0.82 | llm | place |  | Meerut | मेरठ |
| yes | 0.93 | 0.83 | llm | place |  | Kannauj | कन्नौज |
| no | 0.85 | 0.13 | dict | place |  | Krishna River | कृष्णा |

## Amit Shah: Combined discussion on Statutory Resolution regarding approval of Proclamation by President in Relation to State of Jammu and Kashmir (Resolution Adopted) and Statutory Resolution regarding Disapproval of Jammu and Kashmir Reservation (Amendment) Ordinance, 2019 (No. 8 of 2019) (Resolution negatived) and passing of the Jammu and Kashmir Reservation (Amendment) Bill, 2019 (Discussion concluded and Bill Passed).

2019-06-28, 2394 words, state `speech`. Speech id 348672.

**Summary.** Moves statutory resolutions to extend President's Rule in Jammu and Kashmir by six months and to amend the state's reservation laws to benefit residents along the international border.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | President's Rule | राष्ट्रपति शासन |
| yes | 0.99 | - | llm | topic |  | Reservation policy | आरक्षण |
| yes | 0.98 | - | llm | topic |  | Elections | चुनाव |
| yes | 0.99 | - | llm | topic |  | Border security and shelling | सीज़फायर |
| yes | 0.91 | - | llm | topic |  | Local governance | पंचायत |
| no | 0.06 | - | summary (1, 0.35) | law | ? | Article 370 | Constitutional article on special status of Jammu and Kashmir |
| yes | 0.98 | - | summary (2, 0.35) | law | ? | Article 356 | Constitutional provision for president's rule. |
| yes | 1.00 | - | summary (3, 0.36) | law | ? | President's Rule | Constitutional rule that lets the central government run a state directly. |
| yes | 0.98 | - | summary (4, 0.36) | law | ? | Reservation Policy | Constitutional rules that set aside seats and jobs for disadvantaged groups. |
| yes | 0.97 | - | summary (5, 0.37) | law | ? | Reservation Bill | Legislation providing affirmative action quotas |
| yes | 0.98 | - | summary (6, 0.37) | law | ? | Reservation Rules | Regulations for affirmative action in education and jobs |
| yes | 0.99 | - | summary (7, 0.38) | place | ? | Jammu & Kashmir | State in the northern region of India. |
| yes | 0.94 | - | summary (8, 0.38) | law | ? | Employment Reservation | Allocation of jobs by identity |
| yes | 0.91 | - | summary (9, 0.38) | law | ? | Statutory Resolutions | Formal motions passed by parliament with legal effect. |
| no | 0.00 | - | summary (10, 0.39) | law | ? | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.00 | - | summary (11, 0.39) | law | ? | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.01 | - | summary (12, 0.39) | law | ? | Women's Reservation | Constitutional provision for reserved seats for women |
| yes | 1.00 | 0.92 | llm | place |  | Jammu and Kashmir | जम्मू - कश्मीर |
| yes | 1.00 | 0.88 | llm | law |  | Jammu and Kashmir Reservation Act, 2004 | जम्मू - कश्मीर आरक्षण अधिनियम, 2004 *(not in text)* |
| yes | 0.98 | 0.90 | llm | institution |  | Election Commission | चुनाव आयोग |
| yes | 0.72 | 0.89 | llm | place |  | Ladakh | लद्दाख |
| yes | 1.00 | 0.91 | llm | place |  | Pakistan | पाकिस्तान |
| yes | 0.67 | 0.87 | llm | group |  | Gujjar Bakarwal | गुर्जर बकरवाल |
| yes | 0.64 | 0.90 | llm | person |  | Rajnath Singh | श्रीमान् राजनाथ सिंह जी |
| no | 0.42 | 0.91 | llm | person |  | Narendra Modi | नरेन्द्र मोदी |
| yes | 1.00 | 0.88 | dict | place |  | Jammu | जम्मू |
| yes | 1.00 | 0.87 | dict | role |  | President of India | राष्ट्रपति |
| yes | 1.00 | 0.83 | dict | role |  | Governor | राज्यपाल |
| yes | 1.00 | 0.88 | dict | group |  | Children | बच्चों |
| no | 0.74 | 0.10 | dict | law |  | Constitution of India | संविधान |
| no | 0.17 | 0.45 | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| yes | 0.96 | 0.87 | dict | group | ? | Opposition | विपक्ष |
| yes | 0.89 | 0.89 | dict | scheme | other | Amarnath Yatra | अमरनाथ यात्रा |

## Kunwar Danish Ali: Combined discussion on Statutory Resolution regarding approval of Proclamation by President in Relation to State of Jammu and Kashmir (Resolution Adopted) and Statutory Resolution regarding Disapproval of Jammu and Kashmir Reservation (Amendment) Ordinance, 2019 (No. 8 of 2019) (Resolution negatived) and passing of the Jammu and Kashmir Reservation (Amendment) Bill, 2019 (Discussion concluded and Bill Passed).

2019-06-28, 671 words, state `speech`. Speech id 348687.

**Summary.** Discusses the sensitive situation in Jammu and Kashmir, urging the government to restore a democratically elected government, uphold human touch, and ensure welfare for border residents.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.67 | - | llm | topic |  | President's rule | धारा 356 |
| yes | 0.81 | - | llm | topic |  | Assembly elections | विधान सभा का चुनाव |
| yes | 0.91 | - | llm | topic |  | Reservation | रिजर्वेशन में अमेंडमेंट |
| no | 0.50 | - | llm | topic |  | Border security and welfare | इंटरनेशनल बार्डर |
| yes | 0.99 | - | llm | topic |  | Peace and human touch | इंसानियत, कश्मीरियत |
| no | 0.11 | - | summary (1, 0.38) | law | ? | Article 370 | Constitutional article on special status of Jammu and Kashmir |
| yes | 0.99 | - | summary (2, 0.39) | place | ? | Jammu & Kashmir | State in the northern region of India. |
| no | 0.58 | - | summary (3, 0.39) | place | ? | Jammu | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (4, 0.39) | institution | ? | Hurriyat Conference | An alliance of separatist political groups based in Jammu and Kashmir. |
| no | 0.00 | - | summary (5, 0.39) | place | ? | Udhampur | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (6, 0.40) | place | ? | Baramulla | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (7, 0.40) | institution | ? | National Conference | Political party in Kashmir and Jammu region |
| no | 0.01 | - | summary (8, 0.40) | place | ? | Srinagar | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (9, 0.41) | place | ? | Pakistan Occupied Kashmir (PoK) | Part of the former Jammu and Kashmir region under Pakistani control. |
| no | 0.00 | - | summary (10, 0.41) | place | ? | Kathua | District in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (11, 0.42) | place | ? | Pulwama | District in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (12, 0.42) | topic |  | Kashmiri Migrants | People who left the Kashmir region and now live elsewhere. |
| yes | 1.00 | 0.94 | llm | place |  | Jammu and Kashmir | जम्मू - कश्मीर |
| no | 0.17 | 0.92 | llm | person |  | Sheikh Abdullah | शेख अब्दुल्ला साहब |
| no | 0.03 | 0.95 | llm | person |  | Indira Gandhi | श्रीमती इंदिरा गांधी जी |
| no | 0.02 | 0.94 | llm | person |  | Rajiv Gandhi | श्री राजीव गांधी जी |
| no | 0.10 | 0.96 | llm | person |  | Narendra Modi | आदरणीय प्रधान मंत्री नरेन्द्र मोदी जी |
| yes | 0.75 | 0.85 | llm | person |  | Atal Bihari Vajpayee | वाजपेयी जी |
| no | 0.38 | 0.93 | llm | person |  | H. D. Deve Gowda | श्री एच. डी. देवेगौड़ा जी |
| yes | 0.95 | 0.87 | llm | institution |  | Election Commission of India | चुनाव आयोग |
| yes | 0.98 | 0.87 | dict | place |  | Jammu | जम्मू |
| no | 0.88 | 0.40 | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| no | 0.21 | 0.86 | dict | place |  | Rajouri | राजौरी |
| yes | 0.82 | 0.93 | dict | group | institution | Bahujan Samaj Party | बहुजन समाज पार्टी |
| yes | 0.96 | 0.90 | dict | law |  | Article 356 | धारा 356 |

## Nama Nageswara Rao: Combined discussion on Statutory Resolution regarding approval of Proclamation by President in Relation to State of Jammu and Kashmir (Resolution Adopted) and Statutory Resolution regarding Disapproval of Jammu and Kashmir Reservation (Amendment) Ordinance, 2019 (No. 8 of 2019) (Resolution negatived) and passing of the Jammu and Kashmir Reservation (Amendment) Bill, 2019 (Discussion concluded and Bill Passed).

2019-06-28, 413 words, state `speech`. Speech id 348688.

**Summary.** Supports the Jammu and Kashmir Reservation (Amendment) Bill, 2019, highlighting the need for employment and development in the region.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.94 | - | llm | topic |  | Reservation | रिजर्वेशन |
| yes | 0.98 | - | llm | topic |  | Border safety and bunkers | बंकर्स |
| yes | 0.72 | - | llm | topic |  | Youth employment and industrial development | युवाओं के पास नौकरी नहीं थी |
| yes | 0.73 | - | llm | topic |  | Panchayat elections | पंचायत के चुनाव |
| no | 0.07 | - | llm | topic |  | Tourism | टूरिज्म |
| yes | 0.71 | - | summary (1, 0.36) | law | ? | Employment Reservation | Allocation of jobs by identity |
| yes | 0.92 | - | summary (2, 0.36) | law | ? | Reservation Bill | Legislation providing affirmative action quotas |
| no | 0.11 | - | summary (3, 0.37) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.09 | - | summary (4, 0.38) | law | ? | Article 370 | Constitutional article on special status of Jammu and Kashmir |
| yes | 0.99 | - | summary (5, 0.38) | place | ? | Jammu & Kashmir | State in the northern region of India. |
| yes | 0.90 | - | summary (6, 0.39) | law | ? | Reservation Policy | Constitutional rules that set aside seats and jobs for disadvantaged groups. |
| no | 0.00 | - | summary (7, 0.39) | scheme | ? | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| no | 0.57 | - | summary (8, 0.39) | place | ? | Jammu | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| yes | 0.87 | - | summary (9, 0.39) | law | ? | Reservation Rules | Regulations for affirmative action in education and jobs |
| no | 0.00 | - | summary (10, 0.39) | scheme | ? | Deen Dayal Upadhyaya Antyodaya Yojana | Government scheme for poverty reduction through skills and self-employment. |
| no | 0.00 | - | summary (11, 0.39) | scheme | ? | Pradhan Mantri Jan Vikas Karyakram (PMJVK) | Government program for the development of minority communities. |
| no | 0.00 | - | summary (12, 0.39) | place | ? | Udhampur | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| yes | 1.00 | 0.93 | llm | place |  | Jammu and Kashmir | जम्मू एण्ड कश्मीर |
| yes | 0.92 | 0.76 | llm | law |  | Jammu and Kashmir Reservation (Amendment) Bill, 2019 | रिजर्वेशन पर जो बिल आया है |
| yes | 0.63 | 0.62 | llm | person |  | Kalvakuntla Chandrashekar Rao | के. सी. आर. जी |
| no | 0.40 | 0.37 | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| no | 0.39 | 0.81 | dict | group | institution | Opposition | विपक्ष |
| yes | 0.77 | 0.77 | dict | group | institution | United Progressive Alliance | यू. पी. ए. |
| yes | 0.97 | 0.64 | dict | group |  | Children | बच्चों |
| yes | 0.90 | 0.81 | dict | group |  | Students | स्टूडेंट्स |
| yes | 0.95 | 0.86 | dict | group |  | Youth | युवाओं |
| no | 0.29 | 0.81 | dict | group |  | Other Backward Classes | ओ.बी.सी. |
| no | 0.23 | 0.82 | dict | group |  | Scheduled Tribes | एस. टी. |

## Uttam Kumar Nalamada Reddy: Need to meet the assurances given to the state of Telegana by Central Government.

2019-07-09, 186 words, state `speech`. Speech id 347763.

**Summary.** Urges the Central Government to fulfill pending assurances given to Telangana in the Andhra Pradesh Reorganisation Act, including establishing a railway coach factory, steel plant, and tribal university.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | State reorganization assurances | assurances given to the state of Telegana *(not in text)* |
| no | 0.03 | - | llm | topic |  | Railway coach factory | Railway Coach Factory was assured at Kazipet |
| no | 0.03 | - | llm | topic |  | Steel plant | Steel Plant was assured at Bayyaram |
| yes | 0.98 | - | llm | topic |  | Tribal university | Tribal University was assured in the Act |
| yes | 1.00 | - | summary (1, 0.38) | place | ? | Telangana | State in southern India, formed from the former Andhra Pradesh. |
| no | 0.00 | - | summary (2, 0.39) | law | ? | Article 371 | Constitutional provisions for northeastern states' special status. |
| no | 0.31 | - | summary (3, 0.40) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.15 | - | summary (4, 0.41) | topic |  | Tribal Sub Plan, Centre-State Relations | Government program for tribal development and governance. |
| yes | 0.97 | - | summary (5, 0.41) | law | ? | States Reorganisation | Restructuring or redrawing of state boundaries and administrative divisions. |
| no | 0.00 | - | summary (6, 0.41) | law | ? | SCs & STs lists | Lists of scheduled castes and scheduled tribes. |
| no | 0.00 | - | summary (7, 0.41) | topic |  | Telugu Language | Language spoken in Andhra Pradesh and Telangana regions of India. |
| no | 0.00 | - | summary (8, 0.41) | law | ? | Reservation Bill | Legislation providing affirmative action quotas |
| no | 0.00 | - | summary (9, 0.41) | topic |  | Rehabilitation | Support programs to help people recover from disasters or other hardships. |
| no | 0.06 | - | summary (10, 0.42) | institution | ? | Integral Coach Factory | State manufacturer of railway coaches |
| no | 0.03 | - | summary (11, 0.42) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| no | 0.00 | - | summary (12, 0.42) | law | ? | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| yes | 1.00 | 0.91 | llm | place |  | Telangana | Telangana |
| yes | 1.00 | 0.87 | llm | law |  | Andhra Pradesh Reorganisation Act | Andhra Pradesh Reorganisation Act |
| yes | 0.79 | 0.77 | llm | place |  | Kazipet | Kazipet |
| yes | 0.81 | 0.65 | llm | place |  | Bayyaram | Bayyaram |
| yes | 0.93 | 0.60 | dict | group |  | Scheduled Tribes | tribal |
| yes | 0.92 | 0.90 | dict | role |  | President of India | President of India |
| yes | 0.96 | 0.81 | dict | law | other | Union Budget | Budget |
| no | 1.00 | 0.58 | dict | institution |  | Ministry of Home Affairs | Home Minister |

## Dhanush M Kumar: Issue regarding plight of farmers in the country.

2019-07-18, 286 words, state `speech`. Speech id 346044.

**Summary.** Highlights the plight of farmers in the country and demands remunerative prices for their agricultural produce instead of financial support or subsidies.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Agricultural pricing | remunerative price for their agricultural produce |
| yes | 0.99 | - | llm | topic |  | Farmers' distress | plight of farmers of this country |
| no | 0.14 | - | llm | topic |  | Farmers' suicide | forced to commit suicides |
| no | 0.47 | - | llm | topic |  | Agricultural subsidies | subsidy for fertilizers and raw material |
| yes | 1.00 | - | summary (1, 0.29) | topic |  | Remunerative Prices | Fair prices for agricultural products that provide adequate farmer income. |
| yes | 0.81 | - | summary (2, 0.31) | scheme | ? | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| yes | 0.87 | - | summary (3, 0.32) | law | ? | Minimum Support Prices | Price floor for agricultural commodities |
| yes | 1.00 | - | summary (4, 0.33) | topic |  | Support Prices | Guaranteed minimum prices. |
| yes | 1.00 | - | summary (5, 0.33) | topic |  | Agricultural Prices | Price levels for agricultural produce |
| no | 0.00 | - | summary (6, 0.34) | topic |  | Zero Budget Farming | Agricultural approach minimizing external input costs. |
| yes | 0.99 | - | summary (7, 0.35) | topic |  | Farmers' Grievances | Complaints from agricultural workers |
| no | 0.34 | - | summary (8, 0.35) | topic |  | Farmers' Agitation | Farm worker protests and demonstrations. |
| no | 0.00 | - | summary (9, 0.35) | institution | ? | Swaminathan Commission Report | Report from a government commission that recommended higher crop support prices. |
| no | 0.01 | - | summary (10, 0.35) | institution | ? | Commission for Agricultural Costs and Prices | Government body that recommends minimum support prices for farm crops. |
| yes | 0.99 | - | summary (11, 0.35) | topic |  | Farmers' Welfare | Government support and welfare programs for farmers. |
| no | 0.11 | - | summary (12, 0.35) | scheme | ? | Pradhan Mantri Kisan Samman Nidhi Yojana | Government scheme that gives direct cash payments to farming families. |
| no | 0.04 | 0.80 | llm | place |  | Tenkasi | Tenkasi parliamentary constituency |
| yes | 0.84 | 0.87 | llm | law | other | Thirukkural | Thirukkural |
| yes | 1.00 | 0.77 | llm | group |  | Farmers | farmers |
| no | 0.01 | 0.89 | llm | person |  | M. K. Stalin | Thalapathi Thiru M.K Stalin |
| no | 0.00 | 0.87 | llm | person |  | Udhayanidhi Stalin | Thiru Udhayanidhi Stalin |
| no | 0.56 | 0.53 | dict | group |  | Manufacturers | manufacturers |
| no | 0.00 | 0.50 | dict | group | institution | Youth | youth |

## Bharatiben Dhirubhai Shiyal: Need to start morning flight from Bhavnagar to Mumbai.

2019-07-22, 101 words, state `speech`. Speech id 345769.

**Summary.** Requests the introduction of a morning flight from Bhavnagar to Mumbai to boost connectivity for trade, tourism, and industry.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Air connectivity | सुबह की फ्लाइट |
| yes | 1.00 | - | summary (1, 0.37) | place | ? | Bhavnagar | District and Lok Sabha constituency in Gujarat, India. |
| no | 0.00 | - | summary (2, 0.41) | scheme | ? | Sagarmala Project | Government plan to develop coastal ports and facilities. |
| yes | 1.00 | - | summary (3, 0.41) | topic |  | Air Connectivity | How well places are linked by air routes. |
| no | 0.00 | - | summary (4, 0.41) | scheme | ? | Vocal for Local | Promoting Indian-made goods and local businesses |
| yes | 1.00 | - | summary (5, 0.41) | topic |  | Transport Development | Improvement of transportation infrastructure. |
| yes | 0.85 | - | summary (6, 0.41) | topic |  | Domestic airports | Airports that handle flights within India only. |
| no | 0.00 | - | summary (7, 0.41) | place | ? | Jamnagar | District and Lok Sabha constituency in Gujarat, India. |
| no | 0.00 | - | summary (8, 0.41) | institution | ? | Vande Bharat Express | High-speed rail service connecting Indian cities |
| yes | 1.00 | - | summary (9, 0.41) | topic |  | Domestic Flights | Air travel between airports within the same country. |
| yes | 1.00 | - | summary (10, 0.41) | topic |  | Air Links | Flight routes that connect two places. |
| no | 0.00 | - | summary (11, 0.42) | scheme | ? | UDAAN Scheme | Government scheme that supports small and medium businesses. |
| no | 0.00 | - | summary (12, 0.42) | institution | ? | Pawan Hans Ltd | A government-owned company that runs helicopter services. |
| yes | 1.00 | 0.93 | llm | place |  | Bhavnagar | भावनगर |
| yes | 1.00 | 0.95 | llm | place |  | Mumbai | मुंबई |
| no | 0.38 | 0.82 | llm | place |  | Alang Ship Breaking Yard | शिपब्रेकिंग यार्ड |
| no | 0.15 | 0.70 | llm | place |  | Velavadar Blackbuck National Park | ब्लैक बग की नेशनल सेंन्चुरी |
| no | 0.12 | 0.87 | llm | place |  | Pipavav Port | पीपावा पोर्ट |
| no | 0.14 | 0.86 | llm | place |  | Palitana | पालीताना |

## Adhir Ranjan Chowdhury: Regarding US President's reported mediation claim on Kashmir.

2019-07-24, 577 words, state `speech`. Speech id 345470.

**Summary.** Demands a statement from the Prime Minister in Parliament regarding the US President's reported claim of mediation on the Kashmir issue.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Kashmir mediation claim | कश्मीर मुद्दे पर किसी तृतीय पक्ष का हस्तक्षेप नहीं होगा |
| yes | 0.86 | - | llm | topic |  | Bilateral relations | शिमला एग्रीमेंट के मुताबिक कश्मीर मुद्दा बाइलेटरल है *(not in text)* |
| yes | 0.94 | - | summary (1, 0.41) | topic |  | Indo-US relations | Relations between India and the United States. |
| yes | 0.63 | - | summary (2, 0.42) | topic |  | Statement | A formal announcement made by a minister in parliament. |
| no | 0.18 | - | summary (3, 0.42) | topic |  | Members | Participants or representatives in a group. Meaning here is unclear. |
| no | 0.01 | - | summary (4, 0.42) | law | ? | Article 370 | Constitutional article on special status of Jammu and Kashmir |
| no | 0.05 | - | summary (5, 0.42) | role | ? | President | Constitutional de jure head of state of India, as distinct from the Prime Minister, the elected de facto head. |
| yes | 0.71 | - | summary (6, 0.42) | institution | ? | Parliament | The body that makes India's national laws. |
| yes | 0.97 | - | summary (7, 0.42) | topic |  | Indo-Pak Relation | Relations between India and Pakistan. |
| no | 0.00 | - | summary (8, 0.42) | place | ? | Srinagar | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.24 | - | summary (9, 0.42) | topic |  | Observation | A formal note made by parliament on a matter. |
| yes | 1.00 | - | summary (10, 0.42) | role | ? | Prime Minister | Elected de facto head of state of India, as distinct from the President, the de jure constitutional head. |
| no | 0.16 | - | summary (11, 0.42) | place | ? | Pakistan Occupied Kashmir (PoK) | Part of the former Jammu and Kashmir region under Pakistani control. |
| no | 0.16 | - | summary (12, 0.43) | law | ? | Private Members Resolution | Parliamentary proposal from individual lawmakers |
| yes | 1.00 | 0.94 | llm | person |  | Narendra Modi | नरेन्द्र मोदी जी |
| yes | 1.00 | 0.93 | llm | person |  | Donald Trump | ट्रंप साहब |
| yes | 0.84 | 0.94 | llm | person |  | Indira Gandhi | इंदिरा गाँधी जी |
| yes | 0.99 | 0.92 | llm | law | other | Simla Agreement | शिमला एग्रीमेंट |
| yes | 0.99 | 0.93 | llm | place |  | United States | अमेरिका |
| yes | 0.89 | 0.92 | llm | place |  | Pakistan | पाकिस्तान |
| yes | 1.00 | 0.90 | llm | place | ? | Kashmir | कश्मीर |
| yes | 0.69 | 0.82 | llm | person |  | Zulfikar Ali Bhutto | भुट्टो |
| yes | 1.00 | 0.92 | dict | law | other | Shimla Agreement | शिमला एग्रीमेंट |
| no | 0.09 | 0.03 | dict | role |  | President of India | राष्ट्रपति |

## Rajnath Singh: Regarding US President's reported mediation claim on Kashmir.

2019-07-24, 444 words, state `speech`. Speech id 345472.

**Summary.** Assures the House that the Prime Minister never asked for US mediation on Kashmir, emphasizes national self-respect, and states that talks with Pakistan will include Pakistan-occupied Kashmir.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Kashmir mediation claim | कश्मीर के सवाल पर किसी की मध्यस्थता |
| yes | 0.72 | - | llm | topic |  | India-Pakistan relations | पाकिस्तान के साथ |
| yes | 0.91 | - | llm | topic |  | National sovereignty and pride | राष्ट्रीय स्वाभिमान |
| no | 0.08 | - | summary (1, 0.39) | place | ? | Pakistan Occupied Kashmir (PoK) | Part of the former Jammu and Kashmir region under Pakistani control. |
| no | 0.09 | - | summary (2, 0.42) | law | ? | Shimla Agreement | Agreement between India and Pakistan on the border after the 1971 war. |
| no | 0.00 | - | summary (3, 0.42) | place | ? | Srinagar | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| yes | 0.62 | - | summary (4, 0.42) | topic |  | Indo-Pak Relation | Relations between India and Pakistan. |
| no | 0.00 | - | summary (5, 0.42) | law | ? | Article 370 | Constitutional article on special status of Jammu and Kashmir |
| yes | 0.99 | - | summary (6, 0.42) | place | ? | Jammu & Kashmir | State in the northern region of India. |
| no | 0.12 | - | summary (7, 0.42) | place | ? | Indo-Pak Border | Border region between India and Pakistan |
| yes | 0.89 | - | summary (8, 0.42) | topic |  | Negotiations | Formal talks between countries to reach an agreement. |
| no | 0.00 | - | summary (9, 0.42) | topic |  | Kargil War | A military conflict fought between India and Pakistan in 1999. |
| no | 0.00 | - | summary (10, 0.43) | place | ? | Udhampur | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | summary (11, 0.43) | institution | ? | Hurriyat Conference | An alliance of separatist political groups based in Jammu and Kashmir. |
| no | 0.07 | - | summary (12, 0.43) | place | ? | Jammu | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| yes | 0.98 | 0.93 | llm | place |  | United States | अमेरिका |
| yes | 0.99 | 0.92 | llm | place |  | Pakistan | पाकिस्तान |
| yes | 0.99 | 0.63 | llm | place |  | Jammu and Kashmir | कश्मीर |
| yes | 0.99 | 0.93 | llm | person |  | Donald Trump | मिस्टर ट्रम्प |
| yes | 0.95 | 0.93 | llm | person |  | Narendra Modi | प्रधान मंत्री मोदी जी |
| yes | 1.00 | 0.92 | llm | person |  | S. Jaishankar | विदेश मंत्री श्री जयशंकर जी |
| yes | 1.00 | 0.89 | llm | law | other | Shimla Agreement | शिमला समझौते |
| yes | 0.98 | 0.91 | llm | place |  | Pakistan-administered Kashmir | पाक अधिकृत जम्मू - कश्मीर |
| no | 0.12 | 0.05 | dict | role |  | President of India | राष्ट्रपति |
| no | 0.93 | 0.33 | dict | institution |  | Ministry of External Affairs | विदेश मंत्री |
| no | 0.10 | 0.02 | dict | scheme | other | Aadhaar | आधार |
| no | 0.17 | 0.04 | dict | place | ? | Surat | सूरत |

## Pinaki Misra: Secretary General reported a message from Rajya Sabha regarding passing of the Motor Vehicles (Ammendment) Bill,2019.

2019-08-01, 955 words, state `speech`. Speech id 344219.

**Summary.** Supports the Arbitration and Conciliation (Amendment) Bill, 2019, while raising queries regarding the body corporate status of the Arbitration Council, the inclusion of foreign arbitrators, and strict timelines.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Arbitration | Indian arbitration system |
| yes | 0.96 | - | llm | topic |  | Arbitration Council | Arbitration Council |
| yes | 0.98 | - | llm | topic |  | Foreign Arbitrators | foreigners can also be arbitrators |
| yes | 0.94 | - | summary (1, 0.36) | institution | ? | Arbitration Council of India | Body resolving disputes through arbitration. |
| no | 0.00 | - | summary (2, 0.42) | law | ? | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| yes | 0.94 | - | summary (3, 0.42) | law | ? | Law Amendment | Change to existing legislation |
| no | 0.00 | - | summary (4, 0.42) | law | ? | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.00 | - | summary (5, 0.43) | law | ? | Citizens Amendment Act (CAA) | Law amending citizenship provisions for religious minorities from neighboring countries. |
| no | 0.20 | - | summary (6, 0.43) | law | ? | Arbitration Agreement | Legal contract for settling disputes without court |
| yes | 0.98 | - | summary (7, 0.44) | topic |  | Arbitration | Dispute resolution through neutral mediators. |
| no | 0.00 | - | summary (8, 0.44) | institution | ? | Ficci | Federation of Indian Chambers of Commerce and Industry. A non-governmental trade association and advocacy group in India. |
| no | 0.00 | - | summary (9, 0.44) | institution | ? | Lok Adalats | Alternative dispute resolution forums |
| no | 0.00 | - | summary (10, 0.44) | institution | ? | National Company Law Appellate Tribunal (NCLAT) | Higher court for corporate and commercial law appeals |
| no | 0.00 | - | summary (11, 0.44) | law | ? | The Nari Shakti Vandan Adhiniyam | Law that reserves seats for women in Parliament and state assemblies. |
| no | 0.00 | - | summary (12, 0.44) | law | ? | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| yes | 0.76 | 0.76 | llm | law |  | Arbitration and Conciliation Act | Arbitration Act, 1996 |
| no | 0.91 | 0.50 | llm | institution |  | High-Level Committee to Review Institutionalisation of Arbitration Mechanism in India | High-Level Committee |
| no | 0.99 | 0.57 | llm | law |  | Companies Act | Companies Act |
| no | 0.17 | 0.86 | llm | place |  | United Kingdom | U.K. |
| no | 0.13 | 0.86 | llm | place |  | Hong Kong | Hong Kong |
| no | 0.12 | 0.88 | llm | place |  | Singapore | Singapore |
| yes | 0.99 | 0.74 | llm | role |  | Law Minister of India | Law Minister |
| yes | 0.85 | 0.63 | llm | group |  | Lawyers | lawyers |
| yes | 1.00 | 0.75 | dict | group |  | Judges | Judges |
| no | 0.79 | 0.39 | dict | group | institution | Companies | companies |
| no | 0.00 | 0.02 | dict | law | ? | National Exit Test | NEXT |
| yes | 0.79 | 0.76 | dict | institution |  | High Court | High Court |

## Nama Nageswara Rao: Secretary General reported a message from Rajya Sabha regarding passing of the Motor Vehicles (Ammendment) Bill,2019.

2019-08-01, 434 words, state `speech`. Speech id 344220.

**Summary.** Supports the Arbitration and Conciliation (Amendment) Bill, while raising concerns about existing contracts, jurisdiction of district courts, and timeframes for arbitration.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Arbitration | Arbitration Act |
| yes | 0.99 | - | llm | topic |  | Dispute resolution | Dispute is between two parties |
| yes | 0.98 | - | llm | topic |  | Judicial jurisdiction | High Court and the hon. Supreme Court |
| no | 0.01 | - | summary (1, 0.39) | institution | ? | Arbitration Council of India | Body resolving disputes through arbitration. |
| no | 0.00 | - | summary (2, 0.40) | law | ? | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| yes | 0.90 | - | summary (3, 0.40) | law | ? | Arbitration Agreement | Legal contract for settling disputes without court |
| yes | 0.97 | - | summary (4, 0.40) | law | ? | Law Amendment | Change to existing legislation |
| no | 0.00 | - | summary (5, 0.40) | law | ? | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| no | 0.00 | - | summary (6, 0.42) | law | ? | Constitution (One Hundred And Thirtieth Amendment) Bill, 2025 | Proposed amendment to India Constitution number 130 |
| yes | 0.99 | - | summary (7, 0.42) | topic |  | Arbitration | Dispute resolution through neutral mediators. |
| no | 0.00 | - | summary (8, 0.43) | institution | ? | Lok Adalats | Alternative dispute resolution forums |
| no | 0.00 | - | summary (9, 0.43) | law | ? | Citizens Amendment Act (CAA) | Law amending citizenship provisions for religious minorities from neighboring countries. |
| no | 0.00 | - | summary (10, 0.43) | institution | ? | Ficci | Federation of Indian Chambers of Commerce and Industry. A non-governmental trade association and advocacy group in India. |
| no | 0.00 | - | summary (11, 0.43) | law | ? | National Anti-Doping (amendment) Bill 2025 | Legislative amendment to anti-doping regulations |
| no | 0.00 | - | summary (12, 0.43) | law | ? | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| yes | 0.99 | 0.84 | llm | institution |  | Supreme Court of India | Supreme Court |
| yes | 1.00 | 0.79 | llm | institution |  | High Court | High Court |
| no | 0.24 | 0.72 | llm | institution |  | Ministry of Jal Shakti | जल शक्ति |
| no | 1.00 | 0.42 | dict | law |  | Arbitration Act | Arbitration Act |
| no | 0.99 | 0.09 | dict | institution |  | Supreme Court | कोर्ट |

## Ravi Shankar Prasad: Secretary General reported a message from Rajya Sabha regarding passing of the Motor Vehicles (Ammendment) Bill,2019.

2019-08-01, 1458 words, state `speech`. Speech id 344225.

**Summary.** Responds to members' suggestions on the Arbitration and Conciliation (Amendment) Bill, emphasizing the role of the Arbitration Council of India in grading institutions and making India a global arbitration hub.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Arbitration | Arbitration Council of India |
| no | 0.37 | - | llm | topic |  | Ease of Doing Business | Ease of Doing Business |
| yes | 0.93 | - | llm | topic |  | Judiciary | appointment of Chief Justice |
| yes | 0.96 | - | summary (1, 0.32) | institution | ? | Arbitration Council of India | Body resolving disputes through arbitration. |
| no | 0.00 | - | summary (2, 0.41) | institution | ? | Lok Adalats | Alternative dispute resolution forums |
| no | 0.00 | - | summary (3, 0.42) | law | ? | Advocates(Amendment) Bill | Legislation modifying the Advocates Act and regulations. |
| yes | 0.68 | - | summary (4, 0.42) | institution | ? | Parliament | The body that makes India's national laws. |
| yes | 0.94 | - | summary (5, 0.42) | law | ? | Law Amendment | Change to existing legislation |
| yes | 0.97 | - | summary (6, 0.42) | topic |  | Arbitration | Dispute resolution through neutral mediators. |
| no | 0.00 | - | summary (7, 0.42) | institution | ? | Bar Council of India | Regulatory body for lawyers and legal profession. |
| no | 0.28 | - | summary (8, 0.43) | law | ? | Arbitration Agreement | Legal contract for settling disputes without court |
| yes | 0.83 | - | summary (9, 0.43) | institution | ? | Supreme Court | Highest judicial authority in India. |
| no | 0.00 | - | summary (10, 0.43) | institution | ? | National Company Law Appellate Tribunal (NCLAT) | Higher court for corporate and commercial law appeals |
| no | 0.00 | - | summary (11, 0.43) | law | ? | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| no | 0.00 | - | summary (12, 0.43) | institution | ? | Ficci | Federation of Indian Chambers of Commerce and Industry. A non-governmental trade association and advocacy group in India. |
| yes | 1.00 | 0.82 | llm | institution |  | Arbitration Council of India | Arbitration Council of India |
| yes | 0.98 | 0.87 | llm | institution |  | Supreme Court of India | Supreme Court |
| yes | 0.99 | 0.77 | llm | institution |  | High Court | High Court |
| no | 0.39 | 0.62 | llm | person |  | B.N. Srikrishna | Justice Srikrishna |
| no | 0.57 | 0.45 | dict | place | person | Kalyan | Kalyan |
| yes | 0.98 | 0.69 | dict | group |  | Judges | Judges |
| yes | 0.98 | 0.78 | dict | person |  | A. Raja | Shri A. Raja |
| no | 0.30 | 0.66 | dict | group | other | Hindi | Hindi |
| no | 0.76 | 0.59 | dict | group |  | Lawyers | lawyers |
| no | 0.46 | 0.51 | dict | institution |  | Srikrishna Committee | Srikrishna Committee |
| yes | 0.91 | 0.82 | dict | person |  | Supriya Sule | Supriya Sule |
| no | 0.55 | 0.78 | dict | place |  | London | London |

## Kirit Premjibhai Solanki: Regarding laying of new railway line between Chanasma and Radhanpur in Gujarat.

2019-11-27, 159 words, state `speech`. Speech id 342375.

**Summary.** Demands the construction of a new railway line between Chanasma and Radhanpur in north Gujarat to improve connectivity and strategic border movement.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Rail connectivity | रेल कनेक्टिविटी |
| yes | 0.99 | - | llm | topic |  | Railway line construction | नया रेलमार्ग |
| yes | 0.99 | - | summary (1, 0.35) | topic |  | New Railway Line | Construction of new railway routes and tracks. |
| yes | 0.99 | - | summary (2, 0.39) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| no | 0.00 | - | summary (3, 0.39) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| yes | 0.99 | - | summary (4, 0.40) | topic |  | Railway Projects | Development and implementation of railway infrastructure and services. |
| no | 0.00 | - | summary (5, 0.40) | institution | ? | Vande Bharat Express | High-speed rail service connecting Indian cities |
| no | 0.00 | - | summary (6, 0.41) | scheme | ? | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.00 | - | summary (7, 0.41) | topic |  | Bullet Train | High-speed rail service connecting cities. |
| yes | 0.99 | - | summary (8, 0.41) | topic |  | Transport Development | Improvement of transportation infrastructure. |
| no | 0.00 | - | summary (9, 0.41) | scheme | ? | Vande Bharat | Semi high-speed train service run by Indian Railways. |
| no | 0.00 | - | summary (10, 0.41) | institution | ? | Rail Vikas Nigam Limited | Government company constructing railway infrastructure |
| no | 0.05 | - | summary (11, 0.41) | place | ? | Banaskantha | District and Lok Sabha constituency in Gujarat, India. |
| no | 0.01 | - | summary (12, 0.41) | topic |  | Rail Budget | Annual financial allocation for railway services |
| yes | 1.00 | 0.92 | llm | place |  | Gujarat | गुजरात |
| yes | 1.00 | 0.89 | llm | place |  | Chanasma | चाणस् ‍ मा |
| yes | 1.00 | 0.89 | llm | place |  | Radhanpur | राधनपुर |
| yes | 1.00 | 0.86 | llm | place |  | Kutch | कच्छ |
| yes | 0.64 | 0.84 | llm | place |  | Kandla | कांडला |
| yes | 0.98 | 0.94 | llm | place |  | Pakistan | पाकिस्तान |
| yes | 1.00 | 0.87 | dict | place |  | North Gujarat | उत्तर गुजरात |
| no | 1.00 | 0.35 | dict | institution |  | Ministry of Railways | रेल मंत्री |

## Ajay (Teni) Misra: Need to start work on new railway line connecting on Belraya, Palia Kala, Singhai and Nighasan, U.P.

2019-12-11, 118 words, state `speech`. Speech id 340402.

**Summary.** Requests the expeditious completion of the survey and early commencement of the new railway line connecting Belraya, Palia Kala, Singhai, and Nighasan in Uttar Pradesh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Rail connectivity | पलिया, निघासन, बेलरायां और सिंघाई रेल मार्ग |
| no | 0.18 | - | llm | topic |  | Railway gauge conversion | आमान परिवर्तन |
| yes | 0.98 | - | llm | topic |  | Railway survey | सर्वे |
| yes | 0.99 | - | summary (1, 0.36) | topic |  | New Railway Line | Construction of new railway routes and tracks. |
| no | 0.01 | - | summary (2, 0.40) | place | ? | Bareilly | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.99 | - | summary (3, 0.40) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| yes | 0.99 | - | summary (4, 0.41) | topic |  | Railway Projects | Development and implementation of railway infrastructure and services. |
| no | 0.00 | - | summary (5, 0.41) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.00 | - | summary (6, 0.41) | institution | ? | Rail Vikas Nigam Limited | Government company constructing railway infrastructure |
| no | 0.00 | - | summary (7, 0.41) | place | ? | Bulandshahr | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.00 | - | summary (8, 0.41) | place | ? | Raebareli | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Rae Bareli. |
| no | 0.00 | - | summary (9, 0.41) | scheme | ? | Vande Bharat | Semi high-speed train service run by Indian Railways. |
| no | 0.00 | - | summary (10, 0.41) | place | ? | Unnao | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.00 | - | summary (11, 0.41) | place | ? | Lucknow | District and Lok Sabha constituency in Uttar Pradesh, India. |
| no | 0.48 | - | summary (12, 0.42) | place | ? | Uttar Pradesh | Northern Indian state. |
| yes | 0.98 | 0.90 | llm | place |  | Lakhimpur Kheri | लखीमपुर खीरी |
| yes | 0.64 | 0.81 | llm | place |  | Uttar Pradesh | यू० पी० *(not in text)* |
| yes | 0.99 | 0.87 | llm | institution |  | Forest Department | वन विभाग |
| yes | 0.99 | 0.68 | dict | place |  | Mailani | मैलानी |
| yes | 0.95 | 0.87 | dict | place |  | Bahraich | बहराइच |
| yes | 1.00 | 0.90 | dict | institution |  | Ministry of Railways | रेल मंत्रालय |

## Shyam Singh Yadav: Request to government to give compensation to farmers whoes crops are damaged by wild animals.

2019-12-11, 158 words, state `speech`. Speech id 340545.

**Summary.** Requests the government to provide adequate compensation to farmers whose crops are destroyed by stray animals.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Crop damage by stray animals | छुट्टा पशुओं |
| yes | 0.99 | - | llm | topic |  | Agricultural compensation | वाजिब मुआवजा |
| yes | 0.99 | - | summary (1, 0.32) | topic |  | agriculture compensation | Payment to farmers for crop loss or land acquisition |
| no | 0.00 | - | summary (2, 0.32) | scheme | ? | Pradhan Mantri Fasal Bima Yojana | Government crop insurance scheme that pays farmers for crop loss. |
| no | 0.00 | - | summary (3, 0.35) | scheme | ? | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| no | 0.07 | - | summary (4, 0.36) | topic |  | Cow Protection | Policies protecting cattle and preventing cattle slaughter |
| yes | 1.00 | - | summary (5, 0.36) | topic |  | Crop Damages | Loss or destruction of agricultural crops due to various causes. |
| no | 0.00 | - | summary (6, 0.36) | scheme | ? | National Agricultural Insurance Scheme | Government insurance scheme that protects farmers from crop loss. |
| no | 0.00 | - | summary (7, 0.37) | scheme | ? | National Crop Insurance Programme (NCIP) | Government insurance scheme that pays farmers when crops fail. |
| yes | 0.99 | - | summary (8, 0.37) | topic |  | Farmers' Welfare | Government support and welfare programs for farmers. |
| no | 0.00 | - | summary (9, 0.37) | law | ? | Minimum Support Prices | Price floor for agricultural commodities |
| yes | 0.99 | - | summary (10, 0.37) | topic |  | Farmers' Grievances | Complaints from agricultural workers |
| no | 0.08 | - | summary (11, 0.37) | topic |  | Insurance Claim | Request for insurance payment |
| no | 0.06 | - | summary (12, 0.37) | topic |  | Crop Insurance | General insurance that pays farmers when their crops are damaged or fail. |
| yes | 1.00 | 0.84 | llm | place |  | Jaunpur | जौनपुर |
| yes | 1.00 | 0.93 | llm | group |  | Farmers | किसान |
| yes | 0.78 | 0.92 | dict | group |  | Government employees | सरकारी कर्मचारी |

