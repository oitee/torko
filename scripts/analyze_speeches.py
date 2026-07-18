"""
Corpus-wide speech/turn/keyword analysis. Emits ONE JSON blob consumed by the
standalone analysis dashboard (internal_docs + static/analysis.html).

Every number is computed over the whole population (no sampling -- the corpus is
a vicious heavy tail and a 200-row sample describes a corpus that does not
exist, per internal_docs/023). Where a number is counted over a subset, the key
name says so (e.g. person_owned, tagged_debates).

Run: source .venv/bin/activate && python3 scripts/analyze_speeches.py > fixtures/analysis.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine


def scalar(c, q, **kw):
    return c.execute(text(q), kw).scalar()


def rows(c, q, **kw):
    return [dict(r._mapping) for r in c.execute(text(q), kw)]


def num(x):
    """Postgres Decimal/float -> plain float/int for JSON."""
    if x is None:
        return None
    f = float(x)
    return int(f) if f.is_integer() else round(f, 2)


def main():
    e = get_engine()
    out = {}
    with e.connect() as c:
        # ---- Overview ----
        out["overview"] = {
            "debates_total": scalar(c, "select count(*) from debates"),
            "debates_with_turns": scalar(c, "select count(distinct debate_id) from turns"),
            "debates_with_speeches": scalar(c, "select count(distinct debate_id) from speeches"),
            "turns_total": scalar(c, "select count(*) from turns"),
            "speeches_total": scalar(c, "select count(*) from speeches"),
            "speeches_person": scalar(c, "select count(*) from speeches where person_id is not null"),
            "speeches_unresolved": scalar(c, "select count(*) from speeches where person_id is null"),
            "words_total": num(scalar(c, "select sum(word_count) from speeches")),
            "distinct_speakers": scalar(c, "select count(distinct person_id) from speeches where person_id is not null"),
        }

        # ---- Speech size distribution ----
        def dist(where):
            r = c.execute(text(f"""
                select count(*) n, avg(word_count) mean, stddev(word_count) sd,
                  percentile_cont(0.25) within group (order by word_count) p25,
                  percentile_cont(0.5)  within group (order by word_count) median,
                  percentile_cont(0.75) within group (order by word_count) p75,
                  percentile_cont(0.9)  within group (order by word_count) p90,
                  percentile_cont(0.99) within group (order by word_count) p99,
                  min(word_count) mn, max(word_count) mx
                from speeches {where}""")).fetchone()
            return {k: num(v) for k, v in r._mapping.items()}

        out["size"] = {
            "all": dist(""),
            "person_owned": dist("where person_id is not null"),
        }
        out["size"]["mode"] = rows(c, """
            select word_count, count(*) n from speeches
            group by word_count order by n desc limit 6""")
        for m in out["size"]["mode"]:
            m["n"] = int(m["n"])

        # log-ish histogram buckets
        out["size"]["histogram"] = rows(c, """
            with b as (select case
                when word_count <= 50 then '0-50'
                when word_count <= 100 then '51-100'
                when word_count <= 250 then '101-250'
                when word_count <= 500 then '251-500'
                when word_count <= 1000 then '501-1000'
                when word_count <= 2500 then '1001-2500'
                when word_count <= 5000 then '2501-5000'
                else '5000+' end bucket,
              case
                when word_count <= 50 then 0 when word_count <= 100 then 1
                when word_count <= 250 then 2 when word_count <= 500 then 3
                when word_count <= 1000 then 4 when word_count <= 2500 then 5
                when word_count <= 5000 then 6 else 7 end ord
              from speeches)
            select bucket, ord, count(*) n from b group by bucket, ord order by ord""")
        for h in out["size"]["histogram"]:
            h["n"] = int(h["n"])
            h.pop("ord", None)

        # ---- Skew: Lorenz-style share of words by speech-size percentile ----
        r = c.execute(text("""
            with s as (select word_count, ntile(100) over (order by word_count) pct from speeches),
                 tot as (select sum(word_count)::numeric t from speeches)
            select
              100*sum(word_count) filter (where pct=100)/(select t from tot) top1,
              100*sum(word_count) filter (where pct>=96)/(select t from tot) top5,
              100*sum(word_count) filter (where pct>=91)/(select t from tot) top10,
              100*sum(word_count) filter (where pct<=50)/(select t from tot) bottom50
            from s""")).fetchone()
        out["skew"] = {k: num(v) for k, v in r._mapping.items()}

        # ---- Per-term ----
        out["by_term"] = rows(c, """
            select d.loksabha, count(s.*) speeches,
              avg(s.word_count) mean, percentile_cont(0.5) within group (order by s.word_count) median,
              max(s.word_count) mx, sum(s.word_count) words
            from speeches s join debates d on d.id=s.debate_id
            group by d.loksabha order by d.loksabha""")
        for t in out["by_term"]:
            for k in ("mean", "median", "mx", "words"):
                t[k] = num(t[k])
            t["speeches"] = int(t["speeches"])

        # ---- Speaker-wise ----
        out["speakers"] = {}
        out["speakers"]["per_speaker_dist"] = {k: num(v) for k, v in c.execute(text("""
            with s as (select person_id, count(*) n from speeches where person_id is not null group by person_id)
            select avg(n) mean, percentile_cont(0.5) within group (order by n) median,
              percentile_cont(0.9) within group (order by n) p90, max(n) mx from s""")).fetchone()._mapping.items()}
        # party/constituency are a LAST-TERM snapshot on speakers (one row per
        # person) -- see internal_docs risk on party history. Shown as context,
        # NOT as party-at-time-of-speech.
        out["speakers"]["top_by_speeches"] = rows(c, """
            select p.name, sp2.party, count(*) speeches, sum(sp.word_count) words,
              percentile_cont(0.5) within group (order by sp.word_count) median_len
            from speeches sp join persons p on p.id=sp.person_id
            left join speakers sp2 on sp2.person_id=p.id
            group by p.id, p.name, sp2.party order by speeches desc limit 25""")
        out["speakers"]["top_by_words"] = rows(c, """
            select p.name, sp2.party, count(*) speeches, sum(sp.word_count) words,
              avg(sp.word_count) mean_len
            from speeches sp join persons p on p.id=sp.person_id
            left join speakers sp2 on sp2.person_id=p.id
            group by p.id, p.name, sp2.party order by words desc limit 25""")
        for grp in ("top_by_speeches", "top_by_words"):
            for s in out["speakers"][grp]:
                for k in ("words", "median_len", "mean_len"):
                    if k in s:
                        s[k] = num(s[k])
                s["speeches"] = int(s["speeches"])

        # ---- Large debates: participation scaling + the core group ----
        out["large"] = {}
        out["large"]["participation"] = rows(c, """
            with dw as (select debate_id, sum(word_count) w,
                          count(distinct person_id) filter (where person_id is not null) spk
                        from speeches group by debate_id)
            select case when w<=1000 then '0-1k' when w<=5000 then '1-5k'
                        when w<=20000 then '5-20k' when w<=50000 then '20-50k'
                        else '50k+' end bucket,
                   min(w) ord, count(*) debates, avg(spk) avg_speakers, max(spk) max_speakers
            from dw group by 1 order by min(w)""")
        for p in out["large"]["participation"]:
            p["debates"] = int(p["debates"]); p["avg_speakers"] = num(p["avg_speakers"])
            p["max_speakers"] = int(p["max_speakers"]); p.pop("ord", None)
        # the recurring core across the 500 largest debates
        out["large"]["top_n"] = 500
        out["large"]["core_speakers"] = rows(c, """
            with big as (select debate_id from speeches group by debate_id
                         order by sum(word_count) desc limit 500)
            select p.name, count(distinct s.debate_id) in_debates, sum(s.word_count) words
            from speeches s join persons p on p.id=s.person_id
            where s.debate_id in (select debate_id from big)
            group by p.id, p.name order by in_debates desc limit 25""")
        for s in out["large"]["core_speakers"]:
            s["in_debates"] = int(s["in_debates"]); s["words"] = num(s["words"])
        # concentration: share of person-speeches in the 500 largest that come
        # from the 20 most-recurrent speakers
        out["large"]["concentration"] = {k: num(v) for k, v in c.execute(text("""
            with big as (select debate_id from speeches group by debate_id
                         order by sum(word_count) desc limit 500),
                 sp as (select person_id, count(*) n from speeches
                        where debate_id in (select debate_id from big) and person_id is not null
                        group by person_id),
                 tot as (select sum(n) t, count(*) speakers from sp),
                 top20 as (select sum(n) t20 from (select n from sp order by n desc limit 20) x)
            select (select speakers from tot) distinct_speakers,
                   (select t from tot) person_speeches,
                   100.0*(select t20 from top20)/(select t from tot) top20_share
            """)).fetchone()._mapping.items()}

        # ---- Keyword layer ----
        out["keywords"] = {}
        out["keywords"]["coverage"] = {
            "debates_total": out["overview"]["debates_total"],
            "tagged": scalar(c, "select count(*) from debates where coalesce(array_length(keywords,1),0)>0"),
            "distinct_tags": scalar(c, "select count(distinct k) from debates, unnest(keywords) k"),
            "avg_tags_per_tagged": num(scalar(c, "select avg(array_length(keywords,1)) from debates where coalesce(array_length(keywords,1),0)>0")),
        }
        out["keywords"]["by_term"] = rows(c, """
            select loksabha, count(*) tot,
              count(*) filter (where coalesce(array_length(keywords,1),0)>0) tagged
            from debates group by loksabha order by loksabha""")
        for t in out["keywords"]["by_term"]:
            t["tot"] = int(t["tot"]); t["tagged"] = int(t["tagged"])
            t["pct"] = round(100 * t["tagged"] / t["tot"], 1)
        out["keywords"]["by_type"] = rows(c, """
            select debate_type, count(*) n,
              round(100.0*avg((coalesce(array_length(keywords,1),0)>0)::int), 1) pct
            from debates group by debate_type order by n desc limit 15""")
        for t in out["keywords"]["by_type"]:
            t["n"] = int(t["n"]); t["pct"] = num(t["pct"])
        out["keywords"]["top_tags"] = rows(c, """
            select k tag, count(*) n from debates, unnest(keywords) k
            group by k order by n desc limit 40""")
        for t in out["keywords"]["top_tags"]:
            t["n"] = int(t["n"])
        # frequency shape
        out["keywords"]["freq_shape"] = rows(c, """
            with f as (select k, count(*) n from debates, unnest(keywords) k group by k)
            select case when n=1 then '1' when n<=5 then '2-5' when n<=20 then '6-20'
                   when n<=100 then '21-100' else '100+' end bucket,
                   min(n) mn, count(*) tags, sum(n) uses
            from f group by 1 order by min(n)""")
        for t in out["keywords"]["freq_shape"]:
            t["tags"] = int(t["tags"]); t["uses"] = int(t["uses"]); t.pop("mn", None)

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
