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
== Building images (cached after the first time) ==
sha256:e60eae57d6a0c8566d458af0fd48b74bc8ebacdd9ff72291f82b90666cfea6a2
sha256:2374c4544e77d66a23a1a6df2a4a40f591cb765c3c52db8d41785cdd5d27a52a

== ClingOWL (snomed) ==
theory_atoms,parsing_mean_ms,parsing_stdev_ms,translation_mean_ms,translation_stdev_ms,reasoning_mean_ms,reasoning_stdev_ms,total_mean_ms,total_stdev_ms
10,0.363,0.450,5.100,0.523,24.859,3.068,31.268,3.837
50,0.884,0.212,25.818,1.717,102.140,10.869,130.063,10.842
100,1.803,0.386,56.261,16.598,188.952,15.955,248.691,19.373
500,9.178,1.456,261.784,31.621,854.754,29.140,1131.073,45.039

== DLVHEX (snomed) ==
(this takes ~10-15 min: DLVHEX re-classifies the ontology on every run,
 which is precisely the finding; output appears when all runs finish)
theory_atoms,total_mean_ms,total_stdev_ms,failures
10,15515.8,1111.8,0
50,16509.1,991.5,0
100,16307.1,1090.8,0
500,16273.5,1101.6,0

== Combined (total wall-clock time per run, ms) ==
theory_atoms,clingowl_mean_ms,clingowl_stdev_ms,dlvhex_mean_ms,dlvhex_stdev_ms
10,31.268,3.837,15515.8,1111.8
50,130.063,10.842,16509.1,991.5
100,248.691,19.373,16307.1,1090.8
500,1131.073,45.039,16273.5,1101.6

== ClingOWL (family) ==
[main] INFO org.semanticweb.owlapi.rdf.rdfxml.parser.OWLRDFConsumer - Unparsed triple: http://www.w3.org/1999/02/22-rdf-syntax-ns#type -> http://example.com/my_family#Ann -> _:genid2147483675
[main] INFO org.semanticweb.owlapi.rdf.rdfxml.parser.OWLRDFConsumer - Unparsed triple: http://www.w3.org/1999/02/22-rdf-syntax-ns#type -> http://example.com/my_family#Susan -> _:genid2147483674
theory_atoms,parsing_mean_ms,parsing_stdev_ms,translation_mean_ms,translation_stdev_ms,reasoning_mean_ms,reasoning_stdev_ms,total_mean_ms,total_stdev_ms
10,0.256,0.063,6.566,1.032,26.648,2.878,34.323,3.038
50,0.839,0.073,30.386,2.695,107.181,20.464,139.654,21.360
100,1.625,0.119,72.056,35.956,192.872,26.607,268.502,44.147
500,9.604,2.995,331.536,30.151,896.165,55.280,1243.463,77.655

== DLVHEX (family) ==
theory_atoms,total_mean_ms,total_stdev_ms,failures
10,194.6,62.8,0
50,172.4,13.0,0
100,212.4,17.5,0
500,487.3,47.1,0

== Combined (total wall-clock time per run, ms) ==
theory_atoms,clingowl_mean_ms,clingowl_stdev_ms,dlvhex_mean_ms,dlvhex_stdev_ms
10,34.323,3.038,194.6,62.8
50,139.654,21.360,172.4,13.0
100,268.502,44.147,212.4,17.5
500,1243.463,77.655,487.3,47.1



```

`ontologies/` contains the two benchmark ontologies. The family one is a
normalized copy of `../../ontologies/my_family.owl` (names lowercased —
DLVHEX constants must start lowercase — and the default namespace aligned
with the entity IRIs; pure renaming, same DL semantics). `snomed_allergy.owl`
is the allergy module of the real SNOMED CT International release (1,424
concepts with their full role-group definitions), generated locally with
`../extract_snomed_fragment.py` — SNOMED content is licensed, so this file
is gitignored rather than committed. Three case individuals are added there
so retrieval queries have answers (SNOMED itself is TBox-only). Notably,
`bench snomed` queries include an *inferred* superclass (609328004), so the
answers require actual DL classification. To add an ontology: drop the OWL
file in `ontologies/`, add a block to `ONTOLOGIES` in `generate_hex.py`,
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
