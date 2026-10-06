# ClingOWL

This repository contains the prototype accompanying our paper on the integration of **Answer Set Programming (ASP)** with **OWL reasoning**.

The project provides two runnable examples:

- a **family ontology** example;
- a **SNOMED CT-inspired** example.

The framework allows ASP programs to use custom theory atoms:

- `&owlassert{...}` for adding OWL axioms before ASP reasoning (family example, v0.2);
- `&owl{...}` for Boolean ontology checks;
- `&owlquery{...} = X` for ontology queries returning individuals.

Ontology checks and queries are evaluated through **OWLAPY** and a DL reasoner. In the v0.2 family example, ontology assertions are applied first, and subsequent queries use the extended ontology.

---

## What's New in v0.2

The family example now supports `&owlassert{...}` facts in a dedicated `#program ontology.` section.

Supported additions include:

- class assertions;
- object property assertions;
- subclass axioms;
- equivalent-class axioms.

The assertions are collected and applied before the ASP base program is grounded and solved. The extended ontology is saved to a temporary file, and the reasoner is reinitialized on that file. The original ontology file is not overwritten.

Assertions must be ground facts without an ASP rule body. They are applied once before ASP reasoning, rather than being derived from individual answer sets.

The ASP program is organized into two sections:

- `#program ontology.` contains ontology assertion facts;
- `#program base.` contains ordinary ASP rules and ontology queries.

This addition is implemented in `examples/family/clingowl_family.py`. The SNOMED CT-inspired example remains a separate query example.

---

## Requirements

To run the code, you need:

- Python 3.11;
- Java installed;
- Conda recommended.

Java is required by the **Pellet** reasoner.

---

## Environment Setup

Run the installation commands in your Python 3.11 environment.

If you use Conda, create and activate the environment first:

```bash
conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
```

Then install **OWLAPY** using one of the following options.

### Option A: Install from PyPI

```bash
pip3 install owlapy
```

### Option B: Install OWLAPY from Source

```bash
git clone https://github.com/dice-group/owlapy
cd owlapy
pip install -e '.[dev]'
```

### Additional Dependencies

Inside the environment, install the dependencies required by this repository:

```bash
pip install clingo==5.8.0 clingox==1.2.1 owlready2==0.50 jpype1==1.7.0 rdflib==7.6.0
```

---

## Run the Family Example

Activate the environment where you installed the dependencies.

If you used the Conda setup above:

```bash
conda activate temp_owlapy
```

From the root of this **ClingOWL repository**, move to the family example directory:

```bash
cd examples/family
```

### Example with Assertions (v0.2)

Run the default example:

```bash
python clingowl_family.py
```

This is equivalent to:

```bash
python clingowl_family.py family_withassertion.lp
```

The script:

- loads `ontologies/my_family.owl`;
- parses `family_withassertion.lp`;
- collects the `&owlassert{...}` facts from `#program ontology.`;
- applies the axioms and saves the extended ontology to a temporary file;
- evaluates `&owl{...}` and `&owlquery{...} = X` against the extended ontology during grounding;
- solves the ASP base program with Clingo;
- prints the resulting answer set.

### Assertion Example

The supplied example includes:

```asp
#program ontology.

% Add a class assertion.
&owlassert{ john :: father }.

% Add an object property assertion.
&owlassert{ (john,ann) :: hasChild }.

#program base.

% Check the newly added assertions.
assertion_applied :- &owl{ john :: father }.
john_has_child_ann :- &owl{ (john,ann) :: hasChild }.

% Query the extended ontology.
parent(X) :- &owlquery{ adult & (father | mother) } = X.
```

The first section adds two axioms. The second section checks and queries the extended ontology.

### Original Example without Assertions

From the same directory, run:

```bash
python clingowl_family.py family.lp
```

An alternative ASP input file can be supplied as the first command-line argument.

### Output Reference

The original family example output is documented in:

```text
examples/family/expected_output.txt
```

This file refers to `family.lp`, not to the new `family_withassertion.lp` example.

It is a reference for the original results rather than an exact console-output snapshot for v0.2: the updated script prints additional assertion information, and output formatting or atom order may differ.

For `family_withassertion.lp`, the program includes the checks `assertion_applied` and `john_has_child_ann` for the two added axioms.

---

## Supported DL-style Operators

ClingOWL supports the following Description Logic (DL) operators and OWL axioms.

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

---

## Benchmarks

The `benchmarks/` folder contains a containerized comparison against DLVHEX
(engine + DL-Plugin + Racer reasoner), on the family ontology and on a real
SNOMED CT allergy fragment.

See `benchmarks/README.md` for details.

From the repository root:

```bash
sh benchmarks/compare.sh family
sh benchmarks/compare.sh snomed
```
