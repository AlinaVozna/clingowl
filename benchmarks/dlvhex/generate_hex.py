#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generates the HEX programs for the DLVHEX benchmark, mirroring
examples/family/benchmark_family.py: programs with N DL atoms
(N = 10/50/100/500) built by cycling a fixed set of templates.

Usage: python generate_hex.py <family|snomed> <output_dir> [ontology.owl]
"""
import os
import sys

ONTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ontologies")

# classes: concepts queried with &dlC (leading "-" = negation)
# roles:   roles queried with &dlR
# inst:    (concept, individual) membership checks
# pairs:   (role, ind, ind) relation checks
ONTOLOGIES = {
    "family": {
        "file":    "my_family.owl",
        "ns":      "http://example.com/my_family#",
        "classes": ["parent", "mother", "-female", "grandfather"],
        "roles":   ["hasChild"],
        "inst":    [("father", "peter"), ("mother", "mary"), ("person", "diego")],
        "pairs":   [("hasChild", "susan", "peter")],
    },
    # Allergy module extracted from the full SNOMED CT release (see
    # ../extract_snomed_fragment.py). SCTIDs: 420134006 = Propensity to
    # adverse reaction (module root), 609328004 = Allergic disposition
    # (an INFERRED superclass: answering requires DL classification over
    # SNOMED's role-group definitions), 91936005 = Allergy to penicillin.
    # case1..case3 are the synthetic individuals added by the extractor.
    "snomed": {
        "file":    "snomed_allergy.owl",
        "ns":      "http://snomed.info/id/",
        "classes": ["420134006", "609328004", "-420134006", "91936005"],
        "roles":   [],
        "inst":    [("420134006", "case3"),
                    ("609328004", "case1"),
                    ("91936005", "case1")],
        "pairs":   [],
    },
}

SIZES = [10, 50, 100, 500]


def build_templates(cfg):
    onto = '"%s", pc, mc, pr, mr' % cfg["owl"]   # pc/mc/pr/mr: no ABox additions
    iri = lambda name: '"<%s%s>"' % (cfg["ns"], name)

    templates = []
    for c in cfg["classes"]:
        templates.append('q{0}(X) :- &dlC[%s, "%s"](X).' % (onto, c))
    for r in cfg["roles"]:
        templates.append('q{0}(X,Y) :- &dlR[%s, "%s"](X,Y).' % (onto, r))
    for c, ind in cfg["inst"]:
        templates.append('b{0}(X) :- &dlC[%s, "%s"](X), X == %s.' % (onto, c, iri(ind)))
    templates.append('b{0} :- &dlConsistent[%s]().' % onto)
    for r, a, b in cfg["pairs"]:
        templates.append('b{0}(X,Y) :- &dlR[%s, "%s"](X,Y), X == %s, Y == %s.'
                         % (onto, r, iri(a), iri(b)))
    return templates


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python generate_hex.py <family|snomed> <output_dir> [ontology.owl]")

    name, outdir = sys.argv[1], sys.argv[2]
    if name not in ONTOLOGIES:
        sys.exit("Unknown ontology: %s (options: %s)" % (name, ", ".join(ONTOLOGIES)))

    cfg = dict(ONTOLOGIES[name])
    cfg["owl"] = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ONTO_DIR, cfg["file"])

    templates = build_templates(cfg)
    for size in SIZES:
        lines, counter = [], 1
        while len(lines) < size:
            for tpl in templates:
                if len(lines) >= size:
                    break
                lines.append(tpl.format(counter))
                counter += 1
        path = "%s/bench_%s_%d.hex" % (outdir, name, size)
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("wrote %s (%d dl-atoms)" % (path, size))


if __name__ == "__main__":
    main()
