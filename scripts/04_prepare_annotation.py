"""Phase 4: draw the critiques to annotate and write the files of the annotators.

    uv run python scripts/04_prepare_annotation.py

Writes in data/annotation/:
- to_annotate_<annotator>.csv: the same critiques for every annotator, in a different
  order, with their context and empty label columns. No label of the LLM.
- sample_key.parquet: critique, labels of the LLM and sampling weight of each item.
  Not to be opened by the annotators.
and results/tables/annotation_sample_strata.csv (population and sample per stratum).

The sample is drawn once and frozen in the file named by `annotation.sample_file`.
A file that already holds annotations is never overwritten.
"""

import sys

import pandas as pd

from src.eval import annotation
from src.llm import inputs, steps
from src.utils.config import REPO_ROOT, load_config
from src.utils.runlog import setup_run_logging


def excluded_reviews(cfg) -> set[str]:
    """Reviews the sample never draws from: prompt examples and tuning samples."""
    excluded = inputs.prompt_example_ids(cfg["paths"]["prompts"])
    for name in cfg["annotation"]["excluded_samples"]:
        excluded |= set(inputs.read_sample(inputs.sample_path(cfg, name)))
    return excluded


def main() -> int:
    cfg = load_config()
    settings = cfg["annotation"]
    log = setup_run_logging("04_prepare_annotation", cfg["paths"]["logs"])

    critiques = pd.read_parquet(cfg["paths"]["llm"] / settings["run"] / "critiques.parquet")
    excluded = excluded_reviews(cfg)
    pool = annotation.population(critiques, excluded)
    log.info("run=%s critiques=%d excluded_reviews=%d population=%d",
             settings["run"], len(critiques), len(excluded), len(pool))

    sample_file = REPO_ROOT / settings["sample_file"]
    if sample_file.exists():
        ids = annotation.read_sample_file(sample_file)
        log.info("frozen sample read from %s (%d critiques)", sample_file, len(ids))
    else:
        ids = annotation.draw_sample(pool, settings["size"], settings["stratum_floor"], settings["seed"])
        annotation.write_sample_file(sample_file, ids, [
            f"Annotation sample: {len(ids)} critique ids of run {settings['run']}, in the order of the items",
            f"(item_001 is the first line). Stratified by year x aspect x severity given by the LLM, at least",
            f"{settings['stratum_floor']} critiques per stratum, seed {settings['seed']}. Reviews used as prompt examples",
            f"or in the samples {settings['excluded_samples']} are excluded. Frozen: never drawn again.",
        ])
        log.info("sample drawn and frozen in %s (%d critiques)", sample_file, len(ids))
    if len(ids) != settings["size"]:
        raise SystemExit(f"{sample_file} holds {len(ids)} critiques, the config asks for {settings['size']}")

    key = annotation.sample_key(pool, ids)
    reviews = inputs.usable_reviews(cfg)
    reviews = reviews[reviews["review_id"].isin(set(key["review_id"]))]
    max_chars = cfg["llm"]["max_input_chars"]
    units = {r["review_id"]: steps.review_units(r, max_chars)[0] for r in reviews.to_dict("records")}
    table = annotation.annotation_table(key, units, settings["context_units"])

    out_dir = cfg["paths"]["annotation"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(settings["annotators"]):
        path = out_dir / f"to_annotate_{name}.csv"
        order = annotation.annotator_order(len(table), settings["seed"], index)
        if annotation.write_annotator_file(path, table.iloc[order]):
            log.info("written: %s (%d items)", path, len(table))
        else:
            log.warning("kept as it is, it already holds annotations: %s", path)

    key.to_parquet(out_dir / "sample_key.parquet", index=False)
    (out_dir / "sample_key.stats.md").write_text("\n".join([
        "# sample_key.parquet", "",
        f"{len(key)} items of the annotation sample (run `{settings['run']}`), one row per item: critique,",
        "labels given by the LLM (`llm_*`) and sampling weight. Not to be opened by the annotators.", "",
        f"- reviews: {key['review_id'].nunique()}; papers: {key['forum_id'].nunique()}",
        "- items per year: " + ", ".join(f"{year}: {n}" for year, n in key["year"].value_counts().sort_index().items()),
        f"- critique length in characters: median {int(key['text'].str.len().median())}, "
        f"max {int(key['text'].str.len().max())}",
        "- strata: `results/tables/annotation_sample_strata.csv`", "",
    ]), encoding="utf-8")

    sampled = key.rename(columns={"llm_aspect": "aspect", "llm_severity": "severity"}) \
                 .groupby(list(annotation.STRATA)).size()
    strata = annotation.strata_table(pool, sampled)
    cfg["paths"]["tables"].mkdir(parents=True, exist_ok=True)
    strata.to_csv(cfg["paths"]["tables"] / "annotation_sample_strata.csv", index=False)
    log.info("strata=%d (with at least one critique drawn: %d) population=%d sampled=%d",
             len(strata), int((strata["sampled"] > 0).sum()), int(strata["population"].sum()),
             int(strata["sampled"].sum()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
