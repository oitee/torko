# Review pairs

Each row is a possible duplicate or risk. Fill the column `review` in `review_pairs.tsv`. This file is a short view. The first 15 rows of each kind are here.

## existing_exact (13 rows)

| place | state | other tag | other type | detail |
|---|---|---|---|---|
| Andaman and Nicobar Islands | Andaman and Nicobar Islands | Andaman & N Islands | place union_territory | equals the alias of an existing tag. No new tag. |
| Chandigarh | Chandigarh | Chandigarh | place union_territory | equals the name of an existing tag. No new tag. |
| Daman and Diu | Dadra and Nagar Haveli and Daman and Diu | Daman & Diu | place union_territory | equals the alias of an existing tag. No new tag. |
| Kutch | Gujarat | Kachchh Region | place region | equals the alias of an existing tag. No new tag. |
| Ranchi | Jharkhand | Ranchi | place city | equals the name of an existing tag. No new tag. |
| Thiruvananthapuram | Kerala | Thiruvananthapuram | place city | equals the name of an existing tag. No new tag. |
| Kargil | Ladakh | Kargil | place region | equals the name of an existing tag. No new tag. |
| Ladakh | Ladakh | Ladakh | place union_territory | equals the name of an existing tag. No new tag. |
| Lakshadweep | Lakshadweep | Lakshadweep | place union_territory | equals the name of an existing tag. No new tag. |
| Mizoram | Mizoram | Mizoram | place state | equals the name of an existing tag. No new tag. |
| Nagaland | Nagaland | Nagaland | place state | equals the name of an existing tag. No new tag. |
| Puducherry | Puducherry | Pondicherry | place union_territory | equals the alias of an existing tag. No new tag. |
| Sikkim | Sikkim | Sikkim | place state | equals the name of an existing tag. No new tag. |

## existing_near (1 rows)

| place | state | other tag | other type | detail |
|---|---|---|---|---|
| Una | Himachal Pradesh | United Nations (UN) | institution  | the spelling key of 'Una' equals the key of 'UN' |

## shared_name (14 rows)

| place | state | other tag | other type | detail |
|---|---|---|---|---|
| Aurangabad (Bihar) | Bihar | Chhatrapati Sambhajinagar (Maharashtra, old name) | place  | bare name 'Aurangabad' is an alias of every tag in the group. The decision model decides. |
| Maharajganj (Bihar) | Bihar | Maharajganj (Uttar Pradesh) | place  | bare name 'Maharajganj' is an alias of every tag in the group. The decision model decides. |
| Bijapur (Chhattisgarh) | Chhattisgarh | Vijayapura (Karnataka, old name) | place  | bare name 'Bijapur' is an alias of every tag in the group. The decision model decides. |
| Bilaspur (Chhattisgarh) | Chhattisgarh | Bilaspur (Himachal Pradesh) | place  | bare name 'Bilaspur' is an alias of every tag in the group. The decision model decides. |
| Bilaspur (Himachal Pradesh) | Himachal Pradesh | Bilaspur (Chhattisgarh) | place  | bare name 'Bilaspur' is an alias of every tag in the group. The decision model decides. |
| Hamirpur (Himachal Pradesh) | Himachal Pradesh | Hamirpur (Uttar Pradesh) | place  | bare name 'Hamirpur' is an alias of every tag in the group. The decision model decides. |
| Dindori (Madhya Pradesh) | Madhya Pradesh | Dindori (Maharashtra) | place  | bare name 'Dindori' is an alias of every tag in the group. The decision model decides. |
| Dindori (Maharashtra) | Maharashtra | Dindori (Madhya Pradesh) | place  | bare name 'Dindori' is an alias of every tag in the group. The decision model decides. |
| Bishnupur (Manipur) | Manipur | Bishnupur (West Bengal) | place  | bare name 'Bishnupur' is an alias of every tag in the group. The decision model decides. |
| Pratapgarh (Rajasthan) | Rajasthan | Pratapgarh (Uttar Pradesh) | place  | bare name 'Pratapgarh' is an alias of every tag in the group. The decision model decides. |
| Hamirpur (Uttar Pradesh) | Uttar Pradesh | Hamirpur (Himachal Pradesh) | place  | bare name 'Hamirpur' is an alias of every tag in the group. The decision model decides. |
| Maharajganj (Uttar Pradesh) | Uttar Pradesh | Maharajganj (Bihar) | place  | bare name 'Maharajganj' is an alias of every tag in the group. The decision model decides. |
| Pratapgarh (Uttar Pradesh) | Uttar Pradesh | Pratapgarh (Rajasthan) | place  | bare name 'Pratapgarh' is an alias of every tag in the group. The decision model decides. |
| Bishnupur (West Bengal) | West Bengal | Bishnupur (Manipur) | place  | bare name 'Bishnupur' is an alias of every tag in the group. The decision model decides. |

## common_word (31 rows)

| place | state | other tag | other type | detail |
|---|---|---|---|---|
| Krishna | Andhra Pradesh |  | person  | method entity_name: 1 speech items use this name with type person |
| Polavaram | Andhra Pradesh |  | scheme  | method entity_name: 1 speech items use this name with type scheme |
| Arrah | Bihar |  |   | method english_word: the name is an English word in the system word list |
| Daman | Dadra and Nagar Haveli and Daman and Diu |  |   | method english_word: the name is an English word in the system word list |
| Dang | Gujarat |  |   | method english_word: the name is an English word in the system word list |
| Surat | Gujarat |  |   | method english_word: the name is an English word in the system word list |
| Panipat | Haryana |  | law  | method entity_name: 1 speech items use this name with type law |
| Mandi | Himachal Pradesh |  |   | method hand_list: Hindi and Urdu: a market |
| Solan | Himachal Pradesh |  |   | method english_word: the name is an English word in the system word list |
| Samba | Jammu and Kashmir |  |   | method english_word: the name is an English word in the system word list |
| Bidar | Karnataka |  |   | method english_word: the name is an English word in the system word list |
| Sham | Ladakh |  |   | method english_word: the name is an English word in the system word list |
| Balaghat | Madhya Pradesh |  |   | method english_word: the name is an English word in the system word list |
| Dhar | Madhya Pradesh |  |   | method hand_list: Hindi: a flow or a ridge |
| Guna | Madhya Pradesh |  |   | method english_word: the name is an English word in the system word list |

## rename (28 rows)

| place | state | other tag | other type | detail |
|---|---|---|---|---|
| Sribhumi | Assam | Karimganj |   | alias 'Karimganj' is the old name of this place |
| Gurugram | Haryana | Gurgaon |   | alias 'Gurgaon' is the old name of this place |
| Nuh | Haryana | Mewat |   | alias 'Mewat' is the old name of this place |
| Ballari | Karnataka | Bellary |   | alias 'Bellary' is the old name of this place |
| Belagavi | Karnataka | Belgaum |   | alias 'Belgaum' is the old name of this place |
| Bengaluru Rural | Karnataka | Bangalore Rural |   | alias 'Bangalore Rural' is the old name of this place |
| Bengaluru Urban | Karnataka | Bangalore Urban |   | alias 'Bangalore Urban' is the old name of this place |
| Chikkamagaluru | Karnataka | Chikmagalur |   | alias 'Chikmagalur' is the old name of this place |
| Kalaburagi | Karnataka | Gulbarga |   | alias 'Gulbarga' is the old name of this place |
| Mysuru | Karnataka | Mysore |   | alias 'Mysore' is the old name of this place |
| Shivamogga | Karnataka | Shimoga |   | alias 'Shimoga' is the old name of this place |
| Tumakuru | Karnataka | Tumkur |   | alias 'Tumkur' is the old name of this place |
| Vijayapura | Karnataka | Bijapur |   | alias 'Bijapur' is the old name of this place |
| Narmadapuram | Madhya Pradesh | Hoshangabad |   | alias 'Hoshangabad' is the old name of this place |
| Ahilyanagar | Maharashtra | Ahmednagar |   | alias 'Ahmednagar' is the old name of this place |

## new_near (0 rows)

No rows.
