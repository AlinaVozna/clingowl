# clingowl

ClingOWL is a prototype system that extends `clingo` with OWL theory atoms, allowing ASP programs to query OWL ontologies through external Description Logic reasoners.

The system is built on top of:

- `clingo`
- `clingox`
- `OWLAPY`
- Pellet
- RDFLib, only for the SNOMED example

---

## 1. Set up the OWLAPY environment
Before running ClingOWL, install OWLAPY and create the Python environment following the official OWLAPY installation instructions.

### Option A — Install OWLAPY from PyPI

```bash
pip3 install owlapy

### Option B — Install OWLAPY from source
```bash

git clone https://github.com/dice-group/owlapy
cd owlapy

conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy

pip install -e '.[dev]'

All ClingOWL files should be executed inside this environment.
