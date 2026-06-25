from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
from owlapy.class_expression import OWLObjectMinCardinality, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectUnionOf
from owlapy.owl_ontology import Ontology
from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom, OWLDeclarationAxiom, OWLEquivalentClassesAxiom, OWLSubClassOfAxiom
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner
from owlapy.owl_individual import OWLNamedIndividual

from owlapy import owl_expression_to_sparql, owl_expression_to_dl, owl_expression_to_manchester

onto = Ontology(
    IRI.create("my_family.owl"),
    load=True
)

namespace = "http://example.com/my_family#"

#CLASSES
Person= OWLClass(IRI(namespace, "Person"))
Parent = OWLClass(IRI(namespace, "Parent"))
Child = OWLClass(IRI(namespace, "Child"))
Father = OWLClass(IRI(namespace, "Father"))
Mother = OWLClass(IRI(namespace, "Mother"))
Female = OWLClass(IRI(namespace, "Female"))    
Male = OWLClass (IRI(namespace, "Male"))
Grandfather = OWLClass(IRI(namespace, "Grandfather"))
Grandmother = OWLClass(IRI(namespace, "Grandmother"))
#Grandparent = OWLClass(IRI(namespace, "Grandparent"))
Grandchild = OWLClass(IRI(namespace, "Grandchild"))
Adult = OWLClass(IRI(namespace, "Adult"))

#for ind in onto.individuals_in_signature():
 #   print(ind)


# Reasoner 
#structural_reasoner = StructuralReasoner(onto, property_cache = True, negation_default = True, sub_properties = False)
sync_reasoner = SyncReasoner(ontology="clingowl/ontology/my_family.owl", reasoner="Pellet")


#Reasoning
parent_individuals = sync_reasoner.instances(Parent)
for ind in parent_individuals:
   print("Who is a parent?:", owl_expression_to_manchester(ind))

child_individuals = sync_reasoner.instances(Child)
for ind in child_individuals:
   print("Who is a child?:", owl_expression_to_manchester(ind))

Grandfather_individuals = sync_reasoner.instances(Grandfather)
for ind in Grandfather_individuals:
   print("Who is a grandfather?:", owl_expression_to_manchester(ind))

Grandmother_individuals = sync_reasoner.instances(Grandmother)
for ind in Grandmother_individuals:
   print("Who is a grandmother?:", owl_expression_to_manchester(ind))

Adult_individuals = sync_reasoner.instances(Adult)
for ind in Adult_individuals:
   print("Who is an adult?:", owl_expression_to_manchester(ind))


