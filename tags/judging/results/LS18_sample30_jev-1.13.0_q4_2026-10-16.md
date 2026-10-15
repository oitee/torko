# Relevance check review: sample

Model `jev-1.13.0`, questions `q4`, written on 2026-10-16. 30 speeches. For a topic, `P(keep)` is P(central or supporting), kept at 0.6. For a named item, `P(keep)` is P(part of the member's point), kept at 0.6 together with `P(refers)` at 0.6. `Model type` shows the model's type only when it differs from the extraction type. `Source`: `llm` = the extraction, `dict` = the entity dictionary found the words in the text, `recognised` = a recognised tag, near the summary in meaning (its rank and distance in brackets). Write keep or drop in the `review` column of `sample_jev-1.13.0_q4_2026-10-16_2.tsv`. 0 items carry an earlier manual mark already.

## Manickam Tagore B: Establishment of a medical college and multi-speciality Hospital in Sivakasi-laid

2024-07-25, 203 words, state `speech`. Speech id 299342.

**Summary.** Urges the establishment of a medical college and multi-speciality hospital in Sivakasi to improve healthcare access.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Healthcare infrastructure | medical college and multi-speciality Hospital *(not in text)* |
| no | 0.00 | - | recognised (1, 0.40) | place | ? | Sivaganga | District and Lok Sabha constituency in Tamil Nadu, India. |
| no | 0.00 | - | recognised (2, 0.40) | place | ? | Madurai | District and Lok Sabha constituency in Tamil Nadu, India. |
| no | 0.00 | - | recognised (3, 0.42) | place | ? | Tenkasi | District and Lok Sabha constituency in Tamil Nadu, India. |
| yes | 0.99 | - | recognised (4, 0.42) | topic |  | Social Infrastructure | Public facilities for health, education and community services. |
| no | 0.00 | - | recognised (5, 0.42) | place | ? | Thoothukudi | District and Lok Sabha constituency in Tamil Nadu, India. The constituency is listed as Thoothukkudi. |
| no | 0.00 | - | recognised (6, 0.42) | place | ? | Tiruppur | District and Lok Sabha constituency in Tamil Nadu, India. |
| yes | 0.99 | - | recognised (7, 0.42) | institution | ? | Medical Colleges | Higher education institutions for medical training. |
| no | 0.00 | - | recognised (8, 0.42) | place | ? | Tirunelveli | District and Lok Sabha constituency in Tamil Nadu, India. |
| no | 0.44 | - | recognised (9, 0.42) | institution | ? | Government Hospitals | Public medical facilities providing healthcare |
| no | 0.00 | - | recognised (10, 0.42) | law | ? | National Medical Commission Bill | Legislation regulating medical doctors and practice. |
| yes | 0.99 | - | recognised (11, 0.42) | institution | ? | Hospitals | Medical facilities for treatment of patients. |
| no | 0.00 | - | recognised (12, 0.42) | place | ? | Coimbatore | District and Lok Sabha constituency in Tamil Nadu, India. |
| yes | 1.00 | 0.84 | llm | place |  | Sivakasi | Sivakasi |
| yes | 1.00 | 0.79 | llm | place |  | Virudhunagar | Virudhunagar |

## Praveen Patel: General discussion on the Budget 2024-2025; General discussion on the Budget of Union Territory of Jammu and Kashmir for 2024-2025 and Demands for Grants in respect of Union Territory of Jammu and Kashmir for 2024-2025

2024-07-30, 2231 words, state `speech`. Speech id 298340.

**Summary.** Supports the Union Budget 2024-2025 as a comprehensive roadmap for achieving Viksit Bharat 2047 through inclusive growth, youth employment, and infrastructural development.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Economic development and budget | केंद्रीय बजट |
| yes | 0.99 | - | llm | topic |  | Youth employment and skill development | कौशल विकास |
| yes | 0.98 | - | llm | topic |  | Infrastructure development | बुनियादी ढांचे |
| yes | 0.98 | - | llm | topic |  | Micro, Small and Medium Enterprises | एम.एस.एम.ई |
| yes | 0.86 | - | llm | topic |  | Agricultural and rural development | कृषि में उत्पादकता |
| no | 0.47 | - | recognised (1, 0.37) | topic |  | Sabka Sath Sabka Vikas | Government slogan for growth that includes and benefits everyone. |
| no | 0.01 | - | recognised (2, 0.38) | scheme | ? | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| yes | 0.98 | - | recognised (3, 0.38) | topic |  | Budget | India's yearly financial plan, showing the government's planned income and spending. |
| no | 0.00 | - | recognised (4, 0.38) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.90 | - | recognised (5, 0.38) | law | ? | Development Policy | Government strategy for economic growth. |
| yes | 0.98 | - | recognised (6, 0.40) | law | ? | General Budget | Annual government financial plan detailing revenue and expenditure allocations. |
| no | 0.13 | - | recognised (7, 0.40) | scheme | ? | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.15 | - | recognised (8, 0.40) | scheme | ? | Atmanirbhar Bharat | Government program that promotes self-reliance and domestic production. |
| no | 0.00 | - | recognised (9, 0.41) | institution | ? | Swadeshi Jagran Manch | Organization promoting indigenous Indian economic and social development. |
| no | 0.02 | - | recognised (10, 0.41) | scheme | ? | Start Up India | Government initiative that supports new businesses and entrepreneurs. |
| yes | 0.60 | - | recognised (11, 0.41) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.07 | - | recognised (12, 0.41) | scheme | ? | Vocal for Local | Promoting Indian-made goods and local businesses |
| yes | 0.83 | 0.83 | llm | scheme |  | Pradhan Mantri Awas Yojana | पीएम आवास योजना |
| yes | 0.79 | 0.62 | llm | scheme |  | Pradhan Mantri Gram Sadak Yojana | पी.एम. जी.एस.वाई. |
| yes | 0.70 | 0.79 | llm | law |  | Andhra Pradesh Reorganisation Act | आंध्र प्रदेश पुनर्गठन अधिनियम |
| no | 0.47 | 0.87 | llm | institution |  | Nalanda University | नालंदा विश्वविद्यालय |
| yes | 0.94 | 0.89 | dict | person |  | Narendra Modi | मोदी |
| yes | 0.99 | 0.88 | dict | group |  | Youth | युवाओं |
| yes | 0.99 | 0.87 | dict | group |  | Middle class | मध्यम वर्ग |
| no | 0.04 | 0.05 | dict | scheme |  | Atal Mission for Rejuvenation and Urban Transformation | अमृत |
| yes | 0.87 | 0.74 | dict | group |  | Scheduled Tribes | आदिवासी |
| yes | 0.76 | 0.85 | dict | group |  | Poor | गरीब |
| no | 0.52 | 0.85 | dict | place |  | Andhra Pradesh | आंध्र प्रदेश |
| yes | 0.73 | 0.90 | dict | group |  | Women | महिलाओं |

## S Jothimani: Union Budget (2024-2025)- Demands For Grants-Ministry of Railways-Contd

2024-07-31, 869 words, state `speech`. Speech id 297980.

**Summary.** Criticises the government over railway safety, recurring train accidents, overcrowding in general compartments, withdrawal of senior citizen concessions, and unaddressed connectivity demands in Karur.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Railway safety | rail safety |
| yes | 0.99 | - | llm | topic |  | Train accidents | Rail accidents |
| yes | 0.97 | - | llm | topic |  | Train overcrowding | Overcrowding in railways |
| yes | 0.88 | - | llm | topic |  | Railway fare concessions | railway concession |
| yes | 0.93 | - | llm | topic |  | Rail connectivity | stoppages to facilitate smooth travel |
| yes | 0.99 | - | recognised (1, 0.41) | topic |  | Railway Accidents | Collisions and crashes involving trains. |
| yes | 0.99 | - | recognised (2, 0.41) | topic |  | Railway Safety | Measures to ensure safe railway operations. |
| no | 0.58 | - | recognised (3, 0.41) | place | ? | Karur | District and Lok Sabha constituency in Tamil Nadu, India. |
| no | 0.00 | - | recognised (4, 0.42) | scheme | ? | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| yes | 0.98 | - | recognised (5, 0.42) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| no | 0.00 | - | recognised (6, 0.42) | institution | ? | Railway Reforms Committee | Committee examining railway modernization |
| yes | 0.98 | - | recognised (7, 0.42) | institution | ? | Indian Railways | Government rail organization. |
| no | 0.00 | - | recognised (8, 0.43) | topic |  | Tatkal Quota | Unreserved seats available for last-minute train bookings |
| no | 0.00 | - | recognised (9, 0.43) | topic |  | Railway Compensation | General government payments made for injury or loss in railway incidents. |
| no | 0.00 | - | recognised (10, 0.43) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.00 | - | recognised (11, 0.43) | institution | ? | Railway Convention Committee | Body setting terms between government and railways. |
| no | 0.00 | - | recognised (12, 0.43) | topic |  | Ticketless Travelling | Travel without valid ticket or permit on trains. |
| yes | 1.00 | 0.92 | llm | institution |  | Indian Railways | Indian Railways |
| yes | 0.99 | 0.75 | llm | scheme |  | Kavach | Kavach |
| yes | 1.00 | 0.83 | llm | group |  | Senior citizens | senior citizens |
| yes | 0.96 | 0.90 | llm | scheme |  | Rashtriya Rail Sanraksha Kosh | Rashtriya Rail Sanraksha Kosh |
| yes | 0.92 | 0.78 | llm | scheme | other | Vande Bharat Express | Vande Bharat trains |
| yes | 0.99 | 0.75 | llm | place |  | Karur | Karur district |
| yes | 0.99 | 0.60 | llm | institution |  | Integral Coach Factory | ICF |
| yes | 0.96 | 0.60 | llm | institution |  | Southern Railway | Southern Railways |
| yes | 0.99 | 0.78 | dict | law | other | Union Budget | Budget |
| no | 1.00 | 0.37 | dict | institution |  | Ministry of Railways | Minister of Railways |
| yes | 0.98 | 0.93 | dict | scheme | other | COVID-19 pandemic | COVID-19 pandemic |
| yes | 0.97 | 0.68 | dict | law | other | Railway Budget | Railway Budget |
| yes | 0.97 | 0.84 | dict | place |  | Bengaluru | Bengaluru |
| no | 0.81 | 0.44 | dict | group |  | Traders | traders |
| yes | 0.72 | 0.79 | dict | place |  | Howrah | Howrah |
| no | 0.80 | 0.59 | dict | group |  | Students | students |

## V K Sreekandan: Union Budget (2024-2025)- Demands For Grants-Ministry of Railways-Contd

2024-07-31, 143 words, state `speech`. Speech id 297986.

**Summary.** Expresses disappointment over the neglect of Kerala in railway budget allocations and lack of major projects.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Rail connectivity | Railways |
| yes | 0.99 | - | recognised (1, 0.38) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.99 | - | recognised (2, 0.38) | topic |  | Rail Budget | Annual financial allocation for railway services |
| yes | 0.98 | - | recognised (3, 0.41) | topic |  | Railway Projects | Development and implementation of railway infrastructure and services. |
| yes | 0.99 | - | recognised (4, 0.41) | institution | ? | Indian Railways | Government rail organization. |
| no | 0.13 | - | recognised (5, 0.42) | topic |  | New Railway Line | Construction of new railway routes and tracks. |
| no | 0.00 | - | recognised (6, 0.42) | topic |  | Tatkal Quota | Unreserved seats available for last-minute train bookings |
| no | 0.00 | - | recognised (7, 0.43) | law | ? | Railway Freight Exemptions | Relief from transport taxes for certain rail cargo. |
| yes | 0.99 | - | recognised (8, 0.43) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| no | 0.00 | - | recognised (9, 0.43) | scheme | ? | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| no | 0.00 | - | recognised (10, 0.43) | institution | ? | Integral Coach Factory | State manufacturer of railway coaches |
| yes | 1.00 | - | recognised (11, 0.43) | place | ? | Kerala | State in southwestern India |
| no | 0.00 | - | recognised (12, 0.43) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| yes | 1.00 | 0.66 | llm | institution |  | Ministry of Railways | Railways |
| yes | 1.00 | 0.92 | llm | place |  | Kerala | Kerala |
| yes | 0.83 | 0.86 | llm | place |  | Palakkad | Palakkad |

## Shreyas M Patel: General Budget (2024-2025) - Demands for Grants - Ministry of Education

2024-08-01, 502 words, state `speech`. Speech id 297874.

**Summary.** Asks for increased budget allocation for education, enhanced research and development, and improved school infrastructure in Hassan.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Educational funding and expenditure | Government expenditure on education as a percentage of GDP remains alarmingly low |
| yes | 0.95 | - | llm | topic |  | School infrastructure development | mid - day meal preparation rooms have been damaged |
| yes | 0.97 | - | recognised (1, 0.35) | place | ? | Hassan | District and Lok Sabha constituency in Karnataka, India. |
| yes | 0.81 | - | recognised (2, 0.39) | topic |  | Educational Reforms | Changes to improve education system. |
| no | 0.00 | - | recognised (3, 0.39) | scheme | ? | Sarva Shiksha Abhiyan | Government program that aims to give every child access to school education. |
| yes | 0.99 | - | recognised (4, 0.39) | topic |  | Educational Budget | The amount of government money set aside for education. |
| yes | 0.99 | - | recognised (5, 0.39) | topic |  | Educational Projects | Initiatives for improving educational infrastructure. |
| no | 0.00 | - | recognised (6, 0.39) | topic |  | Health Budget | Financial allocation for healthcare |
| yes | 0.99 | - | recognised (7, 0.40) | topic |  | Social Infrastructure | Public facilities for health, education and community services. |
| yes | 0.98 | - | recognised (8, 0.40) | topic |  | Education | Provision of schooling and learning opportunities for students. |
| no | 0.01 | - | recognised (9, 0.40) | topic |  | Coaching Facilities | Infrastructure for training programs |
| yes | 0.99 | - | recognised (10, 0.40) | topic |  | Educational Development | Improvement in learning systems |
| no | 0.10 | - | recognised (11, 0.40) | law | ? | Right to Education | Constitutional right to education. |
| no | 0.00 | - | recognised (12, 0.40) | topic |  | Teachers' Grievances | Complaints and concerns raised by educators about working conditions. |
| yes | 1.00 | 0.89 | llm | institution |  | Ministry of Education | Education Ministry |
| yes | 0.98 | 0.94 | llm | law | other | National Education Policy 2020 | National Education Policy 2020 |
| no | 0.07 | 0.88 | llm | law |  | Right of Children to Free and Compulsory Education Act | Right of Children to Free and Compulsory Education Act *(not in text)* |
| yes | 1.00 | 0.89 | llm | institution |  | Indian Institute of Technology | Indian Institute of Technology ( IIT ) |
| yes | 1.00 | 0.72 | llm | place |  | Hassan | Hassan Constituency |
| no | 1.00 | 0.58 | llm | scheme |  | Pradhan Mantri Schools for Rising India | PM SHRI Scheme |
| yes | 1.00 | 0.70 | llm | institution |  | Jawahar Navodaya Vidyalaya | Jawahar Navodaya Vidyalaya school |
| no | 1.00 | 0.56 | dict | scheme |  | PM SHRI | PM SHRI |
| yes | 0.99 | 0.81 | dict | law | other | Union Budget | Budget |
| no | 0.44 | 0.90 | dict | person |  | B. R. Ambedkar | Dr. B.R. Ambedkar |
| no | 0.16 | 0.89 | dict | institution |  | Infosys | Infosys |
| yes | 0.97 | 0.76 | dict | law | other | Economic Survey | Economic Survey |
| yes | 0.90 | 0.91 | dict | place |  | Karnataka | Karnataka |
| no | 0.55 | 0.50 | dict | group |  | Children | children |
| yes | 0.98 | 0.80 | dict | scheme |  | Mid-Day Meal Scheme | Mid-day Meal |

## Laxmikant Pappu Nishad: Discussion on the Demands for Grants No. 46 and 47 under the control of the Ministry of Health and Family Welfare-not concluded

2024-08-02, 297 words, state `speech`. Speech id 297062.

**Summary.** Criticizes inadequate health services and medicine availability in Sant Kabir Nagar and requests the establishment of a medical college, nursing college, and trauma center.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Healthcare infrastructure | स्वास्थ्य बजट |
| yes | 0.99 | - | recognised (1, 0.37) | place | ? | Sant Kabir Nagar | District and Lok Sabha constituency in Uttar Pradesh, India. |
| yes | 0.98 | - | recognised (2, 0.40) | institution | ? | Health Centres | Facilities providing medical services |
| yes | 0.99 | - | recognised (3, 0.41) | topic |  | Social Infrastructure | Public facilities for health, education and community services. |
| no | 0.02 | - | recognised (4, 0.41) | place | ? | Kushinagar | District and Lok Sabha constituency in Uttar Pradesh, India. The constituency is listed as Kushi Nagar. |
| no | 0.58 | - | recognised (5, 0.42) | institution | ? | Dispensaries | Facilities providing basic medical services. |
| yes | 0.99 | - | recognised (6, 0.42) | topic |  | Social Sector | Government services for health, education, and welfare. |
| yes | 0.99 | - | recognised (7, 0.42) | topic |  | Health Sector | The overall system of institutions that deliver health care. |
| yes | 0.74 | - | recognised (8, 0.42) | institution | ? | Community Health Centres | Basic healthcare facilities in communities |
| yes | 0.99 | - | recognised (9, 0.42) | topic |  | Health Care | Medical services provided to keep people healthy. |
| yes | 0.82 | - | recognised (10, 0.42) | institution | ? | Primary Health Centres | Basic healthcare facilities |
| no | 0.09 | - | recognised (11, 0.43) | institution | ? | Medical Store Depot | Facility storing and distributing medicines and medical supplies. |
| yes | 0.99 | - | recognised (12, 0.43) | topic |  | Medical Facilities | Hospitals, clinics, and other places that provide medical care. |
| yes | 1.00 | 0.90 | llm | place |  | Sant Kabir Nagar | संतकबीर नगर |
| yes | 0.90 | 0.76 | llm | scheme |  | Ayushman Bharat | आयुष्मान कार्ड |
| yes | 0.99 | 0.80 | dict | person |  | Kabir | संत कबीर |
| yes | 1.00 | 0.89 | dict | group |  | Poor | गरीब |
| yes | 0.99 | 0.78 | dict | institution | ? | Primary Health Centre | पीएचसी |
| yes | 0.89 | 0.78 | dict | group | ? | Nurses | नर्सेज |
| yes | 0.73 | 0.91 | dict | group | institution | Samajwadi Party | समाजवादी पार्टी |
| yes | 0.96 | 0.88 | dict | group |  | Doctors | डॉक्टरों |
| yes | 0.66 | 0.86 | dict | person |  | Akhilesh Yadav | अखिलेश जी |
| no | 0.40 | 0.94 | dict | group |  | Women | महिलाओं |

## Shahu Shahaji Chhatrapati: Regarding the woes of the Employees` Pension Scheme

2024-08-06, 309 words, state `speech`. Speech id 296097.

**Summary.** Criticises the government over the low minimum pension and lack of inflation protection for pensioners under the Employees' Pension Scheme.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Pensions and elderly welfare | Employees? Pension Scheme, 1995 ( EPS - 95 ) |
| yes | 0.99 | - | recognised (1, 0.32) | scheme | ? | Employees Pension Scheme | Government retirement pension scheme for workers, run with the provident fund. |
| yes | 0.99 | - | recognised (2, 0.38) | topic |  | EPS 95 Pensioner | Retired workers with pensions. |
| no | 0.00 | - | recognised (3, 0.38) | scheme | ? | National Pension System | Government retirement savings scheme where contributions build a pension. |
| no | 0.40 | - | recognised (4, 0.39) | scheme | ? | Employees Provident Fund | Government retirement savings scheme where workers and employers both pay in. |
| no | 0.00 | - | recognised (5, 0.39) | scheme | ? | UNIFIED PENSION SCHEME(UPS) | Government pension scheme that unifies retirement benefits for public sector staff. |
| yes | 0.90 | - | recognised (6, 0.39) | topic |  | Pension Reforms | Changes to retirement benefit systems. |
| yes | 0.99 | - | recognised (7, 0.39) | topic |  | Pension Schemes | General government programs that pay regular income to retired people. |
| no | 0.00 | - | recognised (8, 0.39) | scheme | ? | Atal Pension Yojana | Government pension scheme for workers in the unorganised sector. |
| no | 0.33 | - | recognised (9, 0.40) | institution | ? | Employees Provident Fund Organisation | The government body that manages retirement savings for Indian workers. |
| yes | 0.85 | - | recognised (10, 0.40) | law | ? | Pension Rules | Regulations governing retirement income payments. |
| yes | 0.99 | - | recognised (11, 0.41) | topic |  | Retirement Pensions | Regular payments to retired workers. |
| yes | 0.96 | - | recognised (12, 0.41) | topic |  | Pension Funds | Investment and management of retirement income schemes. |
| yes | 1.00 | 0.90 | llm | law | scheme | Employees' Pension Scheme, 1995 | Employees? Pension Scheme, 1995 ( EPS - 95 ) |
| yes | 0.99 | 0.88 | llm | law |  | Article 41 of the Constitution | Article 41 of the Constitution |
| no | 0.98 | 0.53 | dict | group |  | Employees | employees |
| yes | 1.00 | 0.93 | dict | law |  | Constitution of India | Constitution |
| yes | 1.00 | 0.91 | dict | law |  | Directive Principles of State Policy | Directive Principles of State Policy |
| yes | 0.93 | 0.79 | dict | place |  | Jantar Mantar | Jantar Mantar |

## Anup Sanjay Dhotre: Regarding need of Vande Bharat train between Nagpur and Mumbai

2024-08-08, 257 words, state `speech`. Speech id 295888.

**Summary.** Requests the introduction of a Vande Bharat train between Nagpur and Mumbai and thanks the Prime Minister for station development funds under Amrit Bharat scheme.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Rail connectivity | वंदे भारत रेलवे सेवा |
| no | 0.38 | - | llm | topic |  | Station development | अमृत भारत योजना *(not in text)* |
| yes | 1.00 | - | recognised (1, 0.37) | scheme | ? | Vande Bharat | Semi high-speed train service run by Indian Railways. |
| yes | 1.00 | - | recognised (2, 0.37) | institution | ? | Vande Bharat Express | High-speed rail service connecting Indian cities |
| no | 0.17 | - | recognised (3, 0.37) | scheme | ? | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| yes | 0.99 | - | recognised (4, 0.40) | place | ? | Nagpur | District and Lok Sabha constituency in Maharashtra, India. |
| no | 0.15 | - | recognised (5, 0.42) | scheme | ? | Atal Mission for Rejuvenation and Urban Transformation (AMRUT) | Government program that improves basic infrastructure in cities. |
| no | 0.00 | - | recognised (6, 0.42) | place | ? | Amravati | District and Lok Sabha constituency in Maharashtra, India. |
| no | 0.00 | - | recognised (7, 0.42) | scheme | ? | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.00 | - | recognised (8, 0.42) | place | ? | Wardha | District and Lok Sabha constituency in Maharashtra, India. |
| no | 0.00 | - | recognised (9, 0.43) | scheme | ? | Vande Bharat Mission | Government program that brought Indian citizens home from abroad. |
| no | 0.00 | - | recognised (10, 0.43) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.00 | - | recognised (11, 0.43) | topic |  | Rajdhani Express | Premium long-distance passenger train service. |
| no | 0.00 | - | recognised (12, 0.44) | place | ? | Nanded | District and Lok Sabha constituency in Maharashtra, India. |
| no | 0.06 | 0.84 | llm | scheme |  | Amrit Bharat Scheme | अमृत भारत योजना *(not in text)* |
| yes | 1.00 | 0.93 | llm | scheme | other | Vande Bharat Train | वंदे भारत |
| yes | 1.00 | 0.91 | llm | place |  | Nagpur | नागपुर |
| yes | 1.00 | 0.94 | llm | place |  | Mumbai | मुंबई |
| no | 0.50 | 0.87 | llm | place |  | Akola | अकोला |
| yes | 0.92 | 0.90 | dict | place |  | Nashik | नासिक |
| no | 0.03 | 0.91 | dict | person |  | Narendra Modi | मोदी जी |
| yes | 0.66 | 0.87 | dict | place |  | Bhusawal | भुसावल |
| yes | 1.00 | 0.80 | dict | group |  | Railway passengers | यात्री |
| no | 0.28 | 0.46 | dict | scheme |  | Atal Mission for Rejuvenation and Urban Transformation | अमृत |
| yes | 1.00 | 0.93 | dict | place |  | Maharashtra | महाराष्ट्र |
| yes | 0.83 | 0.92 | dict | group |  | Students | विद्यार्थी |
| yes | 1.00 | 0.89 | dict | scheme | other | Vande Bharat Express | वंदे भारत ट्रेन |

## Chandra Prakash Joshi: Motion for Election to Committee on Public Undertakings

2025-02-03, 65 words, state `speech`. Speech id 291530.

**Summary.** Moves that the House elect fifteen members to the Committee on Public Undertakings for 2025-26.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| no | 0.03 | - | recognised (1, 0.39) | law | ? | Rule 56 | Parliamentary procedure rule |
| no | 0.00 | - | recognised (2, 0.39) | institution | ? | Business Advisory Committee | The Lok Sabha committee that plans the order of parliamentary business. |
| yes | 0.90 | - | recognised (3, 0.40) | topic |  | Members | Participants or representatives in a group. Meaning here is unclear. |
| no | 0.01 | - | recognised (4, 0.40) | topic |  | Select Committee | A committee formed to study one bill in detail. |
| no | 0.00 | - | recognised (5, 0.40) | topic |  | Joint Parliamentary Committee (JPC) | A committee formed from both houses of parliament to study one issue. |
| no | 0.00 | - | recognised (6, 0.40) | topic |  | Recommendation | Advice given by a parliamentary committee. |
| no | 0.00 | - | recognised (7, 0.41) | institution | ? | Committee on Papers Laid on the Table of the House | The Lok Sabha committee that checks documents placed before the house. |
| no | 0.00 | - | recognised (8, 0.41) | institution | ? | George Fernandes Committee | Committee formed by government leader |
| yes | 0.97 | - | recognised (9, 0.41) | topic |  | Parliamentary Committees | A group of parliament members that studies a specific issue in depth. |
| no | 0.00 | - | recognised (10, 0.41) | topic |  | Observation | A formal note made by parliament on a matter. |
| no | 0.01 | - | recognised (11, 0.41) | topic |  | Rule 184 | A specific rule that allows a parliamentary discussion with a vote. |
| yes | 0.70 | - | recognised (12, 0.41) | topic |  | MP(s) | An elected member of parliament. |
| yes | 1.00 | 0.87 | dict | institution |  | Committee on Public Undertakings | सरकारी उपक्रमों संबंधी समिति |

## C N Annadurai: The Union Budget,2025-2026(concluded)

2025-02-11, 752 words, state `speech`. Speech id 290457.

**Summary.** Criticises the Union Budget 2025-2026 for ignoring Tamil Nadu's demands, failing to address unemployment, poverty, and inflation, and keeping allocations for key welfare schemes stagnant.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.97 | - | llm | topic |  | Federal budget | Union Budget 2025-26 |
| yes | 0.99 | - | llm | topic |  | Regional development | needs of Tamil Nadu |
| yes | 0.96 | - | llm | topic |  | Agricultural welfare | farmer's income |
| yes | 0.88 | - | llm | topic |  | Employment | unemployment |
| yes | 0.74 | - | recognised (1, 0.40) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.99 | - | recognised (2, 0.41) | topic |  | Budget | India's yearly financial plan, showing the government's planned income and spending. |
| yes | 0.97 | - | recognised (3, 0.42) | law | ? | General Budget | Annual government financial plan detailing revenue and expenditure allocations. |
| no | 0.06 | - | recognised (4, 0.42) | topic |  | Health Budget | Financial allocation for healthcare |
| yes | 0.93 | - | recognised (5, 0.43) | topic |  | Poverty | State of living with insufficient income. |
| yes | 0.99 | - | recognised (6, 0.43) | topic |  | Regional Disparity | Economic inequalities between different regions of India |
| no | 0.00 | - | recognised (7, 0.43) | law | ? | Constitution (One Hundred And Thirtieth Amendment) Bill, 2025 | Proposed amendment to India Constitution number 130 |
| yes | 0.97 | - | recognised (8, 0.44) | topic |  | Underdevelopment | State of regions or countries lacking economic and infrastructure development. |
| yes | 0.92 | - | recognised (9, 0.44) | topic |  | Annual Plans | Yearly government budgets and goals. |
| yes | 0.95 | - | recognised (10, 0.44) | topic |  | Poor | People living in poverty with insufficient income and resources. |
| no | 0.13 | - | recognised (11, 0.44) | law | ? | Central and Sales Tax | Taxation system and revenue collection laws. |
| yes | 0.75 | - | recognised (12, 0.44) | topic |  | Rail Budget | Annual financial allocation for railway services |
| yes | 1.00 | 0.93 | llm | place |  | Tamil Nadu | Tamil Nadu |
| yes | 0.88 | 0.81 | llm | scheme |  | Pradhan Mantri Kisan Samman Nidhi | PM-KISAN |
| yes | 0.99 | 0.75 | llm | law | scheme | Mahatma Gandhi National Rural Employment Guarantee Act | MGNREGA |
| yes | 0.68 | 0.84 | llm | scheme |  | National Health Mission | National Health Mission |
| no | 0.48 | 0.63 | llm | scheme |  | Pradhan Mantri Gram Sadak Yojana | PMGSY |
| yes | 1.00 | 0.91 | dict | law | other | Union Budget | Budget |
| no | 0.99 | 0.46 | dict | group |  | Poor | poor |
| no | 0.14 | 0.89 | dict | person |  | M. K. Stalin | M.K. Stalin |
| yes | 0.97 | 0.66 | dict | group |  | Farmers | farmer |
| no | 0.93 | 0.58 | dict | group |  | Youth | youth |
| yes | 0.96 | 0.89 | dict | scheme | other | Cyclone Michaung | Cyclone Michaung |
| yes | 0.95 | 0.81 | dict | scheme |  | Viksit Bharat | Viksit Bharat |
| no | 0.43 | 0.59 | dict | law | other | Economic Survey | Economic Survey |

## S Supongmeren Jamir: Regarding issues pertaining to Myanmar border areas

2025-03-12, 180 words, state `speech`. Speech id 204345.

**Summary.** Asks the government to increase allowances for village guards on the Indo-Myanmar border and opposes the construction of the international boundary fence under the Act East Policy.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Border security | guard against invaders and intruders |
| yes | 1.00 | - | llm | topic |  | Village guards welfare | village guards |
| no | 0.00 | - | recognised (1, 0.37) | institution | ? | Border Security Force (BSF) | Paramilitary force that guards India's international land borders. |
| no | 0.00 | - | recognised (2, 0.38) | scheme | ? | Vibrant Village Programme | Government program that develops villages near the international border. |
| no | 0.00 | - | recognised (3, 0.40) | institution | ? | Assam Rifles | Paramilitary force operating in northeastern India. |
| yes | 0.90 | - | recognised (4, 0.40) | topic |  | Border Fencing | Barriers along national boundaries |
| yes | 0.83 | - | recognised (5, 0.40) | topic |  | Indo-Myanmar Relations | Relations between India and Myanmar. |
| no | 0.00 | - | recognised (6, 0.40) | institution | ? | North-Eastern Council (NEC) | Regional body for development in North Eastern states. |
| yes | 0.99 | - | recognised (7, 0.41) | place | ? | International Boundries | National borders separating India from neighbours |
| no | 0.00 | - | recognised (8, 0.41) | institution | ? | ITBP | Paramilitary border security force |
| no | 0.19 | - | recognised (9, 0.41) | place | ? | Mizoram | Northeastern state bordering Myanmar |
| no | 0.00 | - | recognised (10, 0.41) | place | ? | Line of Actual Control | De facto border between India and China |
| no | 0.00 | - | recognised (11, 0.41) | institution | ? | NSCN(IM) | Armed group operating in northeast India |
| no | 0.00 | - | recognised (12, 0.42) | institution | ? | National Security Guards (NSGs) | Elite force that protects VIPs and responds to major security threats. |
| yes | 0.99 | 0.68 | llm | scheme |  | Act East Policy | Act East Policy |
| yes | 0.94 | 0.72 | llm | place |  | Myanmar | Myanmar |
| no | 0.54 | 0.39 | llm | place |  | Mon | Mon |
| no | 0.50 | 0.72 | llm | place |  | Tuensang | Tuensang |
| no | 0.58 | 0.72 | llm | place |  | Kiphire | Kiphire |
| no | 0.56 | 0.52 | llm | place |  | Meluri | Meluri |
| no | 0.45 | 0.73 | llm | place |  | Noklak | Noklak |
| no | 0.51 | 0.71 | llm | place |  | Longleng | Longleng |
| no | 0.54 | 0.63 | dict | institution |  | External Affairs Ministry | External Affairs Ministry |

## Manish Jaiswal: Regarding irrigation facility in Hazaribagh Parliamentary Constituency

2025-03-17, 166 words, state `speech`. Speech id 204281.

**Summary.** Demands the completion of the long-pending Konar Dam canal irrigation project and the rehabilitation of displaced villagers in Hazaribagh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Irrigation | सिंचाई परियोजना |
| yes | 0.90 | - | llm | topic |  | Dam displacement | विस्थापित |
| yes | 0.83 | - | recognised (1, 0.37) | topic |  | Rehabilitation | Support programs to help people recover from disasters or other hardships. |
| no | 0.58 | - | recognised (2, 0.38) | place | ? | Hazaribag | District and Lok Sabha constituency in Jharkhand, India. The constituency is listed as Hazaribagh. |
| no | 0.03 | - | recognised (3, 0.39) | scheme | ? | Kosi Project | Named dam and irrigation project on the Kosi river. |
| no | 0.02 | - | recognised (4, 0.39) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.00 | - | recognised (5, 0.40) | place | ? | Polavaram Dam | Major dam project providing water for irrigation. |
| no | 0.11 | - | recognised (6, 0.40) | place | ? | Damodar River | River in eastern India used for irrigation and power |
| yes | 0.92 | - | recognised (7, 0.40) | scheme | ? | Multipurpose Irrigation Project | Named dam or canal project used for irrigation and other purposes together. |
| no | 0.00 | - | recognised (8, 0.40) | scheme | ? | Narmada Irrigation Project | Named dam and irrigation project on the Narmada river. |
| no | 0.00 | - | recognised (9, 0.40) | scheme | ? | Polavaram Irrigation Project | Named dam and irrigation project for water management. |
| no | 0.02 | - | recognised (10, 0.41) | place | ? | Palamu | District and Lok Sabha constituency in Jharkhand, India. |
| yes | 0.63 | - | recognised (11, 0.41) | scheme | ? | River Valley Project | Government irrigation and power generation project on a river. |
| yes | 0.89 | - | recognised (12, 0.41) | topic |  | Rural Development | Improving infrastructure and services in rural areas. |
| yes | 1.00 | 0.88 | dict | place | ? | Konar Dam | कोनार डैम |
| yes | 0.96 | 0.86 | dict | place | other | Tilaiya Dam | तिलैया डैम |
| yes | 1.00 | 0.91 | dict | place |  | Jharkhand | झारखंड |

## Bidyut Baran Mahato: The Union Budget (2025-2026) - Demands for Grants - Ministry of Railways

2025-03-17, 1560 words, state `speech`. Speech id 290252.

**Summary.** Supports the Demands for Grants for the Ministry of Railways, highlighting modernization, infrastructure expansion, and requesting new train services and stoppages for his constituency.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Railway infrastructure development | भारतीय रेल के विकास |
| yes | 0.81 | - | llm | topic |  | Railway safety and accident reduction | दुर्घटनाएँ |
| yes | 0.93 | - | llm | topic |  | Station modernization and passenger amenities | अमृत स्टेशन्‍स |
| yes | 0.99 | - | llm | topic |  | New train services and line expansions | वंदे भारत ट्रेन्स |
| yes | 0.99 | - | llm | topic |  | Constituency railway demands | अपने संसदीय क्षेत्र से जुड़ी रेल संबंधित समस्याओं |
| yes | 0.61 | - | recognised (1, 0.39) | scheme | ? | Amrit Bharat Station Scheme | Government program that modernises railway stations. |
| yes | 0.98 | - | recognised (2, 0.40) | topic |  | Railway Development | Expansion and improvement of railway infrastructure and services. |
| yes | 0.96 | - | recognised (3, 0.40) | scheme | ? | Vande Bharat | Semi high-speed train service run by Indian Railways. |
| yes | 0.97 | - | recognised (4, 0.41) | law | ? | Railway Budget | Annual government allocation for railway operations and development. |
| yes | 0.96 | - | recognised (5, 0.41) | institution | ? | Vande Bharat Express | High-speed rail service connecting Indian cities |
| yes | 0.96 | - | recognised (6, 0.41) | topic |  | Rail Budget | Annual financial allocation for railway services |
| yes | 0.99 | - | recognised (7, 0.43) | institution | ? | Indian Railways | Government rail organization. |
| yes | 0.97 | - | recognised (8, 0.43) | topic |  | New Railway Line | Construction of new railway routes and tracks. |
| no | 0.00 | - | recognised (9, 0.43) | institution | ? | Rail Vikas Nigam Limited | Government company constructing railway infrastructure |
| no | 0.00 | - | recognised (10, 0.43) | scheme | ? | Diamond Quadrilateral Project | Government project linking four major Indian cities by high-speed rail. |
| no | 0.00 | - | recognised (11, 0.43) | institution | ? | IRCTC | Government company managing railway bookings and catering. |
| yes | 0.98 | - | recognised (12, 0.43) | topic |  | Railway Projects | Development and implementation of railway infrastructure and services. |
| no | 0.98 | 0.40 | llm | institution |  | Ministry of Railways | भारतीय रेलवे |
| yes | 0.90 | 0.91 | llm | scheme | other | Vande Bharat Express | वंदे भारत ट्रेन्स |
| no | 0.36 | 0.77 | llm | scheme |  | Amrit Bharat Station Scheme | अमृत स्टेशन्‍स |
| yes | 0.98 | 0.93 | llm | place |  | Jharkhand | झारखंड |
| no | 0.32 | 0.88 | llm | place |  | Jamshedpur | जमशेदपुर |
| yes | 1.00 | 0.80 | dict | group | place | Tata | टाटा |
| yes | 0.86 | 0.94 | dict | person |  | Narendra Modi | मोदी जी |
| yes | 1.00 | 0.94 | dict | institution |  | Indian Railways | भारतीय रेलवे |
| yes | 0.99 | 0.90 | dict | place |  | Tatanagar | टाटानगर |
| yes | 0.98 | 0.87 | dict | place |  | Howrah | हावड़ा |
| yes | 0.96 | 0.84 | dict | group | institution | National Democratic Alliance | एनडीए |
| yes | 0.99 | 0.76 | dict | place |  | Chatra | चतरा |
| yes | 0.98 | 0.77 | dict | place |  | Chakulia | चाकुलिया |

## Dulu Mahato: Title : Need to close the discontinued/abandoned coal mines in appropriate manner in Dhanbad, Jharkhand-laid

2025-03-24, 166 words, state `speech`. Speech id 202862.

**Summary.** Asks the Minister of Coal to ensure that abandoned and closed coal mines in Dhanbad are closed properly under approved mine closure plans to prevent environmental and safety hazards.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Abandoned coal mine closure | कोयला खदानें |
| yes | 0.99 | - | llm | topic |  | Environmental and safety hazards | पर्यावरणीय तथा स्थानीय समुदायों के लिए भी गंभीर खतरे *(not in text)* |
| yes | 0.97 | - | recognised (1, 0.37) | place | ? | Dhanbad | District and Lok Sabha constituency in Jharkhand, India. |
| yes | 0.70 | - | recognised (2, 0.41) | institution | ? | Coal Ministry | Ministry overseeing coal sector development |
| yes | 0.70 | - | recognised (3, 0.42) | topic |  | Coal Blocks | Areas of land assigned for coal mining. |
| no | 0.00 | - | recognised (4, 0.42) | institution | ? | Eastern Coalfields Ltd | Government coal mining company. |
| no | 0.02 | - | recognised (5, 0.43) | institution | ? | Coal India Ltd | Major government-owned company that mines and supplies coal in India. |
| no | 0.00 | - | recognised (6, 0.43) | topic |  | Mines Mafia | Organized crime in mining operations. |
| no | 0.00 | - | recognised (7, 0.43) | place | ? | East Singhbhum | District in Jharkhand, India. |
| yes | 0.99 | - | recognised (8, 0.43) | topic |  | Coal Mining | The extraction of coal from underground or surface deposits. |
| no | 0.00 | - | recognised (9, 0.43) | institution | ? | Central Coalfield Ltd | Government coal mining company in central India |
| yes | 1.00 | - | recognised (10, 0.43) | topic |  | Mines | Sites where minerals or ores are dug out of the earth. |
| no | 0.00 | - | recognised (11, 0.43) | topic |  | Fly-ash | Fine waste left over from burning coal in power plants. |
| no | 0.00 | - | recognised (12, 0.43) | place | ? | Asansol | Lok Sabha constituency in West Bengal, India. |
| no | 1.00 | 0.46 | dict | institution |  | Ministry of Coal | कोयला मंत्री |
| yes | 1.00 | 0.89 | dict | place |  | Dhanbad | धनबाद |

## Utkarsh Verma Madhur: Title : Need to restore Old Pension Scheme-laid

2025-03-24, 220 words, state `speech`. Speech id 202869.

**Summary.** Urges the government to abolish the New Pension Scheme and Integrated Pension Scheme and restore the Old Pension Scheme for teachers, government employees, and paramilitary forces.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Restoration of Old Pension Scheme | एन.पी.एस. तथा यू.पी.एस. व्यवस्था समाप्त कर पुरानी पेंशन व्यवस्था बहाल करने |
| yes | 0.99 | - | recognised (1, 0.36) | scheme | ? | National Pension System | Government retirement savings scheme where contributions build a pension. |
| no | 0.00 | - | recognised (2, 0.38) | scheme | ? | One-Rank-One-Pension | Government scheme that gives the same pension to soldiers of the same rank and service length. |
| yes | 0.94 | - | recognised (3, 0.39) | scheme | ? | UNIFIED PENSION SCHEME(UPS) | Government pension scheme that unifies retirement benefits for public sector staff. |
| no | 0.00 | - | recognised (4, 0.40) | scheme | ? | Atal Pension Yojana | Government pension scheme for workers in the unorganised sector. |
| no | 0.23 | - | recognised (5, 0.40) | law | ? | Central Civil Services (Pension) Rules | Government regulations for employee pensions |
| yes | 0.99 | - | recognised (6, 0.41) | topic |  | Pension Schemes | General government programs that pay regular income to retired people. |
| no | 0.00 | - | recognised (7, 0.41) | scheme | ? | New Education Policy | Government policy document that reforms the structure of the education system. |
| yes | 0.75 | - | recognised (8, 0.41) | scheme | ? | Employees Pension Scheme | Government retirement pension scheme for workers, run with the provident fund. |
| yes | 0.99 | - | recognised (9, 0.41) | topic |  | Pension Reforms | Changes to retirement benefit systems. |
| no | 0.00 | - | recognised (10, 0.42) | law | ? | One Nation, One Voter List | Proposal for unified electoral roll across country |
| no | 0.02 | - | recognised (11, 0.42) | institution | ? | Employees Provident Fund Organisation | The government body that manages retirement savings for Indian workers. |
| yes | 0.97 | - | recognised (12, 0.42) | topic |  | Old Age Benefits | Support for elderly. |
| yes | 0.85 | 0.93 | llm | place |  | Uttar Pradesh | उत्तर प्रदेश |
| yes | 0.98 | 0.91 | dict | group |  | Teachers | शिक्षकों |

## Pradyut Bordoloi: Need to conduct Elephant Specific Environment Impact Assessments (EIAs) in different areas of Assam to address human-elephant conflicts in the State.-laid

2025-03-26, 196 words, state `speech`. Speech id 202100.

**Summary.** Asks for elephant-specific Environment Impact Assessments and Conflict Management Task Forces in Assam to address human-elephant conflicts.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Human-elephant conflict | human-elephant conflict |
| yes | 0.98 | - | llm | topic |  | Environmental impact assessment | Environment Impact Assessments |
| yes | 0.99 | - | recognised (1, 0.35) | topic |  | Man-Animal Conflict | Clashes between human communities and wild animals. |
| yes | 0.99 | - | recognised (2, 0.38) | topic |  | Elephants | Large mammals and efforts to protect them. |
| no | 0.00 | - | recognised (3, 0.41) | topic |  | Tigers | A large wild cat species that needs conservation and protection. |
| no | 0.00 | - | recognised (4, 0.41) | topic |  | Leopard Attacks | Incidents where leopards attack or injure people. |
| yes | 0.66 | - | recognised (5, 0.41) | topic |  | Environmental Clearance | Official approval required before a project can affect the environment. |
| no | 0.00 | - | recognised (6, 0.41) | place | ? | Kaziranga | Lok Sabha constituency in Assam, India. |
| yes | 0.99 | - | recognised (7, 0.42) | place | ? | Assam | State in northeastern India |
| yes | 0.98 | - | recognised (8, 0.42) | topic |  | Animal Protection | Laws and actions that protect wild animals and their habitats. |
| no | 0.00 | - | recognised (9, 0.43) | place | ? | Jorhat | District and Lok Sabha constituency in Assam, India. |
| no | 0.00 | - | recognised (10, 0.43) | scheme | ? | Project Tiger | Government program that protects the endangered tiger population. |
| no | 0.00 | - | recognised (11, 0.43) | place | ? | Dibrugarh | District and Lok Sabha constituency in Assam, India. |
| yes | 0.98 | - | recognised (12, 0.43) | topic |  | Environmental Impact | The effect that human activity has on the natural world. |
| yes | 1.00 | 0.89 | llm | place |  | Assam | Assam |
| no | 0.12 | 0.85 | llm | place |  | West Karbi Anglong | West Karbi Anglong |
| no | 0.97 | 0.46 | llm | institution |  | Elephant Task Force | Elephant Task Force |
| yes | 0.74 | 0.68 | dict | institution |  | Forest Department | Forest Department |

## Dushyant Singh: Need to expedite completion of Parvan River Multipurpose Project in Rajasthan

2025-03-28, 208 words, state `speech`. Speech id 201260.

**Summary.** Urges expedited completion of the Parwan-Akawad water project phases to provide drinking water and irrigation to Jhalawar, Baran, and Kota.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Water resource project | परवन-अकावद वाटर प्रोजेक्ट |
| no | 0.00 | - | recognised (1, 0.38) | institution | ? | Indira Gandhi Canal Project | Large irrigation infrastructure in Rajasthan. |
| yes | 0.91 | - | recognised (2, 0.38) | place | ? | Kota | District and Lok Sabha constituency in Rajasthan, India. |
| yes | 0.97 | - | recognised (3, 0.39) | place | ? | Jhalawar–Baran | Lok Sabha constituency in Rajasthan, India. |
| no | 0.02 | - | recognised (4, 0.39) | topic |  | Inter-linking of rivers | A plan to connect separate river systems by canals. |
| no | 0.00 | - | recognised (5, 0.40) | scheme | ? | Jal Jeevan Mission | Government mission that supplies piped tap water to every rural household. |
| no | 0.00 | - | recognised (6, 0.40) | scheme | ? | Accelerated Rural Water Supply Programme | Government program that provides safe drinking water in rural areas. |
| no | 0.04 | - | recognised (7, 0.40) | scheme | ? | Accelerated Irrigation Benefit Programme | Government program that speeds up the completion of irrigation projects. |
| yes | 0.99 | - | recognised (8, 0.40) | topic |  | Water Projects | Infrastructure for storage supply and management of water. |
| no | 0.19 | - | recognised (9, 0.40) | topic |  | Water Conservation | Measures to protect and save water resources for future use. |
| yes | 0.90 | - | recognised (10, 0.40) | topic |  | Drinking Water Projects | Infrastructure providing safe drinking water. |
| yes | 0.87 | - | recognised (11, 0.40) | place | ? | Baran | District in Rajasthan, India. |
| no | 0.03 | - | recognised (12, 0.40) | scheme | ? | Pradhan Mantri Sichayeen Yojana | Government scheme that expands irrigation to farmland across the country. |
| yes | 1.00 | 0.67 | llm | scheme |  | Parwan River Multipurpose Project | परवन-अकावद वाटर प्रोजेक्ट |
| yes | 1.00 | 0.82 | llm | place |  | Jhalawar | झालावाड़ |
| yes | 1.00 | 0.78 | llm | place |  | Baran | बारां |
| yes | 0.99 | 0.83 | llm | place |  | Kota | कोटा |
| yes | 1.00 | 0.91 | dict | group |  | Farmers | किसानों |

## Jugal Kishore: Need to construct road to facilitate Parikrama of Trikuta Parvat, the abode of Mata Vaishno Devi Temple in Katra in Jammu and Kashmir - Laid

2025-03-28, 188 words, state `speech`. Speech id 201301.

**Summary.** Asks the Ministry to construct a road for the parikrama of Trikuta Parvat in Katra to facilitate pilgrims visiting the Mata Vaishno Devi Temple.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Road infrastructure and pilgrimage | त्रिकुटा पर्वत की भी परिक्रमा के लिए |
| no | 0.00 | - | recognised (1, 0.37) | scheme | ? | PRASAD Scheme | Government scheme that develops pilgrimage and heritage sites for tourism. |
| no | 0.00 | - | recognised (2, 0.39) | topic |  | Amarnath Yatra | Annual pilgrimage to Amarnath cave in Kashmir |
| no | 0.01 | - | recognised (3, 0.39) | scheme | ? | Swadesh Darshan Scheme | Government program that develops tourism and pilgrimage infrastructure. |
| no | 0.13 | - | recognised (4, 0.41) | place | ? | Jammu | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | recognised (5, 0.41) | scheme | ? | Prime Minister Gram Sadak Yojana (PMGSY) | Government program that builds all-weather roads to connect rural villages. |
| yes | 0.99 | - | recognised (6, 0.41) | topic |  | Road Construction | Building or improving roads and highways. |
| no | 0.00 | - | recognised (7, 0.41) | place | ? | Srinagar | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | recognised (8, 0.41) | place | ? | Udhampur | District and Lok Sabha constituency in Jammu and Kashmir, India. |
| no | 0.00 | - | recognised (9, 0.42) | place | ? | Kathua | District in Jammu and Kashmir, India. |
| no | 0.00 | - | recognised (10, 0.42) | institution | ? | National Highways Authority of India (NHAI) | The government body that builds and manages India's national highways. |
| no | 0.01 | - | recognised (11, 0.42) | topic |  | Border Roads | Roads built and kept up in areas near India's border. |
| no | 0.00 | - | recognised (12, 0.42) | scheme | ? | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.51 | 0.79 | llm | place |  | Jammu and Kashmir | जम्मू कश्मीर *(not in text)* |
| yes | 1.00 | 0.91 | llm | place |  | Katra | कटरा |
| yes | 1.00 | 0.93 | llm | institution | place | Mata Vaishno Devi Temple | माता वैष्णो देवी मंदिर |
| yes | 1.00 | 0.88 | dict | group |  | Pilgrims | श्रद्धालुओं |
| no | 0.13 | 0.89 | dict | place |  | Govardhan | गोवर्धन |
| no | 0.19 | 0.71 | dict | place |  | Reasi | रियासी |
| no | 0.06 | 0.90 | dict | place |  | Mathura | मथुरा |

## D. Purandeswari: Regarding Need for introduction of graded front of pack nutrition label and 'health tax' on sugary beverages and ultra-processed junk foods-laid

2025-04-01, 205 words, state `speech`. Speech id 201197.

**Summary.** Urges the Government to introduce graded front-of-pack nutrition labels and levy a health tax on sugary beverages and ultra-processed foods to combat non-communicable diseases.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Public health and nutrition | obesity, diabetes, and non-communicable diseases |
| yes | 0.99 | - | llm | topic |  | Food labeling and taxation | graded front-of-pack nutrition label |
| yes | 0.98 | - | recognised (1, 0.37) | law | ? | Nutrition Policy | Government decisions on dietary standards |
| yes | 0.76 | - | recognised (2, 0.38) | topic |  | Non-Communicable Diseases | Chronic diseases like diabetes and heart disease not spread between people |
| yes | 0.99 | - | recognised (3, 0.39) | topic |  | Nutrition | Dietary intake and nutritional health of population |
| yes | 0.94 | - | recognised (4, 0.41) | topic |  | Junk Food | Food high in calories and low in nutrients. |
| no | 0.00 | - | recognised (5, 0.42) | topic |  | Pan Masala | Betel leaf preparation with health concerns |
| no | 0.00 | - | recognised (6, 0.42) | topic |  | Health Supplements | Products added to the diet to give extra nutrients. |
| no | 0.52 | - | recognised (7, 0.42) | topic |  | Nutritious Food | Food providing essential nutrients for health. |
| no | 0.00 | - | recognised (8, 0.43) | topic |  | One Nation One Tax | A plan for one uniform tax system across India. |
| no | 0.00 | - | recognised (9, 0.43) | scheme | ? | National Health Policy | Government document that sets goals and direction for the health system. |
| no | 0.00 | - | recognised (10, 0.43) | topic |  | Cancer | Serious disease affecting population health |
| yes | 0.93 | - | recognised (11, 0.43) | topic |  | Chronic Diseases | Long-term illnesses affecting health over extended periods |
| yes | 0.99 | - | recognised (12, 0.43) | topic |  | Health Policy | Government policies and programs for public health |
| yes | 1.00 | 0.92 | llm | place |  | India | India |
| no | 0.23 | 0.91 | llm | place |  | Singapore | Singapore |
| no | 0.83 | 0.55 | dict | law | other | Economic Survey | Economic Survey |
| no | 0.01 | 0.89 | dict | place |  | Thailand | Thailand |
| no | 0.01 | 0.89 | dict | place |  | Malaysia | Malaysia |

## Naveen Jindal: Need to conduct National Skill Census for better employment of the youths for national growth

2025-04-03, 180 words, state `speech`. Speech id 200186.

**Summary.** Urges the central government to conduct a nationwide National Skill Census to address skill mismatch and promote youth employment.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Skill development | स्किल डेवलपमेंट |
| yes | 0.99 | - | llm | topic |  | Skill mismatch | स्किल मिसमैच |
| yes | 0.99 | - | llm | topic |  | Youth employment | युवाओं को केवल नौकरी |
| no | 0.02 | - | llm | topic |  | Artificial intelligence | आर्टिफिशियल इंटेलिजेंस |
| no | 0.06 | - | recognised (1, 0.34) | scheme | ? | Skill India Mission | Government program that trains people in job skills. |
| no | 0.00 | - | recognised (2, 0.36) | scheme | ? | Deen Dayal Upadhyaya Grameen Kaushal Yojana | Government scheme that trains rural youth in job skills. |
| no | 0.00 | - | recognised (3, 0.38) | scheme | ? | Deen Dayal Upadhyaya Antyodaya Yojana | Government scheme for poverty reduction through skills and self-employment. |
| no | 0.00 | - | recognised (4, 0.38) | law | ? | Caste Census | Survey to count population by caste groups for government statistics. |
| no | 0.00 | - | recognised (5, 0.38) | scheme | ? | National Livelihood Mission | Government program that supports skill development and self-employment for the poor. |
| yes | 0.99 | - | recognised (6, 0.39) | topic |  | Skill Development | Training to improve competencies. |
| no | 0.00 | - | recognised (7, 0.39) | scheme | ? | TRYSEM | Government program that trained rural youth to become self-employed. |
| no | 0.00 | - | recognised (8, 0.39) | scheme | ? | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| no | 0.00 | - | recognised (9, 0.39) | scheme | ? | E-Shram Portal | Government online database that registers workers in the informal sector. |
| no | 0.00 | - | recognised (10, 0.40) | topic |  | Industrial Training Institutes | Government schools that teach practical job skills. |
| no | 0.00 | - | recognised (11, 0.40) | scheme | ? | National Literacy Mission | Government program that raises reading and writing skills across the population. |
| no | 0.00 | - | recognised (12, 0.40) | institution | ? | Nehru Yuva Kendra Sangathan | Government organization for youth development. |
| yes | 1.00 | 0.90 | llm | scheme |  | National Skill Census | राष्ट्रीय कौशल जनगणना |
| yes | 1.00 | 0.90 | llm | group |  | Youth | युवाओं |

## Manoj Tiwari: Regarding need to construct a building complex for police department in North East Delhi district-Laid

2025-07-25, 176 words, state `speech`. Speech id 198444.

**Summary.** Requests the Home Minister to construct a police line building complex in North East Delhi to improve law enforcement and security.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Police infrastructure development | कानून व्यवस्था को सुदृढ़ करने हेतु आवश्यक ढांचागत सुधारों |
| yes | 0.99 | - | recognised (1, 0.38) | place | ? | North East Delhi | District and Lok Sabha constituency in Delhi, India. |
| yes | 0.91 | - | recognised (2, 0.40) | institution | ? | Delhi Police | Police force of Delhi |
| no | 0.50 | - | recognised (3, 0.41) | topic |  | Police reforms | Changes to law enforcement practices. |
| no | 0.00 | - | recognised (4, 0.41) | topic |  | First Information Report (FIR) | A written police record of a complaint that starts a criminal investigation. |
| no | 0.34 | - | recognised (5, 0.41) | place | ? | East Delhi | District and Lok Sabha constituency in Delhi, India. |
| no | 0.59 | - | recognised (6, 0.42) | institution | ? | Home Ministry | Government department for internal security |
| no | 0.00 | - | recognised (7, 0.42) | institution | ? | Central Reserve Police Force (CRPF) | Paramilitary force that handles internal security and riot control in India. |
| yes | 0.99 | - | recognised (8, 0.42) | institution | ? | Police | Government law enforcement agency responsible for public safety and crime. |
| no | 0.00 | - | recognised (9, 0.42) | topic |  | Naxalism Control | Counter-insurgency against left-wing extremism. |
| no | 0.00 | - | recognised (10, 0.42) | institution | ? | North-Eastern Council (NEC) | Regional body for development in North Eastern states. |
| no | 0.44 | - | recognised (11, 0.42) | institution | ? | Police Stations | Local law enforcement outposts. |
| no | 0.00 | - | recognised (12, 0.42) | law | ? | The Government of National Capital Territory of Delhi(Amendment)Bill, 2023 | Legislative amendment changing governance of Delhi territory. |
| yes | 1.00 | 0.91 | dict | place |  | North East Delhi | उत्तर पूर्वी दिल्ली |
| yes | 1.00 | 0.91 | dict | group | institution | Police | पुलिस |
| no | 0.99 | 0.47 | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |
| no | 0.15 | 0.02 | dict | scheme | other | Aadhaar | आधार |

## Ummeda Ram Beniwal: Regarding payment of pending dues under MGNREGS-laid

2025-07-28, 208 words, state `speech`. Speech id 198328.

**Summary.** Asks the government to clear pending payments for material suppliers and artisans under MGNREGA in Rajasthan and resolve technical and administrative bottlenecks.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | MGNREGA pending payments | मटेरियल सप्लायरों एवं मेट कारीगरों का राज्य में लगभग 3800 करोड़ |
| yes | 0.99 | - | recognised (1, 0.37) | scheme | ? | Mahatma Gandhi National Rural Employment Guarantee Act (MNREGA) | Government law that guarantees 100 days of paid work a year to rural workers. |
| yes | 0.98 | - | recognised (2, 0.38) | law | ? | National Rural Employment Guarantee Act (NREGA) | Government guarantee of employment for rural workers |
| no | 0.36 | - | recognised (3, 0.41) | scheme | ? | The Viksit Bharat – Guarantee for Rozgar and Ajeevika Mission (Gramin) VB – G RAM G Bill | Government program aimed at rural employment and livelihoods. |
| no | 0.00 | - | recognised (4, 0.41) | scheme | ? | Food For Work Programme | Government scheme that pays workers with food grains for their labour. |
| no | 0.18 | - | recognised (5, 0.41) | scheme | ? | National Livelihood Mission | Government program that supports skill development and self-employment for the poor. |
| yes | 0.96 | - | recognised (6, 0.41) | place | ? | Rajasthan | State in northwestern India |
| yes | 0.99 | - | recognised (7, 0.41) | topic |  | Arrears | Outstanding payments due. |
| no | 0.40 | - | recognised (8, 0.42) | scheme | ? | Garib Kalyan Rozgar Yojana | Government scheme that gave paid work to migrant workers in their home villages. |
| no | 0.00 | - | recognised (9, 0.42) | topic |  | Migrant Problems | Issues faced by migrant workers and displaced persons |
| no | 0.00 | - | recognised (10, 0.42) | topic |  | Job Cards | A registration document for workers under a rural job guarantee scheme. |
| yes | 0.85 | - | recognised (11, 0.42) | topic |  | Employment Guarantee | General government promise to give people paid work when they need it. |
| no | 0.00 | - | recognised (12, 0.42) | scheme | ? | Minimum Support  Prices (MSP) | Government guarantee of a minimum price paid to farmers for their crops. |
| yes | 1.00 | 0.83 | llm | law | ? | Mahatma Gandhi National Rural Employment Guarantee Act | मनरेगा |
| yes | 1.00 | 0.90 | llm | place |  | Rajasthan | राजस्थान |
| yes | 0.94 | 0.86 | llm | place |  | Barmer | बाड़मेर |

## Deepender Singh Hooda: Special discussion on India's Strong, Successful and Decisive 'Operation Sindoor' in response to Terrorist Attack in Pahalgam

2025-07-28, 250 words, state `speech`. Speech id 198361.

**Summary.** Criticises the reduction in India's defence budget as a share of GDP, squadron shortages in the air force, and the Agniveer recruitment scheme.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Defence budget | रक्षा बजट |
| yes | 0.96 | - | llm | topic |  | Air force modernisation | एयरफोर्स मॉडर्नाइजेशन |
| yes | 0.97 | - | llm | topic |  | Fighter squadron shortage | स्क्वाड्रन्स |
| yes | 0.88 | - | llm | topic |  | Military aircraft crashes | जहाज क्रैश |
| no | 0.02 | - | recognised (1, 0.35) | scheme | ? | Agniveer | Government short-service scheme for recruiting soldiers into the armed forces. |
| no | 0.00 | - | recognised (2, 0.39) | topic |  | Rafale Deal | India's purchase of Rafale fighter jets from France. |
| yes | 0.99 | - | recognised (3, 0.40) | institution | ? | Air Force | The air-based branch of India's armed forces. |
| yes | 0.99 | - | recognised (4, 0.41) | institution | ? | Defence Forces | The armed forces responsible for defending India. |
| yes | 0.99 | - | recognised (5, 0.42) | topic |  | Armed Forces | The military organizations of a country, including army, navy, and air force. |
| no | 0.28 | - | recognised (6, 0.43) | institution | ? | Army | The land-based branch of India's armed forces. |
| yes | 1.00 | - | recognised (7, 0.43) | topic |  | Defence Budget | The money a government sets aside for military spending. |
| no | 0.00 | - | recognised (8, 0.43) | scheme | ? | One-Rank-One-Pension | Government scheme that gives the same pension to soldiers of the same rank and service length. |
| yes | 1.00 | - | recognised (9, 0.43) | topic |  | Budget | India's yearly financial plan, showing the government's planned income and spending. |
| no | 0.00 | - | recognised (10, 0.43) | institution | ? | Indian Navy | The sea-based branch of India's armed forces. |
| yes | 0.94 | - | recognised (11, 0.43) | topic |  | Defence Personnel | People who serve as members of the armed forces. |
| no | 0.00 | - | recognised (12, 0.43) | institution | ? | Defence Res & Dev Organisation (DRDO) | Organization developing defense technology. |
| yes | 1.00 | 0.89 | llm | institution |  | Indian Air Force | एयरफोर्स |
| yes | 0.94 | 0.83 | llm | scheme |  | Agnipath Scheme | अग्निवीर |
| yes | 0.67 | 0.92 | llm | place |  | Haryana | हरियाणा |
| yes | 0.71 | 0.87 | llm | group |  | Pilots | पायलट्स |
| no | 0.99 | 0.36 | dict | institution |  | Ministry of Defence | रक्षा मंत्री |
| yes | 0.99 | 0.62 | dict | institution |  | Standing Committee | स्टैंडिंग कमेटी |
| yes | 0.68 | 0.85 | dict | person |  | Rahul Gandhi | राहुल जी |

## Vishaldada Prakashbapu Patil: Special discussion on India's Strong, Successful and Decisive 'Operation Sindoor' in response to Terrorist Attack in Pahalgam

2025-07-28, 2052 words, state `speech`. Speech id 198410.

**Summary.** Discusses Operation Sindoor in response to the Pahalgam terrorist attack, praising the armed forces and debating security, defence capabilities, and political accountability.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Operation Sindoor anti-terror strike | Operation Sindoor *(not in text)* |
| yes | 0.99 | - | llm | topic |  | National security and defence preparedness | डिफेंस के बजट |
| yes | 0.99 | - | recognised (1, 0.31) | topic |  | Operation Sindoor | A named military or security operation carried out by India's defence forces. |
| no | 0.00 | - | recognised (2, 0.40) | topic |  | Kargil War | A military conflict fought between India and Pakistan in 1999. |
| yes | 0.77 | - | recognised (3, 0.40) | topic |  | Surgical Strike | A precise military attack aimed at a specific enemy target. |
| yes | 0.99 | - | recognised (4, 0.40) | institution | ? | Defence Forces | The armed forces responsible for defending India. |
| no | 0.00 | - | recognised (5, 0.41) | law | ? | Armed Forces Special Powers Act (AFSPA) | Statute granting military powers in conflict zones |
| yes | 0.98 | - | recognised (6, 0.41) | topic |  | Security Forces | Military and police personnel responsible for national security. |
| no | 0.00 | - | recognised (7, 0.41) | topic |  | Operation Bluestar | Military operation storming Golden Temple in 1984 |
| no | 0.00 | - | recognised (8, 0.42) | topic |  | Operation Green Hunt | Counterinsurgency campaign against Maoist militants |
| no | 0.02 | - | recognised (9, 0.42) | institution | ? | Lashkar-e-Taiba | Terrorist organization designated for attacks on Indian military and civilians. |
| no | 0.00 | - | recognised (10, 0.42) | institution | ? | Central Reserve Police Force (CRPF) | Paramilitary force that handles internal security and riot control in India. |
| yes | 0.97 | - | recognised (11, 0.42) | law | ? | Defence Policy | Government strategy for military strength and security |
| no | 0.00 | - | recognised (12, 0.42) | institution | ? | National Security Guards (NSGs) | Elite force that protects VIPs and responds to major security threats. |
| yes | 0.74 | 0.89 | llm | scheme | other | BrahMos | ब्रह्मोस |
| yes | 0.88 | 0.93 | llm | law |  | Article 370 | अनुच्छेद 370 |
| yes | 0.96 | 0.85 | llm | place |  | Pahalgam | पहलगाम |
| no | 0.59 | 0.81 | llm | person |  | Tahawwur Rana | तहव्वुर राणा |
| yes | 0.99 | 0.91 | dict | person |  | Rahul Gandhi | राहुल गांधी |
| yes | 1.00 | 0.92 | dict | place |  | Pakistan | पाकिस्तान |
| yes | 1.00 | 0.79 | dict | scheme | other | Operation Sindoor | ऑपरेशन सिंदूर |
| no | 0.98 | 0.46 | dict | institution |  | Ministry of Defence | रक्षा मंत्री |
| yes | 0.99 | 0.85 | dict | place |  | Pakistan-occupied Kashmir | पीओके |
| yes | 0.90 | 0.80 | dict | group |  | Muslims | मुस्लिम |
| yes | 1.00 | 0.86 | dict | group | ? | Opposition | विपक्ष |
| yes | 0.98 | 0.76 | dict | person |  | Gaurav Gogoi | गौरव गोगोई |

## Kangna Ranaut: Regarding relief and rehabilitation measures in Mandi district, Himachal Pradesh affected by cloudburst-Laid

2025-07-29, 187 words, state `speech`. Speech id 181008.

**Summary.** Seeks details from the central government on relief, rehabilitation, and long-term mitigation measures for the cloudburst-affected Mandi district in Himachal Pradesh.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Disaster relief | राहत और पुनर्वास |
| yes | 0.99 | - | llm | topic |  | Cloudburst disaster | बादल फटने की घटना |
| yes | 0.91 | - | llm | topic |  | Infrastructure restoration | क्षतिग्रस्त बुनियादी ढाँचे के पुनर्निर्माण |
| yes | 0.98 | - | recognised (1, 0.37) | place | ? | Mandi | District and Lok Sabha constituency in Himachal Pradesh, India. |
| no | 0.03 | - | recognised (2, 0.40) | scheme | ? | National Calamity Contingency Fund (NECF) | Central government emergency fund for relief after a natural disaster. |
| yes | 0.94 | - | recognised (3, 0.40) | topic |  | Flood Relief | Government assistance to flooded areas. |
| no | 0.00 | - | recognised (4, 0.40) | scheme | ? | PM-CARES Fund | Prime minister's relief fund set up for national emergencies. |
| no | 0.11 | - | recognised (5, 0.42) | scheme | ? | National Disaster Relief Fund | Government fund that provides financial aid for natural disaster recovery. |
| yes | 0.99 | - | recognised (6, 0.42) | topic |  | Relief Measures | Government help given to people hurt by a disaster or hardship. |
| no | 0.00 | - | recognised (7, 0.42) | scheme | ? | Prime Minister's National Relief Fund | Government fund controlled by the prime minister for emergency relief. |
| no | 0.00 | - | recognised (8, 0.42) | place | ? | Lahaul and Spiti | District in Himachal Pradesh, India. |
| no | 0.00 | - | recognised (9, 0.42) | place | ? | Kangra | District and Lok Sabha constituency in Himachal Pradesh, India. |
| yes | 0.99 | - | recognised (10, 0.43) | topic |  | Rehabilitation | Support programs to help people recover from disasters or other hardships. |
| no | 0.00 | - | recognised (11, 0.43) | place | ? | Shimla | District and Lok Sabha constituency in Himachal Pradesh, India. |
| yes | 0.98 | - | recognised (12, 0.43) | topic |  | Central Assistance | Financial support by central government to states. |
| yes | 1.00 | 0.93 | llm | place |  | Himachal Pradesh | हिमाचल प्रदेश |
| yes | 1.00 | 0.87 | llm | place |  | Mandi | मंडी ज़िले |
| yes | 1.00 | 0.78 | llm | institution |  | National Disaster Response Force | एनडीआरएफ |
| yes | 0.99 | 0.72 | llm | institution |  | Indo-Tibetan Border Police | आईटीबीपी |
| no | 1.00 | 0.50 | dict | institution |  | Ministry of Home Affairs | गृह मंत्री |

## Bharti Pardhi: Regarding pollution caused due to HCL

2025-07-30, 221 words, state `speech`. Speech id 180841.

**Summary.** Raises concerns over severe environmental pollution, land degradation, and unfulfilled CSR promises caused by the Hindustan Copper Limited project in Malajhkhand.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Industrial pollution and land degradation | जहरीले रसायनिक तत्व के कारण क्षेत्र की उपजाऊ जमीन पूरी तरह से बंजर हो चुकी है |
| yes | 0.99 | - | recognised (1, 0.39) | institution | ? | Hindustan Copper Ltd | State-owned copper mining company |
| yes | 0.99 | - | recognised (2, 0.41) | topic |  | Environmental Degradation | The gradual decline in the quality of the natural environment. |
| yes | 0.99 | - | recognised (3, 0.41) | topic |  | Industrial Pollution | Environmental contamination caused by factories and manufacturing. |
| yes | 0.99 | - | recognised (4, 0.42) | topic |  | Environmental Pollution | General contamination of the environment by harmful substances. |
| yes | 0.99 | - | recognised (5, 0.42) | topic |  | Chemical Pollution | Environmental contamination caused by chemical substances. |
| yes | 0.88 | - | recognised (6, 0.42) | topic |  | Farmers' Grievances | Complaints from agricultural workers |
| no | 0.00 | - | recognised (7, 0.42) | topic |  | Man-Animal Conflict | Clashes between human communities and wild animals. |
| yes | 0.98 | - | recognised (8, 0.42) | topic |  | Pollution Sources | The origins or causes of environmental contamination. |
| yes | 0.97 | - | recognised (9, 0.42) | topic |  | Soil Pollution | Contamination of land and soil by harmful substances. |
| no | 0.00 | - | recognised (10, 0.42) | topic |  | Radioactive Pollution | Environmental contamination caused by nuclear waste. |
| no | 0.00 | - | recognised (11, 0.43) | topic |  | Illegal Mining | Extraction of minerals or resources without official permission. |
| yes | 0.98 | - | recognised (12, 0.43) | topic |  | Public Grievances | Complaints from citizens |
| yes | 1.00 | 0.92 | llm | institution |  | Hindustan Copper Limited | हिन्दुस्तान कॉपर लिमिटेड |
| yes | 1.00 | 0.84 | llm | place |  | Malajhkhand | मलाजखंड |
| no | 0.06 | 0.02 | dict | institution |  | Ministry of Road Transport and Highways | विभाग |

## Hemang Joshi: Regarding urgent need of international flights from Vadodara Airport

2025-07-30, 165 words, state `speech`. Speech id 180958.

**Summary.** Requests the government to increase domestic flights from Vadodara Airport and restore its status for better regional connectivity.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Air connectivity | अंतर्राष्ट्रीय उड़ानों की अतिआवश्यक आवश्यकता |
| yes | 1.00 | - | recognised (1, 0.39) | place | ? | Vadodara | District and Lok Sabha constituency in Gujarat, India. |
| no | 0.40 | - | recognised (2, 0.39) | topic |  | Domestic airports | Airports that handle flights within India only. |
| no | 0.02 | - | recognised (3, 0.41) | institution | ? | Airports Authority Of India | Government agency that manages and operates India's airports. |
| no | 0.41 | - | recognised (4, 0.41) | topic |  | Domestic Flights | Air travel between airports within the same country. |
| no | 0.00 | - | recognised (5, 0.42) | institution | ? | DGCA | India's government regulator for civil aviation safety and rules. |
| no | 0.00 | - | recognised (6, 0.43) | institution | ? | Pawan Hans Ltd | A government-owned company that runs helicopter services. |
| no | 0.00 | - | recognised (7, 0.43) | scheme | ? | Sagarmala Project | Government plan to develop coastal ports and facilities. |
| no | 0.00 | - | recognised (8, 0.43) | institution | ? | Indian Airlines | A former state-run commercial airline of India. |
| no | 0.00 | - | recognised (9, 0.43) | scheme | ? | Vande Bharat Mission | Government program that brought Indian citizens home from abroad. |
| yes | 1.00 | - | recognised (10, 0.43) | topic |  | Air Connectivity | How well places are linked by air routes. |
| no | 0.00 | - | recognised (11, 0.43) | scheme | ? | UDAAN Scheme | Government scheme that supports small and medium businesses. |
| no | 0.00 | - | recognised (12, 0.44) | institution | ? | Air India | India's national airline, owned by the government in the past. |
| yes | 1.00 | 0.90 | llm | institution | place | Vadodara Airport | वडोदरा अंतर्राष्ट्रीय हवाई अड्डे |
| yes | 1.00 | 0.90 | llm | place |  | Gujarat | गुजरात |
| yes | 1.00 | 0.91 | llm | place |  | Vadodara | वडोदरा |
| no | 0.60 | 0.38 | llm | place |  | Anand | आनंदखेड़ा |
| yes | 0.67 | 0.84 | llm | place |  | Chhota Udaipur | छोटा उदयपुर |
| yes | 0.75 | 0.83 | llm | place |  | Panchmahal | पंचमहल |
| yes | 0.66 | 0.87 | llm | place |  | Dahod | दाहोद |
| no | 0.59 | 0.88 | llm | place |  | Bharuch | भरुच |
| no | 0.46 | 0.57 | dict | group |  | Scheduled Tribes | आदिवासी |

## P P Chaudhary: Regarding need to formulate a comprehensive Solar-Waste Management Policy and to establish an Advanced Solar-Panel Recycling Plant in Rajasthan- laid

2025-07-31, 189 words, state `speech`. Speech id 180735.

**Summary.** Asks the government to formulate a comprehensive solar-waste management policy and establish advanced recycling plants in Rajasthan.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Solar waste management | solar-panel waste |
| yes | 0.70 | - | recognised (1, 0.38) | topic |  | E-Waste Management | The disposal and recycling of discarded electronic devices. |
| no | 0.03 | - | recognised (2, 0.41) | scheme | ? | National Solar Energy Mission | Government program that promotes generating power from solar energy. |
| no | 0.00 | - | recognised (3, 0.41) | scheme | ? | Voluntary Auto Scrapping Policy | Government incentive that encourages recycling old vehicles to cut emissions. |
| yes | 0.99 | - | recognised (4, 0.42) | place | ? | Rajasthan | State in northwestern India |
| yes | 0.65 | - | recognised (5, 0.42) | topic |  | Electronic Waste | Discarded electronic devices and equipment. |
| no | 0.09 | - | recognised (6, 0.42) | law | ? | Power Sector Reforms | Government policy changes modernizing electricity generation and distribution. |
| no | 0.00 | - | recognised (7, 0.42) | place | ? | Jodhpur | District and Lok Sabha constituency in Rajasthan, India. |
| no | 0.00 | - | recognised (8, 0.43) | place | ? | Jaipur | District and Lok Sabha constituency in Rajasthan, India. |
| no | 0.00 | - | recognised (9, 0.43) | place | ? | Bhilwara | District and Lok Sabha constituency in Rajasthan, India. |
| no | 0.00 | - | recognised (10, 0.43) | place | ? | Ajmer | District and Lok Sabha constituency in Rajasthan, India. |
| yes | 0.99 | - | recognised (11, 0.43) | topic |  | Waste Recycling | The process of turning discarded materials into new products. |
| no | 0.00 | - | recognised (12, 0.43) | place | ? | Churu | District and Lok Sabha constituency in Rajasthan, India. |
| yes | 0.88 | 0.66 | llm | scheme |  | National Critical Mineral Mission | National Critical Mineral Mission |
| no | 0.45 | 0.79 | llm | law |  | E-Waste Management Rules | E-Waste Management Rules |
| yes | 1.00 | 0.92 | llm | place |  | Rajasthan | Rajasthan |
| yes | 1.00 | 0.92 | llm | institution |  | Ministry of New and Renewable Energy | Ministry of New and Renewable Energy |

## Ravindra Dattaram Waikar: The Protection and Welfare of Sanitation Workers Bill, 2024-Introduced

2025-12-05, 51 words, state `speech`. Speech id 179539.

**Summary.** Introduces a bill to provide regulations for the protection, welfare, and rehabilitation of sanitation workers.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 0.99 | - | llm | topic |  | Welfare of sanitation workers | protection, welfare and rehabilitation of sanitation workers |
| no | 0.10 | - | recognised (1, 0.36) | topic |  | Manual Scavengers | Workers engaged in manual removal of human waste |
| no | 0.00 | - | recognised (2, 0.37) | law | ? | Sabka Bima Sabki Raksha Bill | Insurance legislation for comprehensive coverage |
| no | 0.00 | - | recognised (3, 0.40) | topic |  | Weavers Welfare Measures | Support programs for textile workers |
| no | 0.16 | - | recognised (4, 0.40) | topic |  | Health Hazards | Environmental and occupational threats to public health. |
| no | 0.00 | - | recognised (5, 0.40) | law | ? | Reservation Bill | Legislation providing affirmative action quotas |
| yes | 0.93 | - | recognised (6, 0.41) | topic |  | Occupational Safety | Protection of workers from workplace hazards and injury. |
| no | 0.00 | - | recognised (7, 0.41) | scheme | ? | Rashtriya Swasthya Bima Yojana | Government health insurance scheme for workers in the unorganised sector. |
| no | 0.00 | - | recognised (8, 0.41) | law | ? | National Medical Commission Bill | Legislation regulating medical doctors and practice. |
| no | 0.00 | - | recognised (9, 0.41) | scheme | ? | Swachh Bharat Abhiyan | Government mission to improve sanitation and cleanliness across India. |
| no | 0.03 | - | recognised (10, 0.41) | topic |  | SCs and STs welfare | Support for scheduled communities |
| no | 0.02 | - | recognised (11, 0.41) | topic |  | Occupational Diseases | Illness caused by work activities. |
| yes | 0.62 | - | recognised (12, 0.41) | topic |  | Hygiene | Practices and conditions promoting sanitation and disease prevention. |
| yes | 0.96 | 0.87 | llm | law |  | The Protection and Welfare of Sanitation Workers Bill, 2024 | Bill |

## Kamaljeet Sehrawat: Regarding the issue of severe traffic congestion at Dwarka flyover

2025-12-05, 175 words, state `speech`. Speech id 179656.

**Summary.** Asks the Ministry of Road Transport and Highways and the Ministry of Housing and Urban Affairs to form a joint committee with the Delhi Government to address severe traffic congestion at Dwarka.

| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |
|---|---|---|---|---|---|---|---|
| yes | 1.00 | - | llm | topic |  | Traffic congestion | भीषण जाम |
| yes | 0.99 | - | recognised (1, 0.40) | topic |  | Urban Traffic | Movement of vehicles and congestion management in urban areas. |
| yes | 0.99 | - | recognised (2, 0.42) | topic |  | Traffic Congestion | Heavy traffic that blocks smooth movement and causes delay. |
| no | 0.01 | - | recognised (3, 0.42) | scheme | ? | Pradhan Mantri Gati Shakti Yojana | Government program that plans transport infrastructure across the country. |
| no | 0.04 | - | recognised (4, 0.42) | topic |  | Detailed Project Report (DPR) | A detailed document that plans and justifies a government infrastructure project before its approval. |
| no | 0.02 | - | recognised (5, 0.42) | topic |  | Joint Parliamentary Committee (JPC) | A committee formed from both houses of parliament to study one issue. |
| yes | 0.99 | - | recognised (6, 0.42) | topic |  | Road Traffic | The movement of vehicles on roads. |
| no | 0.01 | - | recognised (7, 0.42) | institution | ? | National Highways Authority of India (NHAI) | The government body that builds and manages India's national highways. |
| no | 0.00 | - | recognised (8, 0.43) | institution | ? | Delhi Development Authority (DDA) | The government agency that plans and builds Delhi's urban development. |
| yes | 0.98 | - | recognised (9, 0.43) | topic |  | Traffic Control | The management of vehicle movement on roads. |
| no | 0.00 | - | recognised (10, 0.43) | place | ? | Gurugram | District and Lok Sabha constituency in Haryana, India. The constituency is listed as Gurgaon. |
| no | 0.08 | - | recognised (11, 0.44) | place | ? | North West Delhi | District and Lok Sabha constituency in Delhi, India. |
| no | 0.00 | - | recognised (12, 0.44) | scheme | ? | Atal Mission for Rejuvenation and Urban Transformation (AMRUT) | Government program that improves basic infrastructure in cities. |
| yes | 1.00 | 0.87 | llm | place |  | Dwarka | द्वारका |
| yes | 1.00 | 0.81 | llm | institution |  | Ministry of Road Transport and Highways | सड़क एवं परिवहन मंत्रालय |
| yes | 1.00 | 0.81 | llm | institution |  | Ministry of Housing and Urban Affairs | शहरी कार्य मंत्रालय |
| yes | 1.00 | 0.88 | llm | institution |  | Delhi Government | दिल्ली सरकार |
| no | 0.41 | 0.84 | dict | scheme | ? | Dwarka Expressway | द्वारका एक्सप्रेस - वे |
| yes | 0.86 | 0.84 | dict | place |  | Palam | पालम |
| no | 0.92 | 0.51 | dict | place |  | Nagari | नगरी |
| yes | 0.98 | 0.89 | dict | place |  | Delhi | दिल्ली |

