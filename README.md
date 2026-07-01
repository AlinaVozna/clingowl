# clingowl

# ASP–OWL Integration with OWLAPY, Clingo, and SNOMED

This repository contains the prototype accompanying our paper on the integration of **Answer Set Programming (ASP)** with **OWL reasoning**.

The project provides two runnable examples:

- a **family ontology** example
- a **SNOMED CT-inspired** example

The framework allows ASP programs to use custom theory atoms such as:

- `&owl{...}` for Boolean ontology checks
- `&owlquery{...} = X` for ontology queries returning individuals

These expressions are translated into OWL queries and evaluated through **OWLAPY** and a DL reasoner.

---

## Repository Structure

examples/
- family/
  - `clingowl_family.py`
  - `family.lp`

- snomed/
  - `clingowl_snomed.py`
  - `snomed.lp`

ontologies/
- `my_family.owl`
- `snomed.owl`

---

## Requirements

To run the code, you need:

- Python 3.11
- Java installed
- Conda recommended

Java is required by the **Pellet** reasoner.

---

## Environment Setup

First install **OWLAPY**.

### Option A: install from PyPI

```bash
pip3 install owlapy
---

### Option B: install OWLAPY from source
```bash
git clone https://github.com/dice-group/owlapy
cd owlapy

conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
pip install -e '.[dev]'
---
