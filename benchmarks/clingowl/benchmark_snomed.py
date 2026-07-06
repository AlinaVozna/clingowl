#!/usr/bin/env python
"""
ClingOWL benchmark over the real SNOMED CT allergy fragment
(benchmarks/dlvhex/ontologies/snomed_allergy.owl, shared with the DLVHEX
benchmark). Same structure and CSV format as examples/family/
benchmark_family.py; concepts are addressed by SCTID with the id(N) helper,
mirroring the templates of the DLVHEX side.

Standalone on purpose: it does not import the family example, so it can run
with just the fragment ontology (no label index over the full SNOMED).
"""
from __future__ import annotations

import statistics
import time
from pathlib import Path

import clingo
import clingo.ast as cast
from clingo import Function, Number
from clingo.ast import ASTType, Literal, Location, Position, Rule, SymbolicTerm, parse_string
from clingox.ast import TheoryParser, theory_parser_from_definition

from owlapy.class_expression import OWLClass, OWLObjectComplementOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_reasoner import SyncReasoner

BASE_DIR = Path(__file__).resolve().parent
ONTOLOGY_FILE = (BASE_DIR / ".." / "dlvhex" / "ontologies" / "snomed_allergy.owl").resolve()
NAMESPACE = "http://snomed.info/id/"

sync_reasoner = SyncReasoner(ontology=str(ONTOLOGY_FILE), reasoner="Pellet")

loc = Location(Position("", 0, 0), Position("", 0, 0))

# Mirrors the DLVHEX fragment templates: 4 concept retrievals (root, an
# inferred superclass, a negation, a leaf), 3 membership checks and one
# TBox check (subsumption -- ClingOWL's counterpart of &dlConsistent).
QUERY_TEMPLATES = [
    "q{0}(X) :- &owlquery{{ id(420134006) }} = X.",
    "q{0}(X) :- &owlquery{{ id(609328004) }} = X.",
    "q{0}(X) :- &owlquery{{ ~id(420134006) }} = X.",
    "q{0}(X) :- &owlquery{{ id(91936005) }} = X.",
]
BOOL_TEMPLATES = [
    "b{0} :- &owl{{ (case3) :: id(420134006) }}.",
    "b{0} :- &owl{{ (case1) :: id(609328004) }}.",
    "b{0} :- &owl{{ (case1) :: id(91936005) }}.",
    "b{0} :- &owl{{ id(91936005) <: id(609328004) }}.",
]

THEORY = """#theory clingowl {
    formula {
        <: : 0, binary, left;
        =  : 0, binary, left;
        :: : 0, binary, left;
        |  : 1, binary, left;
        &  : 2, binary, left;
        !  : 3, binary, left;
        ?  : 3, binary, left;
        ~  : 4, unary;
        -  : 4, unary
    };
    term { - : 1, unary };
    &owl/0 : formula, body;
    &owlquery/0 : formula, {=}, term, body
}."""


def parse_theory(source):
    parser = None

    def extract(stm):
        nonlocal parser
        if stm.ast_type == ASTType.TheoryDefinition:
            parser = theory_parser_from_definition(stm)

    parse_string(source, extract)
    return parser


class Context:
    """id(N) -> SCTID class; bare names -> individuals (case1, ...)."""

    def bool_symbol(self, value):
        return clingo.Number(1 if value else 0)

    def owlclass(self, expr):
        if expr.name == "id" and len(expr.arguments) == 1:
            return OWLClass(IRI(NAMESPACE, str(expr.arguments[0].number)))
        if expr.name == "negation":
            return OWLObjectComplementOf(self.owlclass(expr.arguments[0]))
        raise ValueError("unsupported class expression: %s" % expr)

    def owlindividual(self, ind):
        return OWLNamedIndividual(IRI(NAMESPACE, ind.name))

    def axiom(self, expr):
        if expr.name == "subset":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(sync_reasoner.is_entailed(OWLSubClassOfAxiom(c, d)))
        if expr.name == "instance":
            individual = self.owlindividual(expr.arguments[0])
            concept = self.owlclass(expr.arguments[1])
            return self.bool_symbol(
                any(ind == individual for ind in sync_reasoner.instances(concept, direct=False)))
        raise ValueError("unsupported boolean expression: %s" % expr)

    def belongsto(self, expr):
        individuals = sync_reasoner.instances(self.owlclass(expr), direct=False)
        return [clingo.Function(ind.iri.as_str().split("/")[-1]) for ind in individuals]


class Translator:
    def __init__(self):
        self.program = []
        self.theory_parser = parse_theory(THEORY)

    def get_translation(self):
        return "\n".join(str(ast) for ast in self.program)

    def translate_term(self, term):
        operators = {"::": "instance", "<:": "subset", "~": "negation"}
        if term.ast_type == cast.ASTType.SymbolicTerm:
            return term.symbol
        if term.ast_type == cast.ASTType.TheorySequence:
            return Function("", [self.translate_term(a) for a in term.terms])
        if term.ast_type == cast.ASTType.TheoryFunction:
            args = [self.translate_term(a) for a in term.arguments]
            return Function(operators.get(term.name, term.name), args)
        return term

    def translate_rule(self, sentence):
        if sentence.ast_type != cast.ASTType.Rule:
            self.program.append(sentence)
            return
        new_body = []
        for literal in sentence.body:
            if (literal.ast_type == cast.ASTType.Literal
                    and literal.atom.ast_type == cast.ASTType.TheoryAtom):
                atom_name = literal.atom.term.name
                root = self.theory_parser(literal.atom).elements[0].terms[0]
                expr_term = SymbolicTerm(loc, self.translate_term(root))
                if atom_name == "owl":
                    call = cast.Function(loc, "axiom", [expr_term], True)
                    guard = cast.Guard(cast.ComparisonOperator.Equal,
                                       SymbolicTerm(loc, Number(1)))
                elif atom_name == "owlquery":
                    call = cast.Function(loc, "belongsto", [expr_term], True)
                    guard = cast.Guard(cast.ComparisonOperator.Equal,
                                       literal.atom.guard.term)
                else:
                    new_body.append(literal)
                    continue
                comparison = cast.Comparison(call, [guard])
                new_body.append(Literal(literal.location, literal.sign, comparison))
            else:
                new_body.append(literal)
        self.program.append(Rule(sentence.location, sentence.head, new_body))


def generate_program(num_atoms):
    lines, counter = [], 1
    templates = QUERY_TEMPLATES + BOOL_TEMPLATES
    while len(lines) < num_atoms:
        for template in templates:
            if len(lines) >= num_atoms:
                break
            lines.append(template.format(counter))
            counter += 1
    return "\n".join(lines) + "\n"


def run_once(program_text):
    start_total = time.perf_counter()

    asts = []
    start_parse = time.perf_counter()
    parse_string(program_text, lambda ast: asts.append(ast))
    end_parse = time.perf_counter()

    translator = Translator()
    start_translate = time.perf_counter()
    for ast in asts:
        translator.translate_rule(ast)
    translated = translator.get_translation()
    end_translate = time.perf_counter()

    ctl = clingo.Control()
    ctl.add("base", [], translated)
    start_reasoning = time.perf_counter()
    ctl.ground([("base", [])], context=Context())
    with ctl.solve(yield_=True) as handle:
        for _model in handle:
            pass
    end_reasoning = time.perf_counter()

    end_total = time.perf_counter()
    return {
        "parsing": end_parse - start_parse,
        "translation": end_translate - start_translate,
        "reasoning": end_reasoning - start_reasoning,
        "total": end_total - start_total,
    }


def main():
    sizes = [10, 50, 100, 500]
    repeats = 10

    print("Warming up...\n")
    run_once(generate_program(10))

    results = {}
    for size in sizes:
        print("Benchmarking %d theory atoms..." % size)
        program_text = generate_program(size)
        samples = [run_once(program_text) for _ in range(repeats)]
        results[size] = {
            key: {
                "mean": statistics.mean(s[key] for s in samples) * 1000,
                "stdev": (statistics.stdev(s[key] for s in samples) * 1000)
                         if len(samples) > 1 else 0.0,
            }
            for key in ("parsing", "translation", "reasoning", "total")
        }

    print()
    print("theory_atoms,parsing_mean_ms,parsing_stdev_ms,translation_mean_ms,"
          "translation_stdev_ms,reasoning_mean_ms,reasoning_stdev_ms,"
          "total_mean_ms,total_stdev_ms")
    for size, m in results.items():
        print("%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % (
            size,
            m["parsing"]["mean"], m["parsing"]["stdev"],
            m["translation"]["mean"], m["translation"]["stdev"],
            m["reasoning"]["mean"], m["reasoning"]["stdev"],
            m["total"]["mean"], m["total"]["stdev"]))


if __name__ == "__main__":
    main()
