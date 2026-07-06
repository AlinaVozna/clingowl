#!/usr/bin/env python3
r"""
Extracts the allergy module from a full SNOMED CT release (OWL Functional
Syntax) and saves it as RDF/XML, producing benchmarks/dlvhex/ontologies/
snomed_allergy.owl. Kept in the repo so the fragment's provenance is
reproducible; the full SNOMED release is licensed and not included.

Method: take all descendants of "Propensity to adverse reaction" (420134006)
in the stated hierarchy with their full axioms; every other referenced
concept is declared as a primitive class. Three case individuals are added
so instance-retrieval queries have non-empty answers (SNOMED itself is
TBox-only). Note the fragment keeps the real role-group definitions, so e.g.
"Allergy to penicillin" (91936005) falls under "Allergic disposition"
(609328004) only through DL classification.

Expected input: a full SNOMED CT release already converted to OWL Functional
Syntax. SNOMED CT's official distribution format is RF2 
(tab-separated Concept/Relationship/Description files), which looks nothing like
this and this script does NOT read directly.
To go from RF2 to OWL Functional Syntax, use the official
snomed-owl-toolkit (https://github.com/IHTSDO/snomed-owl-toolkit) first.

Run inside the clingowl-bench container (it has the OWL API for the format
conversion; RDF/XML cannot express assertions whose property has a numeric
local name, which is also why the synthetic ABox uses class assertions only).

From the clingowl/ directory, with SNOMED.owl being your full SNOMED CT
release (adjust its path):

  PowerShell:
    docker run --rm -v "C:\path\to\SNOMED.owl:/src/SNOMED.owl:ro" -v "${PWD}:/out" clingowl-bench python /out/benchmarks/extract_snomed_fragment.py /src/SNOMED.owl /out/benchmarks/dlvhex/ontologies/snomed_allergy.owl

  Git Bash:
    docker run --rm -v /c/path/to/SNOMED.owl:/src/SNOMED.owl:ro -v $(pwd):/out clingowl-bench python /out/benchmarks/extract_snomed_fragment.py /src/SNOMED.owl /out/benchmarks/dlvhex/ontologies/snomed_allergy.owl

The output always goes to benchmarks/dlvhex/ontologies/snomed_allergy.owl
(gitignored — see benchmarks/README.md). You only need to run this once;
compare.sh reuses the file if it already exists.
"""
import re
import sys
import tempfile
from collections import defaultdict

SEED = "420134006"          # Propensity to adverse reaction
ROOT = "138875005"          # SNOMED CT root concept
NS = "http://snomed.info/id/"

CASES = [("case1", "91936005"),     # allergy to penicillin
         ("case2", "294505008"),    # allergy to amoxicillin
         ("case3", SEED)]


def extract(src, out_ofn):
    axioms = defaultdict(list)
    parents = defaultdict(set)

    simple = re.compile(r"^SubClassOf\(:(\d+) :(\d+)\)")
    normal = re.compile(r"^(?:SubClassOf|EquivalentClasses)\(:(\d+) ObjectIntersectionOf\(((?::\d+ )+)")
    subject = re.compile(r"^(?:SubClassOf|EquivalentClasses)\(:(\d+) ")

    with open(src, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = subject.match(line)
            if not m:
                continue
            sid = m.group(1)
            axioms[sid].append(line.rstrip())
            m1 = simple.match(line)
            if m1:
                parents[sid].add(m1.group(2))
            m2 = normal.match(line)
            if m2:
                parents[sid].update(p[1:] for p in m2.group(2).split())

    children = defaultdict(set)
    for c, ps in parents.items():
        for p in ps:
            children[p].add(c)

    frag, queue = set(), [SEED]
    while queue:
        c = queue.pop()
        if c not in frag:
            frag.add(c)
            queue.extend(children.get(c, ()))

    chain, cur, seen = [], SEED, {SEED}
    while cur != ROOT and parents.get(cur):
        p = sorted(parents[cur])[0]
        if p in seen:
            break
        chain.append((cur, p))
        seen.add(p)
        cur = p

    frag_axioms = [a for c in sorted(frag) for a in axioms[c]]

    prop_ids, all_ids = set(), set()
    for a in frag_axioms:
        all_ids.update(re.findall(r":(\d+)", a))
        prop_ids.update(re.findall(r"ObjectSomeValuesFrom\(:(\d+)", a))
    class_ids = (all_ids - prop_ids) | frag | {p for _, p in chain}

    for _, cls in CASES:
        if cls not in class_ids:
            sys.exit("ABox class :%s not in fragment, pick another" % cls)

    with open(out_ofn, "w", encoding="utf-8") as o:
        o.write("Prefix(:=<%s>)\n" % NS)
        o.write("Prefix(owl:=<http://www.w3.org/2002/07/owl#>)\n\n")
        o.write("Ontology(<http://snomed.info/sct/allergy-fragment>\n\n")
        for c in sorted(class_ids):
            o.write("Declaration(Class(:%s))\n" % c)
        for p in sorted(prop_ids):
            o.write("Declaration(ObjectProperty(:%s))\n" % p)
        o.write("\n")
        for c, p in chain:
            o.write("SubClassOf(:%s :%s)\n" % (c, p))
        for a in frag_axioms:
            o.write(a + "\n")
        o.write("\n")
        for ind, cls in CASES:
            o.write("Declaration(NamedIndividual(:%s))\n" % ind)
            o.write("ClassAssertion(:%s :%s)\n" % (cls, ind))
        o.write(")\n")

    print("fragment concepts: %d, declared classes: %d, properties: %d"
          % (len(frag), len(class_ids), len(prop_ids)))


def convert(ofn, owl):
    """OWL Functional Syntax -> RDF/XML via the OWL API (jpype)."""
    from owlapy.owl_ontology import SyncOntology
    import jpype.imports  # noqa: F401
    onto = SyncOntology(ofn, load=True)
    from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
    from org.semanticweb.owlapi.model import IRI as JIRI
    from java.io import File
    fmt = RDFXMLDocumentFormat()
    fmt.setDefaultPrefix(NS)   # the DL-plugin resolves names against this
    onto.owlapi_manager.saveOntology(onto.owlapi_ontology, fmt,
                                     JIRI.create(File(owl)))
    print("axioms: %d -> %s" % (onto.owlapi_ontology.getAxiomCount(), owl))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: extract_snomed_fragment.py <full_SNOMED.owl> <out.owl>")
    with tempfile.NamedTemporaryFile(suffix=".ofn", delete=False) as tmp:
        pass
    extract(sys.argv[1], tmp.name)
    convert(tmp.name, sys.argv[2])
