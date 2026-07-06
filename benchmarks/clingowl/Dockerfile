# ClingOWL benchmark container. Same idea as ../dlvhex: self-contained image
# so both systems run isolated on the same machine.
#
# Build from the repository root (the context must include examples/ and
# ontologies/):
#   docker build -f benchmarks/clingowl/Dockerfile -t clingowl-bench .
# Run:
#   docker run --rm clingowl-bench
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Java is required by the Pellet reasoner (used through owlapy/jpype);
# git is needed to install the pinned owlapy commit.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ontologies/ ontologies/
COPY examples/ examples/
# SNOMED fragment benchmark (the ontology is shared with the DLVHEX side)
COPY benchmarks/clingowl/benchmark_snomed.py benchmarks/clingowl/
COPY benchmarks/dlvhex/ontologies/snomed_allergy.owl benchmarks/dlvhex/ontologies/

# Warm import: starts the JVM and loads Pellet once at build time, so the
# image fails fast if the reasoner stack is broken (and any lazy downloads
# happen now, not at benchmark time).
RUN cd examples/family && \
    python -c "import benchmark_family as b; b.load_components()" && \
    echo "reasoner stack OK"

WORKDIR /app/examples/family
CMD ["python", "benchmark_family.py"]
