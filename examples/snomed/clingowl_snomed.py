# =============================================================================
# ClingOWL - SNOMED CT example
# -----------------------------------------------------------------------------
# This version of ClingOWL is adapted to work with a SNOMED-like OWL ontology.
# Unlike the family example, where class names are mapped directly to ontology
# IRIs, this script builds an index from labels and synonyms to SNOMED concept IDs.
#
# Example:
#
#   bacterial_pneumonia
#
# is resolved to the corresponding SNOMED identifier and then converted into:
#
#   http://snomed.info/id/<SNOMED_ID>
#
# This allows ASP rules to use readable names while OWLAPY and Pellet reason over
# the actual SNOMED-style IRIs.
# =============================================================================


from pathlib import Path
import re

import clingo
import clingo.ast as cast
from clingo import Function, Number
from clingo.ast import ASTType, Literal, Location, Position, Rule, SymbolicTerm, parse_string
from rdflib import Graph, URIRef
from rdflib.namespace import RDFS, SKOS

from owlapy.class_expression import (
    OWLClass,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectHasSelf,
    OWLObjectIntersectionOf,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
    OWLNothing,
    OWLThing,
)
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner
from clingox.ast import TheoryParser, theory_parser_from_definition
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent

ONTOLOGY_FILE = BASE_DIR / "ontologies" / "snomed.owl"
ASP_FILE = BASE_DIR / "snomed.lp"

onto = Ontology(
    IRI.create(f"file://{ONTOLOGY_FILE.resolve().as_posix()}"),
    load=True,
)

namespace = "http://snomed.info/id/"
sync_reasoner = SyncReasoner(
    ontology=str(ONTOLOGY_FILE.resolve()),
    reasoner="Pellet",
)

OWL_QUERY_ATOM = "owlquery"
OWL_BOOL_ATOM = "owl"


def normalize_term(text: str) -> str:
    """
    Normalize labels so that SNOMED terms can be used safely inside ASP rules.

    Example:
        "Bacterial pneumonia (disorder)"
        -> "bacterial_pneumonia_disorder"
    """
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def build_snomed_index(path: Path) -> dict[str, str]:
    """
    Build a mapping between human-readable labels and SNOMED identifiers.

    The function parses the OWL/RDF ontology and extracts labels and synonyms
    from common annotation properties such as rdfs:label, skos:prefLabel,
    skos:altLabel, and OBO synonym properties.

    The resulting dictionary is used to translate ASP-level names into
    SNOMED concept/property identifiers.
    """
    graph = Graph()
    graph.parse(path)

    label_to_id: dict[str, str] = {}
    synonym_preds = [
        RDFS.label,
        SKOS.prefLabel,
        SKOS.altLabel,
        URIRef("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"),
        URIRef("http://www.geneontology.org/formats/oboInOwl#hasRelatedSynonym"),
    ]

    for subj, _, _ in graph:
        subj_str = str(subj)
        if not subj_str.startswith(namespace):
            continue

        snomed_id = subj_str.removeprefix(namespace)
        for pred in synonym_preds:
            for _, _, label in graph.triples((subj, pred, None)):
                key = normalize_term(str(label))
                if key and key not in label_to_id:
                    label_to_id[key] = snomed_id

    return label_to_id

# Build the label-to-ID index used to resolve ASP terms into SNOMED IRIs.
entity_map = build_snomed_index(ONTOLOGY_FILE)

loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)


def parse_theory(source: str) -> TheoryParser:
    parser = None

    def extract(statement):
        nonlocal parser
        if statement.ast_type == ASTType.TheoryDefinition:
            parser = theory_parser_from_definition(statement)

    parse_string(source, extract)
    return parser


class Context:
    """
    Clingo grounding context for SNOMED-aware OWL reasoning.

    This class provides callback functions used during grounding.
    It converts internal symbolic expressions into OWLAPY objects and
    delegates reasoning tasks to Pellet.

    Compared to the family ontology example, this context resolves
    concept, property, and individual names through the SNOMED label index.
    """
    def bool_symbol(self, value):
        return clingo.Number(1 if value else 0)

    def owlproperty(self, prop):
        """
        Convert an internal role expression into an OWL object property.

        Supported forms:
            - readable labels, resolved through the SNOMED index;
            - id(NUMBER), used to refer directly to a SNOMED identifier;
            - inverse(R), used for inverse object properties.
        """
        if prop.name == "inverse":
            return OWLObjectInverseOf(self.owlproperty(prop.arguments[0]))

        if prop.name == "id" and len(prop.arguments) == 1:
            property_id = str(prop.arguments[0].number)
        else:
            property_id = entity_map.get(normalize_term(prop.name))
            if property_id is None:
                raise ValueError(f"Unknown SNOMED property: {prop.name}")

        return OWLObjectProperty(IRI(namespace, property_id))

    def owlindividual(self, ind):
        """
        Convert an ASP individual symbol into an OWL named individual.

        Individuals can be written either as readable labels or directly as
        id(NUMBER), depending on the ontology encoding.
        """
        if ind.name == "id" and len(ind.arguments) == 1:
            return OWLNamedIndividual(IRI(namespace, str(ind.arguments[0].number)))

        individual_id = entity_map.get(normalize_term(ind.name))
        if individual_id is None:
            raise ValueError(f"Unknown SNOMED individual: {ind.name}")
        return OWLNamedIndividual(IRI(namespace, individual_id))

    def owlclass(self, expr):
        """
        Recursively convert an internal symbolic expression into an OWLAPY
        class expression using SNOMED-style IRIs.

        Supported constructors include:
            - atomic SNOMED concepts;
            - id(NUMBER) for direct SNOMED identifiers;
            - intersection, union, negation;
            - existential and universal restrictions;
            - nominals;
            - OWL Thing and OWL Nothing;
            - self restrictions.
        """
        if expr.name == "id" and len(expr.arguments) == 1:
            return OWLClass(IRI(namespace, str(expr.arguments[0].number)))

        if expr.name == "":
            return OWLObjectOneOf([self.owlindividual(arg) for arg in expr.arguments])

        if len(expr.arguments) == 0:
            if expr.name == "nothing":
                return OWLNothing
            if expr.name == "thing":
                return OWLThing

            concept_id = entity_map.get(normalize_term(expr.name))
            if concept_id is None:
                raise ValueError(f"Unknown SNOMED concept: {expr.name}")
            return OWLClass(IRI(namespace, concept_id))

        if expr.name == "intersection":
            return OWLObjectIntersectionOf([self.owlclass(arg) for arg in expr.arguments])

        if expr.name == "union":
            return OWLObjectUnionOf([self.owlclass(arg) for arg in expr.arguments])

        if expr.name == "negation":
            return OWLObjectComplementOf(self.owlclass(expr.arguments[0]))

        if expr.name == "exist":
            role = self.owlproperty(expr.arguments[0])
            filler = expr.arguments[1]
            if filler.name == "self" and len(filler.arguments) == 0:
                return OWLObjectHasSelf(role)
            return OWLObjectSomeValuesFrom(role, self.owlclass(filler))

        if expr.name == "forall":
            return OWLObjectAllValuesFrom(
                self.owlproperty(expr.arguments[0]),
                self.owlclass(expr.arguments[1]),
            )

        raise ValueError(f"Unsupported SNOMED class expression: {expr}")

    def axiom(self, expr):
        """
        Evaluate Boolean ontology statements over the SNOMED ontology.

        Supported checks:
            - subclass entailment;
            - class equivalence;
            - class assertion;
            - object property assertion.

        Returns:
            clingo.Number(1) if the statement is entailed;
            clingo.Number(0) otherwise.
        """
        if expr.name == "subset":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(sync_reasoner.is_entailed(OWLSubClassOfAxiom(c, d)))

        if expr.name == "equivalent":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(any(eq == c for eq in sync_reasoner.equivalent_classes(d)))

        if expr.name == "instance":
            arg1 = expr.arguments[0]
            arg2 = expr.arguments[1]

            if len(arg1.arguments) == 0 or arg1.name == "id":
                individual = self.owlindividual(arg1)
                concept = self.owlclass(arg2)
                return self.bool_symbol(any(ind == individual for ind in sync_reasoner.instances(concept, direct=False)))

            if len(arg1.arguments) == 2:
                left = self.owlindividual(arg1.arguments[0])
                right = self.owlindividual(arg1.arguments[1])
                role = self.owlproperty(arg2)
                return self.bool_symbol(any(val == right for val in sync_reasoner.object_property_values(left, role)))

            raise ValueError("instance expects 1 subject or a pair of 2 subjects")

        raise ValueError(f"Unsupported SNOMED boolean expression: {expr}")

    def belongsto(self, expr):
        
        owl_expr = self.owlclass(expr)
        individuals = sync_reasoner.instances(owl_expr, direct=False)
        result = []
        for ind in individuals:
            identifier = ind.iri.as_str().split("/")[-1]
            result.append(clingo.Function(identifier))
        return result


class MyTranslator:
    clingowl_theory = """#theory clingowl {
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
        term {
            - : 1, unary
        };
        &owl/0 : formula, body;
        &owlquery/0 : formula, {=}, term, body
    }."""

    def __init__(self):
        self.program = []
        self.theory_parser = parse_theory(self.clingowl_theory)

    def get_translation(self):
        return "\n".join(str(ast) for ast in self.program)

    def translate_term(self, term):
        operators = {
            "::": "instance",
            "<:": "subset",
            "=": "equivalent",
            "&": "intersection",
            "|": "union",
            "~": "negation",
            "?": "forall",
            "!": "exist",
            "-": "inverse",
        }

        if term.ast_type == cast.ASTType.SymbolicTerm:
            return term.symbol

        if term.ast_type == cast.ASTType.TheorySequence:
            return Function("", [self.translate_term(arg) for arg in term.terms])

        if term.ast_type == cast.ASTType.TheoryFunction:
            args = [self.translate_term(arg) for arg in term.arguments]
            if term.name in operators:
                return Function(operators[term.name], args)
            return Function(term.name, args)

        return term

    def translate_rule(self, sentence: cast.AST):
        new_body = []

        if sentence.ast_type == cast.ASTType.Rule:
            for literal in sentence.body:
                if literal.ast_type == cast.ASTType.Literal and literal.atom.ast_type == cast.ASTType.TheoryAtom:
                    atom_name = literal.atom.term.name
                    parsed_theory_atom = self.theory_parser(literal.atom)
                    root = parsed_theory_atom.elements[0].terms[0]
                    translated_expr = self.translate_term(root)
                    expr_term = SymbolicTerm(loc, translated_expr)

                    if atom_name == OWL_BOOL_ATOM:
                        bool_term = SymbolicTerm(loc, Number(1))
                        axiom_call = cast.Function(loc, "axiom", [expr_term], True)
                        comparison = cast.Comparison(
                            axiom_call,
                            [cast.Guard(cast.ComparisonOperator.Equal, bool_term)],
                        )
                        new_body.append(Literal(literal.location, literal.sign, comparison))

                    elif atom_name == OWL_QUERY_ATOM:
                        if literal.atom.guard is None:
                            raise ValueError("&owlquery must be used with = Variable")

                        guard_op = literal.atom.guard.operator_name
                        guard_term = literal.atom.guard.term
                        if guard_op != "=":
                            raise ValueError("&owlquery only supports '=' guards")
                        if guard_term.ast_type != cast.ASTType.Variable:
                            raise ValueError("&owlquery guard must be a variable")

                        belongsto_call = cast.Function(loc, "belongsto", [expr_term], True)
                        comparison = cast.Comparison(
                            belongsto_call,
                            [cast.Guard(cast.ComparisonOperator.Equal, guard_term)],
                        )
                        new_body.append(Literal(literal.location, literal.sign, comparison))
                    else:
                        new_body.append(literal)
                else:
                    new_body.append(literal)

            self.program.append(Rule(sentence.location, sentence.head, new_body))
        else:
            self.program.append(sentence)

 #Read the ASP program containing SNOMED-oriented OWL theory atoms.
with open(ASP_FILE, "r") as file_handle:
    program = file_handle.read()

# Translate OWL theory atoms into Clingo callback functions.
translator = MyTranslator()
parse_string(program, lambda ast: translator.translate_rule(ast))

translated_program = translator.get_translation()
# Uncomment the following lines to inspect the translated ASP program.
# This is useful for understanding how SNOMED-oriented OWL theory atoms
# are rewritten into executable Clingo callback functions.
#
# print("===== Translated Program =====")
# print(translated_program)

# Ground and solve the translated ASP program.
# During grounding, Clingo calls the Context methods whenever it encounters
# @axiom(...) or @belongsto(...), which in turn query the OWL reasoner.
ctl = clingo.Control()
ctl.add("base", [], translated_program)
ctl.ground([("base", [])], context=Context())
ctl.configuration.solve.models = "2"
nummodels = 0

print("===== Reasoning =====")
with ctl.solve(yield_=True) as handle:
    for model in handle:
        if nummodels > 0:
            print("Warning: more than 1 model")
            break
        for atom in model.symbols(atoms=True):
            print(atom, end=" ")
        print()
        nummodels = 1
if nummodels == 0:
    print("UNSATISFIABLE")

