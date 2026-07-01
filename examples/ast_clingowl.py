import clingo
import sys
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
from owlapy.class_expression import OWLObjectMinCardinality, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectUnionOf, OWLObjectComplementOf, OWLNothing, OWLObjectAllValuesFrom, OWLThing, OWLObjectOneOf
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import  SyncReasoner
from owlapy.owl_individual import OWLNamedIndividual
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

onto = Ontology(
    IRI.create("my_family.owl"),
    load=True
)

namespace = "http://example.com/my_family#"
sync_reasoner = SyncReasoner(ontology=r"clingowl\ontology\my_family.owl", reasoner="Pellet")

loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)

OWL_QUERY_ATOM = "owlquery"
OWL_BOOL_ATOM = "owl"

def parse_theory(s: str) -> TheoryParser:

    parser = None

    def extract(stm):
        nonlocal parser
        if stm.ast_type == ASTType.TheoryDefinition:
            parser = theory_parser_from_definition(stm)

    parse_string(s, extract)
    return parser


class Context:
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
        return OWLObjectProperty(IRI(namespace, property_name))
   
    def owlindividual(self, ind):
        individual_name = self.upper_first(ind.name)
        return OWLNamedIndividual(IRI(namespace, individual_name))

     
    def owlclass(self, expr): 
        if expr.name == "":
            return OWLObjectOneOf([self.owlindividual(arg) for arg in expr.arguments])
        
        if len(expr.arguments)== 0: 
            #nothing
            if expr.name== "nothing":
                return OWLNothing
            if expr.name == "thing":
                return OWLThing

            class_name = self.upper_first(expr.name)
            return OWLClass(IRI(namespace, class_name))


    
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

    def axiom (self, expr):
        if expr.name == "subset":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(any(sc == d for sc in sync_reasoner.super_classes(c)))

        if expr.name == "equivalent":
            c = self.owlclass(expr.arguments[0])
            d = self.owlclass(expr.arguments[1])
            return self.bool_symbol(any(eq == c for eq in sync_reasoner.equivalent_classes(d)))
        
        #instances
        if expr.name == "instance":
            arg1 = expr.arguments[0]
            arg2 = expr.arguments[1]

            if len(arg1.arguments) == 0:
                o = self.owlindividual(arg1)
                c = self.owlclass(arg2)
                return self.bool_symbol(any(ind == o for ind in sync_reasoner.instances(c, direct=False)))

            elif len(arg1.arguments) == 2:
                o1 = self.owlindividual(arg1.arguments[0])
                o2 = self.owlindividual(arg1.arguments[1])
                r = self.owlproperty(arg2)
                return self.bool_symbol(any(val == o2 for val in sync_reasoner.object_property_values(o1, r)))
            
            else:

                raise ValueError("instance expects 1 or 2 subjects")
            
    def belongsto(self, expr):
            owl_expr = self.owlclass(expr)
            individuals = sync_reasoner.instances(owl_expr, direct=False)
            result = []
            for ind in individuals:
                name = ind.iri.as_str().split("#")[-1]
                result.append(clingo.Function(name.lower()))
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
        translation = "\n".join([str(ast) for ast in self.program])
        return translation

    def translate_term(self, term):
        
        operators = {
            "::" : "instance",
            "<:" : "subset",
            "=" : "equivalent",
            "&" : "intersection",
            "|" : "union",
            "~" : "negation",
            "?" : "forall",
            "!" : "exist",
            "-": "inverse",
        }

        
        if term.ast_type == cast.ASTType.SymbolicTerm:
            return term.symbol
        
        if term.ast_type == cast.ASTType.TheorySequence:
            return Function ("" ,[self.translate_term(arg) for arg in term.terms])
        
            
        if term.ast_type == cast.ASTType.TheoryFunction:
            args = [self.translate_term(arg) for arg in term.arguments]

            if term.name in operators:      
                return Function (operators[term.name], args)

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

with open(r"theory_ex.lp", "r") as f:
    program = f.read()

t = MyTranslator()

parse_string(
    program,
    lambda ast: t.translate_rule(ast)
)

translated_program = t.get_translation()
print("=====Translated program:====== ")
print(translated_program)

# Loading files and grounding
ctl = clingo.Control()
ctl.add("base", [], translated_program)
ctl.ground([("base", [])], context=Context())
ctl.configuration.solve.models="2" # This retrieves 2 models at most
nummodels=0

# Solving    
atoms=[]
size=0
print("===== Reasoning =====")
with ctl.solve(yield_=True) as handle:
  for model in handle:
      if nummodels>0: print("Warning: more than 1 model"); break
      for atom in model.symbols(atoms=True):
          print(atom,end=" ")
      print()
      nummodels=1 
if nummodels==0: print("UNSATISFIABLE")
