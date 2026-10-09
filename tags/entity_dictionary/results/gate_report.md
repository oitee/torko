# Entity lookup gate report

The dictionary has 5040 entities. K is the cap of added entities per speech.

## (a) Precision and recall proxies on 3764 speeches that 'gemini-3.8-flash' extracted

The lookup ran with an empty "already has" set. The dictionary was built from the same speeches, so the proxies are optimistic.

| K | names looked up | of them also extracted by the model (precision proxy) | model names in the dictionary | of them found (recall proxy) | speeches with such a name |
|---|---|---|---|---|---|
| 8 | 21453 | 6802 (31.7% of 21453) | 13132 | 6802 (51.8% of 13132) | 2730 of 3764 |
| no cap | 56608 | 10230 (18.1% of 56608) | 13132 | 10230 (77.9% of 13132) | 2730 of 3764 |

## (b) Added entities per speech, 2000 random speeches of 45687 that lite models extracted (seed 1)

The "already has" set is every item name (topics and other entities) of the speech.

K = 8. Denominator: 2000 speeches.

| statistic | value |
|---|---|
| mean | 4.35 |
| median | 4.0 |
| 90th percentile | 8 |
| 99th percentile | 8 |
| maximum | 8 |
| speeches with 0 added | 163 (8.2%) |
| speeches at the cap of 8 | 575 (28.8%) |

K = no cap. Denominator: 2000 speeches.

| statistic | value |
|---|---|
| mean | 6.30 |
| median | 4.0 |
| 90th percentile | 15 |
| 99th percentile | 34 |
| maximum | 53 |
| speeches with 0 added | 163 (8.2%) |
