# clingowl


This repository contains the prototype accompanying our paper on the integration of **Answer Set Programming (ASP)** with **OWL reasoning**.

The project provides two runnable examples:

- a **family ontology** example
- a **SNOMED CT-inspired** example

The framework allows ASP programs to use custom theory atoms such as:

- `&owl{...}` for Boolean ontology checks
- `&owlquery{...} = X` for ontology queries returning individuals

These expressions are translated into OWL queries and evaluated through **OWLAPY** and a DL reasoner.

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
```

### Option B: install OWLAPY from source
```bash
git clone https://github.com/dice-group/owlapy
cd owlapy

conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
pip install -e '.[dev]'
```
### Additional Dependencies
Inside the environment, install the dependencies required by this repository:
``` bash
pip install clingo==5.8.0 clingox==1.2.1 owlready2==0.50 jpype1==1.7.0 rdflib==7.6.0
```
---
### Run the Family Example
Before running the example, make sure you are inside the OWLAPY environment:

```bash
conda activate temp_owlapy
```

Then move to the family example directory:

```bash
cd examples/family
```

Run the ClingOWL family example:

```bash
python clingowl_family.py 
```


This script:

- loads the family ontology;
- parses the ASP file `family.lp`;
- translates theory atoms such as `&owl{...}` and `&owlquery{...} = X`;
- evaluates the corresponding OWL queries through OWLAPY and the configured reasoner;
- returns the results to Clingo;
- prints the resulting answer set.

### Expected Output

The expected output of the Family example is available in

```text
examples/family/expected_output.txt
```

After running

```bash
cd examples/family
python clingowl_family.py family.lp
```

the produced output should match the contents of `expected_output.txt`.

  ---
  ## Supported DL-style Operators

The current version of **ClingOWL** supports the following Description Logic (DL) operators and OWL axioms.

| Operator | Description | DL Semantics | Example |
|----------|-------------|--------------|---------|
| `A <: B` | Subclass axiom | A ⊑ B | `father <: person` |
| `A = B` | Equivalent classes | A ≡ B | `parent = person & (hasChild ! person)` |
| `(a)::C` | Class assertion | a : C | `(peter)::father` |
| `(a,b)::R` | Object property assertion | R(a,b) | `(susan,peter)::hasChild` |
| `C & D` | Class intersection | C ⊓ D | `adult & father` |
| `C \| D` | Class union | C ⊔ D | `father \| mother` |
| `~C` | Class complement | ¬C | `~female` |
| `R ! C` | Existential restriction | ∃R.C | `hasChild ! male` |
| `R ? C` | Universal restriction | ∀R.C | `hasChild ? person` |
| `-R` | Inverse object property | R⁻¹ | `-hasParent` |
| `thing` | Universal class | ⊤ | `thing` |
| `nothing` | Empty class | ⊥ | `nothing` |
| `{a}` | Nominal (singleton) | {a} | `{peter}` |
| `{a,b,c}` | Enumeration of individuals | {a,b,c} | `{peter,mary,john}` |

