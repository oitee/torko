# Coverage check of the place tags

Source: read-only SELECT from `speech_items`, type `place`, list `other`. A name is its `norm_name`.
These numbers measure coverage (the share of names that equal a tag name or alias). They do not measure accuracy.
The denominators are the distinct place names and the place items in the database.

Distinct place names: 8796. Place items: 73027 (kept by the judge: 31).

| Group | Names | Items | Kept items |
|---|---|---|---|
| equals exactly one new tag | 880 | 21639 | 6 |
| equals two or more new tags | 8 | 485 | 0 |
| equals an existing tag | 146 | 33347 | 17 |
| equals nothing | 7762 | 17556 | 8 |

Of the names that equal exactly one new tag, 20 names (701 items) are on the MODEL_ONLY list of scripts/link_entities.py. The exact rule skips them and the decision model decides.

## The 30 most frequent place names that match nothing

| Items | Name (most common spelling) |
|---|---|
| 828 | Mumbai |
| 188 | Bengaluru |
| 181 | Ganga |
| 114 | Marathwada |
| 84 | Santhal Pargana |
| 82 | Brahmaputra |
| 82 | Singapore |
| 77 | Australia |
| 76 | Amaravati |
| 75 | Yamuna |
| 68 | Kashmir |
| 63 | Kosi River |
| 63 | Rayalaseema |
| 61 | Bangalore |
| 59 | Western Ghats |
| 53 | Pahalgam |
| 52 | Sabarimala |
| 52 | Cauvery |
| 51 | Ukraine |
| 51 | Ganges |
| 50 | Godavari |
| 49 | Germany |
| 49 | Katchatheevu |
| 45 | North-East India |
| 45 | Kuttanad |
| 43 | Kochi |
| 41 | Bay of Bengal |
| 39 | Northeast India |
| 37 | Rameswaram |
| 36 | Kosi |

## 20 random names that equal exactly one new tag (seed 7)

| Items | Name | New tag | One mention from a speech |
|---|---|---|---|
| 13 | Hoshangabad | Narmadapuram | होशंगाबाद |
| 16 | Buldhana | Buldhana | बूलढाणा |
| 24 | Kanpur Dehat | Kanpur Dehat | कानपुर देहात |
| 63 | Raipur | Raipur | रायपुर |
| 11 | Aravalli | Aravalli | अरावली |
| 2 | Ballari | Ballari | Bellary |
| 9 | Vadakara | Vatakara | Vadakara |
| 8 | Morbi | Morbi | मोरबी |
| 1 | Bardhaman-Durgapur | Bardhaman–Durgapur | Bardhaman-Durgapur |
| 10 | Jind | Jind | जींद |
| 8 | Nilgiris | Nilgiris | Nilgris |
| 4 | Aurangabad, Bihar | Aurangabad (Bihar) | औरंगाबाद |
| 8 | Malkajgiri | Malkajgiri | मल्‍काजगिरी |
| 27 | Dehradun | Dehradun | देहरादून |
| 15 | Angul | Angul | अंगुल जिले |
| 54 | Banswara | Banswara | Banswara |
| 2 | Kishtwar | Kishtwar | किश्तवाड़ जिले |
| 2 | Khadoor Sahib | Khadoor Sahib | Khadoor Sahib |
| 10 | Balangir | Balangir | Balangir |
| 3 | Dum Dum | Dum Dum | Dum Dum |

## Names that equal two or more new tags (top 15)

| Items | Name | Tags |
|---|---|---|
| 131 | aurangabad | Aurangabad (Bihar) / Chhatrapati Sambhajinagar |
| 95 | pratapgarh | Pratapgarh (Rajasthan) / Pratapgarh (Uttar Pradesh) |
| 79 | maharajganj | Maharajganj (Bihar) / Maharajganj (Uttar Pradesh) |
| 62 | hamirpur | Hamirpur (Himachal Pradesh) / Hamirpur (Uttar Pradesh) |
| 49 | bilaspur | Bilaspur (Chhattisgarh) / Bilaspur (Himachal Pradesh) |
| 44 | dindori | Dindori (Madhya Pradesh) / Dindori (Maharashtra) |
| 18 | bishnupur | Bishnupur (Manipur) / Bishnupur (West Bengal) |
| 7 | bijapur | Bijapur (Chhattisgarh) / Vijayapura |

## Names that equal an existing tag (top 15)

| Items | Name | Tag |
|---|---|---|
| 2358 | tamil nadu | Tamil Nadu |
| 2101 | uttar pradesh | Uttar Pradesh |
| 2038 | bihar | Bihar |
| 1770 | kerala | Kerala |
| 1751 | maharashtra | Maharashtra |
| 1610 | andhra pradesh | Andhra Pradesh |
| 1384 | odisha | Odisha |
| 1354 | rajasthan | Rajasthan |
| 1347 | west bengal | West Bengal |
| 1144 | delhi | Delhi |
| 1002 | jharkhand | Jharkhand |
| 929 | karnataka | Karnataka |
| 873 | gujarat | Gujarat |
| 853 | telangana | Telangana |
| 850 | jammu and kashmir | Jammu & Kashmir |
