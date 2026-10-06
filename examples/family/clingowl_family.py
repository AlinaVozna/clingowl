# =============================================================================
# ClingOWL
# -----------------------------------------------------------------------------
# This prototype extends Clingo with OWL theory atoms, enabling Answer Set
# Programming (ASP) programs to directly query OWL ontologies through external
# Description Logic reasoners.
#
# Main components:
#   - Clingo AST parser
#   - Theory atom translator
#   - OWLAPY interface
#   - Pellet reasoner
#
# Supported theory atoms:
#
#   &owlassert{...}
#       Add an OWL axiom to a temporary ontology copy. Assertions are written
#       as facts in #program ontology and are applied before ASP reasoning.
#
#   &owl{...}
#       Boolean ontology entailment checks.
#
#   &owlquery{...} = X
#       Retrieve ontology individuals satisfying a DL expression.
#
# Program parts:
#   #program ontology.  Contains &owlassert facts.
#   #program base.      Contains ordinary ASP rules with &owl and &owlquery.
# =============================================================================

import clingo
import sys
import tempfile
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty, OWLObjectInverseOf
from owlapy.class_expression import  OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectUnionOf, OWLObjectComplementOf, OWLNothing, OWLObjectAllValuesFrom, OWLThing, OWLObjectOneOf
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import  SyncReasoner
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLEquivalentClassesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLSubClassOfAxiom,
)
from clingo import Function, Number
from clingo.ast import ASTType, parse_string
import clingo.ast as cast
from clingo.ast import (
    Location,
    Position,
    Literal,
    Rule,
    SymbolicAtom,
    SymbolicTerm,
)
from clingox.ast import (
    TheoryParser,
    theory_parser_from_definition,
)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


ONTOLOGY_FILE = BASE_DIR.parent.parent / "ontologies" / "my_family.owl"

DEFAULT_ASP_FILE = BASE_DIR / "family_withassertion.lp"
ASP_FILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_ASP_FILE

namespace = "http://example.com/my_family#"

loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)

OWL_QUERY_ATOM = "owlquery"
OWL_BOOL_ATOM = "owl"
OWL_ASSERT_ATOM = "owlassert"

def parse_theory(s: str) -> TheoryParser:
    parser = None
    def extract(stm):
        nonlocal parser
        if stm.ast_type == ASTType.TheoryDefinition:
            parser = theory_parser_from_definition(stm)
    parse_string(s, extract)
    return parser

class OntologyContext:
    """
    Shared interface between the AST translators, the ontology, and Clingo.

    This class provides all callback functions that are invoked
    by Clingo whenever an OWL theory atom must be evaluated.

    Main responsibilities:
        - Convert symbolic expressions into OWLAPY objects.
        - Query the Description Logic reasoner.
        - Return Boolean values or ontology individuals to Clingo.
    """
    def __init__(self, ontology_file: Path, ontology_namespace: str, reasoner_name: str = "Pellet"):
        self.namespace = ontology_namespace
        self.reasoner_name = reasoner_name
        self.ontology_file = ontology_file
        self.active_ontology_file = ontology_file
        self.ontology = Ontology(
            IRI.create(f"file://{ontology_file.resolve()}"),
            load=True,
        )
        self.reasoner = SyncReasoner(str(self.active_ontology_file), reasoner=reasoner_name)

    def refresh_reasoner(self):
        """Recreate the reasoner after mutable ontology assertions are added."""
        self.reasoner = SyncReasoner(str(self.active_ontology_file), reasoner=self.reasoner_name)

    def bool_symbol(self, value):
        return clingo.Number(1 if value else 0)
   
    def upper_first(self, name):
      return name[:1].upper() + name[1:] if name else name

    def opp(self,a):
        if a.name=='f' and len(a.arguments)==2:
           b=a.arguments
           if b[1].name=='n':
              b[1]=clingo.Function("p")
           elif b[1].name=='p':
              b[1]=clingo.Function("n")
           return clingo.Function("f",b)
        else:
           return a
        
    def range(self,a,b):
        if a.type!=clingo.SymbolType.Number or b.type!=clingo.SymbolType.Number:
            return []
        l=[]
        for x in range(a.number, b.number):
            l.append(clingo.Number(x))
        return l
  
    def owlproperty (self, prop):
        if prop.name == "inverse":
            return OWLObjectInverseOf(self.owlproperty(prop.arguments[0]))
        property_name = prop.name
        return OWLObjectProperty(IRI(self.namespace, property_name))
   
    def owlindividual(self, ind):
        individual_name = self.upper_first(ind.name)
        return OWLNamedIndividual(IRI(self.namespace, individual_name))

     
    def owlclass(self, expr): 
        """
        Recursively converts an internal symbolic expression into
        the corresponding OWLAPY class expression.

        Supported constructors:
            intersection
            union
            negation
            existential restriction
            universal restriction
            nominals
            Thing / Nothing
        """
        if expr.name == "":
            return OWLObjectOneOf([self.owlindividual(arg) for arg in expr.arguments])
        
        if len(expr.arguments)== 0: 
            #nothing
            if expr.name== "nothing":
                return OWLNothing
            if expr.name == "thing":
                return OWLThing

            class_name = self.upper_first(expr.name)
            return OWLClass(IRI(self.namespace, class_name))

        if expr.name == "intersection":
            return OWLObjectIntersectionOf([self.owlclass(arg) for arg in expr.arguments])

        if expr.name == "union":
            return OWLObjectUnionOf([self.owlclass(arg) for arg in expr.arguments])

        if expr.name == "negation":
            return OWLObjectComplementOf(self.owlclass(expr.arguments[0]))
      
        if expr.name == "exist":
            return OWLObjectSomeValuesFrom(
            self.owlproperty(expr.arguments[0]),
            self.owlclass(expr.arguments[1])
        )

        if expr.name == "forall":
            return OWLObjectAllValuesFrom(
            self.owlproperty(expr.arguments[0]),
            self.owlclass(expr.arguments[1])
        )

    def build_axiom(self, expr):
        """Convert an internal symbolic expression into a mutable OWL axiom."""
        if expr.name == "subset":
            return OWLSubClassOfAxiom(
                self.owlclass(expr.arguments[0]),
                self.owlclass(expr.arguments[1]),
            )

        if expr.name == "equivalent":
            return OWLEquivalentClassesAxiom([
                self.owlclass(expr.arguments[0]),
                self.owlclass(expr.arguments[1]),
            ])

        if expr.name == "instance":
            subject, predicate = expr.arguments
            if len(subject.arguments) == 0:
                return OWLClassAssertionAxiom(
                    self.owlindividual(subject),
                    self.owlclass(predicate),
                )
            if len(subject.arguments) == 2:
                return OWLObjectPropertyAssertionAxiom(
                    self.owlindividual(subject.arguments[0]),
                    self.owlproperty(predicate),
                    self.owlindividual(subject.arguments[1]),
                )
            raise ValueError("instance assertions expect one individual or a pair of individuals")

        raise ValueError(f"Unsupported ontology assertion: {expr.name}")

    def add_axioms(self, axioms):
        """Apply assertions before the ASP base program is grounded."""
        if axioms:
            self.ontology.add_axiom(axioms)
            with tempfile.NamedTemporaryFile(suffix=".owl", delete=False) as ontology_copy:
                self.active_ontology_file = Path(ontology_copy.name)
            self.ontology.save(path=str(self.active_ontology_file), document_format="rdfxml")
            self.refresh_reasoner()

    def axiom (self, expr):
        """
            Evaluate Boolean ontology statements.
        
            Supported axioms:
                subset
                equivalence
                class assertion
                object property assertion
        
            Returns:
                clingo.Number(1) if the ontology entails the statement,
                clingo.Number(0) otherwise.
        """
        if expr.name == "subset":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(any(sc == d for sc in self.reasoner.super_classes(c)))

        if expr.name == "equivalent":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(any(eq == c for eq in self.reasoner.equivalent_classes(d)))
        
        #instances
        if expr.name == "instance":
            arg1 = expr.arguments[0]
            arg2 = expr.arguments[1]

            if len(arg1.arguments) == 0:
                o = self.owlindividual(arg1)
                c = self.owlclass(arg2)
                return self.bool_symbol(any(ind == o for ind in self.reasoner.instances(c, direct=False)))

            elif len(arg1.arguments) == 2:
                o1 = self.owlindividual(arg1.arguments[0])
                o2 = self.owlindividual(arg1.arguments[1])
                r = self.owlproperty(arg2)
                return self.bool_symbol(any(val == o2 for val in self.reasoner.object_property_values(o1, r)))
            
            else:

                raise ValueError("instance expects 1 or 2 subjects")
            
    def belongsto(self, expr):
            owl_expr = self.owlclass(expr)
            individuals = self.reasoner.instances(owl_expr, direct=False)
            result = []
            for ind in individuals:
                name = ind.iri.as_str().split("#")[-1]
                result.append(clingo.Function(name.lower()))
            return result
    
class TheoryTermTranslator:
    """Convert parsed Clingo theory terms into the symbolic OWL representation."""

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
            return Function(operators.get(term.name, term.name), args)

        raise ValueError(f"Unsupported theory term: {term.ast_type}")


class OntologyAssertionHandler:
    """Collect &owlassert atoms from #program ontology and apply them as OWL axioms."""

    def __init__(self, theory_parser, term_translator, context):
        self.theory_parser = theory_parser
        self.term_translator = term_translator
        self.context = context
        self.assertions = []

    def collect(self, sentence):
        if sentence.ast_type != cast.ASTType.Rule:
            return

        if sentence.body:
            raise ValueError("Ontology assertions must be facts without an ASP rule body")

        # In a rule head, Clingo represents a theory atom directly rather
        # than wrapping it in a Literal, unlike theory atoms in rule bodies.
        head = sentence.head
        if head.ast_type != cast.ASTType.TheoryAtom:
            raise ValueError("#program ontology accepts only &owlassert{...} facts")

        if head.term.name != OWL_ASSERT_ATOM:
            raise ValueError("Use &owlassert{...} in #program ontology")

        parsed_atom = self.theory_parser(head)
        root = parsed_atom.elements[0].terms[0]
        self.assertions.append(self.term_translator.translate_term(root))

    def apply(self):
        self.context.add_axioms([self.context.build_axiom(expr) for expr in self.assertions])


class ReasoningTranslator:
    """Translate &owl and &owlquery literals from #program base into callbacks."""
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
        
        &owlassert/0 : formula, head;
        &owl/0 : formula, body;
        &owlquery/0 : formula, {=}, term, body
    }."""

    def __init__(self):
        self.program = []
        self.theory_parser = parse_theory(self.clingowl_theory)
        self.term_translator = TheoryTermTranslator()

    def get_translation(self):
        translation = "\n".join([str(ast) for ast in self.program])
        return translation

    def translate_statement(self, sentence: cast.AST):
        """
        Translate every OWL theory atom occurring in a rule.
        &owl{...}--> @axiom(...)
        &owlquery{...}=X--> @belongsto(...)=X
        """
        new_body = []

        if sentence.ast_type == cast.ASTType.Rule:
            for literal in sentence.body:
                if literal.ast_type == cast.ASTType.Literal and literal.atom.ast_type == cast.ASTType.TheoryAtom:
                    atom_name = literal.atom.term.name
                    parsed_theory_atom = self.theory_parser(literal.atom)
                    root = parsed_theory_atom.elements[0].terms[0]
                    translated_expr = self.term_translator.translate_term(root)

                    if atom_name == OWL_BOOL_ATOM:
                        expr_term= SymbolicTerm(loc, translated_expr)
                        bool_term = SymbolicTerm(loc, Number(1))
                        axiom_call = cast.Function(loc,"axiom",[expr_term], True  )
                        comparison = cast.Comparison( axiom_call, [cast.Guard(cast.ComparisonOperator.Equal,bool_term)])
                        new_lit = Literal(literal.location, literal.sign, comparison)
                        new_body.append(new_lit)

                    elif atom_name == OWL_QUERY_ATOM:
                        guard_term = literal.atom.guard.term
                        belongs_call = cast.Function(loc,"belongsto",[SymbolicTerm(loc, translated_expr)], True  )
                        comparison = cast.Comparison( belongs_call, [cast.Guard(cast.ComparisonOperator.Equal,guard_term)])
                        new_lit = Literal(literal.location, literal.sign, comparison)
                        new_body.append(new_lit)


                    else:
                        new_body.append(literal)

                else:
                    new_body.append(literal)

            new_rule = Rule(sentence.location, sentence.head, new_body)
            self.program.append(new_rule)
        else:
            self.program.append(sentence)


class ProgramDispatcher:
    """Route ontology assertions and base-program rules to their dedicated handlers."""

    def __init__(self, assertion_handler, reasoning_translator):
        self.assertion_handler = assertion_handler
        self.reasoning_translator = reasoning_translator
        self.current_program = "base"

    def process(self, sentence):
        if sentence.ast_type == cast.ASTType.Program:
            self.current_program = sentence.name
            if self.current_program != "ontology":
                self.reasoning_translator.translate_statement(sentence)
            return

        if self.current_program == "ontology":
            self.assertion_handler.collect(sentence)
        else:
            self.reasoning_translator.translate_statement(sentence)

def main():
    with open(ASP_FILE, "r") as file:
        program = file.read()

    context = OntologyContext(ONTOLOGY_FILE, namespace)
    reasoning_translator = ReasoningTranslator()
    assertion_handler = OntologyAssertionHandler(
        reasoning_translator.theory_parser,
        reasoning_translator.term_translator,
        context,
    )
    dispatcher = ProgramDispatcher(assertion_handler, reasoning_translator)

    parse_string(program, dispatcher.process)

    # Assertions are applied before the base ASP program is grounded.
    assertion_handler.apply()
    print("===== Applied ontology assertions =====")
    for assertion in assertion_handler.assertions:
        print(assertion)
    print("Ontology used by the reasoner:", context.active_ontology_file)
    translated_program = reasoning_translator.get_translation()
    print("===== Translated Program =====")
    print(translated_program)

    ctl = clingo.Control()
    ctl.add("base", [], translated_program)
    ctl.ground([("base", [])], context=context)
    ctl.configuration.solve.models = "2"
    num_models = 0

    print("===== Reasoning =====")
    with ctl.solve(yield_=True) as handle:
        for model in handle:
            if num_models > 0:
                print("Warning: more than 1 model")
                break
            print(*model.symbols(atoms=True))
            num_models = 1

    if num_models == 0:
        print("UNSATISFIABLE")


if __name__ == "__main__":
    main()
