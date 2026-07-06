# DLVHEX benchmark

Docker environment for [DLVHEX](https://github.com/hexhex/core) 2.5.0
(engine + DL-Plugin + Racer reasoner), used to run a benchmark comparable to
the ClingOWL one in `examples/family/benchmark_family.py`.

DLVHEX dates from 2014-2016 and no longer builds on current systems, so the
Dockerfile pins period-correct versions (Ubuntu 16.04, GCC 4.8, Boost 1.55).
No sources of DLVHEX, the plugin or Racer are patched; each workaround is
explained where it happens in the Dockerfile.

## Usage

```bash
docker build -t dlvhex250 .

docker run --rm dlvhex250 bench family
docker run --rm dlvhex250 bench snomed 20   # 20 repetitions
```

Output is a CSV with the mean/stdev wall-clock time per `dlvhex2` run for
programs of 10/50/100/500 DL atoms, e.g.:

```
theory_atoms,total_mean_ms,total_stdev_ms,failures
10,85.8,6.3,0
50,94.3,2.9,0
100,110.9,6.9,0
500,337.6,27.3,0
```

`ontologies/` contains frozen copies of the two benchmark ontologies. The
family one is a normalized copy of `../../ontologies/my_family.owl` (names
lowercased — DLVHEX constants must start lowercase — and the default
namespace aligned with the entity IRIs; pure renaming, same DL semantics).
The SNOMED CT allergy extract is used as-is. To add an ontology: drop the
OWL file in `ontologies/`, add a block to `ONTOLOGIES` in `generate_hex.py`,
rebuild.

## Scope and known limitations

- The benchmark scales the *number of DL atoms* on a small fixed ontology,
  i.e. it measures per-query overhead, not reasoning over large ontologies
  (that is a separate experiment).
- The DL-Plugin implements dl-programs (Eiter et al.): atomic concepts
  (optionally negated, `-c`) and roles. Composed OWL class expressions are
  not accepted in queries — they must exist as named classes in the TBox, so
  the benchmark uses `parent`, `grandfather`, ... where ClingOWL uses
  composed expressions. Subsumption checks (`father <: person` in ClingOWL)
  have no dl-atom counterpart; consistency checks are used instead.
- The plugin's conjunctive-query atoms (`&dlCQ*`) and ground membership
  calls crash against the 2.5.0 engine, so membership checks are written as
  retrieval plus an ASP join.
- The plugin speaks Racer's nRQL protocol over TCP and cannot use OWL-API
  reasoners (Pellet, HermiT). Commercial RacerPro being unavailable, the
  image builds the open-source successor (github.com/ha-mo-we/Racer, BSD-3).
- DLVHEX and ClingOWL numbers are only comparable when measured on the same
  machine, and the systems still differ in reasoner and architecture — treat
  results as a first experimental comparison.
