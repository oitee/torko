# Place tags build report (2026-10-09)

Source rows: 788 districts, 543 constituencies.

New tags: 951. By subtype: constituency 166, district 416, district_constituency 365, former_constituency 4.
Skipped places (an existing tag has the name or an alias): 13.
Tags with the state in the name (shared names): 14.
Aliases from renames.tsv in use: 28.
Unused rename rows (new name not in the source): 0.
Pairs merged by same_place.tsv: 8.
Aliases added by extra_aliases.tsv: 59.
Former constituency tags (old_seats.tsv): 4.

Review rows by kind: common_word 31, existing_exact 13, existing_near 1, rename 28, shared_name 14.

## Self checks

- All checks passed.

## Warnings about the source

- Nagaland: the overview table states 17 districts, the state table has 16
- West Bengal: the overview table states 27 districts, the state table has 23
- Delhi: the overview table states 13 districts, the state table has 11
- total: the overview table states 800 districts, the state tables have 788
- skipped a second constituency table for Assam (14 rows, first row Karimganj)

## Merged pairs (same_place.tsv)

- Gujarat: Kutch (kept) and Kachchh are one place
- Tamil Nadu: Kanchipuram (kept) and Kancheepuram are one place
- Tamil Nadu: Thoothukudi (kept) and Thoothukkudi are one place
- Tamil Nadu: Viluppuram (kept) and Villupuram are one place
- Uttar Pradesh: Kushinagar (kept) and Kushi Nagar are one place
- Uttar Pradesh: Raebareli (kept) and Rae Bareli are one place
- Uttar Pradesh: Shravasti (kept) and Shrawasti are one place
- Karnataka: Chikkaballapur (kept) and Chikballapur are one place

## Seats of the old constituency table (old_seats.tsv)

- Assam: Karimganj -> same
- Assam: Silchar -> same
- Assam: Autonomous District -> former Autonomous District (Assam)
- Assam: Dhubri -> same
- Assam: Kokrajhar -> same
- Assam: Barpeta -> same
- Assam: Gauhati -> alias Guwahati
- Assam: Mangaldoi -> former
- Assam: Tezpur -> former
- Assam: Nowgong -> ignore
- Assam: Kaliabor -> former
- Assam: Jorhat -> same
- Assam: Dilbrugarh -> ignore
- Assam: Lakhimpur -> same

## Counts for each state (new tags)

| State | district | constituency | district_constituency |
|---|---|---|---|
| Andaman and Nicobar Islands | 3 | 0 | 0 |
| Andhra Pradesh | 15 | 12 | 13 |
| Arunachal Pradesh | 27 | 2 | 0 |
| Assam | 26 | 5 | 9 |
| Bihar | 11 | 13 | 27 |
| Chhattisgarh | 23 | 1 | 10 |
| Dadra and Nagar Haveli and Daman and Diu | 2 | 0 | 1 |
| Delhi | 5 | 1 | 6 |
| Goa | 1 | 0 | 2 |
| Gujarat | 12 | 4 | 21 |
| Haryana | 14 | 1 | 9 |
| Himachal Pradesh | 8 | 0 | 4 |
| Jammu and Kashmir | 16 | 1 | 4 |
| Jharkhand | 14 | 4 | 9 |
| Karnataka | 8 | 5 | 23 |
| Kerala | 0 | 6 | 13 |
| Ladakh | 6 | 0 | 0 |
| Madhya Pradesh | 27 | 1 | 28 |
| Maharashtra | 9 | 21 | 27 |
| Manipur | 16 | 2 | 0 |
| Meghalaya | 12 | 2 | 0 |
| Mizoram | 11 | 0 | 0 |
| Nagaland | 16 | 0 | 0 |
| Odisha | 14 | 5 | 16 |
| Puducherry | 3 | 0 | 0 |
| Punjab | 12 | 2 | 11 |
| Rajasthan | 21 | 5 | 20 |
| Sikkim | 6 | 0 | 0 |
| Tamil Nadu | 9 | 10 | 29 |
| Telangana | 22 | 6 | 11 |
| Tripura | 8 | 2 | 0 |
| Uttar Pradesh | 16 | 21 | 59 |
| Uttarakhand | 10 | 2 | 3 |
| West Bengal | 13 | 32 | 10 |

## Sources

- Districts: https://en.wikipedia.org/wiki/List_of_districts_in_India (fallback, see tags/places/README.md)
- Constituencies: https://en.wikipedia.org/wiki/List_of_constituencies_of_the_Lok_Sabha (fallback, see tags/places/README.md)
