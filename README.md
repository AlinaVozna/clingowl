# clingowl


This project combines OWL reasoning and Answer Set Programming (ASP).

It includes:
- a small family ontology created in Python with OWLAPY
- a bridge between OWL and ASP using custom theory atoms
- example ASP programs evaluated with Clingo and Pellet

## Project Structure

- `create_family/`
  contains the Python code used to create the family ontology
- `ast_clingowl.py/`
  contains the translator from custom ASP theory atoms to OWL queries, together with example ASP rules

## Requirements

- Python 3.x
- Java installed
  required to use the Pellet reasoner

Install dependencies with:

```bash
pip install -r requirements.txt
