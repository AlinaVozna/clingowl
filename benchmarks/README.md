# Benchmarks

Containerized benchmarks for comparing ClingOWL against DLVHEX on the same
machine, both systems isolated in Docker.

```bash
# from the repository root: builds both images and prints each system's CSV
# plus a combined table (total wall-clock time per run)
sh benchmarks/compare.sh family
```

- `clingowl/` — container for the ClingOWL benchmark (`examples/family/benchmark_family.py`)
- `dlvhex/` — container for DLVHEX 2.5.0 + DL-Plugin + Racer, with an
  equivalent benchmark (see its README for scope and known limitations)

Measurement note: both benchmarks exclude reasoner start-up (ClingOWL creates
its reasoner once outside the timer; the Racer server is started before
timing). ClingOWL times are measured in-process, while each DLVHEX run
includes the `dlvhex2` process start — keep that in mind for small sizes.
