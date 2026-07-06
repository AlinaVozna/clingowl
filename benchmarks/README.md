# Benchmarks

Containerized benchmarks for comparing ClingOWL against DLVHEX on the same
machine, both systems isolated in Docker.

```bash
# from the repository root: builds both images and prints each system's CSV
# plus a combined table (total wall-clock time per run)
sh benchmarks/compare.sh family
sh benchmarks/compare.sh snomed   # real SNOMED CT allergy fragment
```

- `clingowl/` — container for the ClingOWL benchmarks
  (`examples/family/benchmark_family.py` and `clingowl/benchmark_snomed.py`)
- `dlvhex/` — container for DLVHEX 2.5.0 + DL-Plugin + Racer, with
  equivalent benchmarks (see its README for scope and known limitations)
- `extract_snomed_fragment.py` — produces the SNOMED allergy fragment from a
  full SNOMED CT release

SNOMED CT content is licensed (free for member countries), so neither the
full release nor the extracted fragment is committed to the repo. Before
running the `snomed` benchmark, generate the fragment once — the script's
docstring has the exact command; it writes
`dlvhex/ontologies/snomed_allergy.owl`, which is gitignored.

Measurement note: both benchmarks exclude reasoner start-up (ClingOWL creates
its reasoner once outside the timer; the Racer server is started before
timing). ClingOWL times are measured in-process, while each DLVHEX run
includes the `dlvhex2` process start — keep that in mind for small sizes.
