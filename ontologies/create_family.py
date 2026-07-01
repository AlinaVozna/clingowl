from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
from owlapy.class_expression import OWLObjectMinCardinality, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectUnionOf, OWLObjectAllValuesFrom, OWLNothing
from owlapy.owl_ontology import Ontology
from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom, OWLDeclarationAxiom, OWLEquivalentClassesAxiom, OWLSubClassOfAxiom, OWLDisjointClassesAxiom
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner
from owlapy.owl_individual import OWLNamedIndividual

from owlapy import owl_expression_to_sparql, owl_expression_to_dl, owl_expression_to_manchester


onto = Ontology(
    IRI.create("my_family.owl"),
    load=False
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

onto.add_axiom(OWLDeclarationAxiom(Person))
onto.add_axiom(OWLDeclarationAxiom(Parent))
onto.add_axiom(OWLDeclarationAxiom(Child))
onto.add_axiom(OWLDeclarationAxiom(Father))
onto.add_axiom(OWLDeclarationAxiom(Mother))
onto.add_axiom(OWLDeclarationAxiom(Female))
onto.add_axiom(OWLDeclarationAxiom(Male))
#onto.add_axiom(OWLDeclarationAxiom(Grandparent))
onto.add_axiom(OWLDeclarationAxiom(Grandchild))
onto.add_axiom(OWLDeclarationAxiom(Adult))
onto.add_axiom(OWLDeclarationAxiom(Grandfather))
onto.add_axiom(OWLDeclarationAxiom(Grandmother))



#OBJECT PROPERTY
hasChild = OWLObjectProperty(IRI(namespace, "hasChild"))
onto.add_axiom(OWLDeclarationAxiom(hasChild))


has_at_least_one_child = OWLObjectMinCardinality(
    cardinality = 1, 
    property = hasChild,
    filler = Person
)

hasAge = OWLDataProperty(IRI(namespace, "hasAge"))
onto.add_axiom(OWLDeclarationAxiom(hasAge))

#has_at_least_18_years = OWLObjectMinCardinality(
 #   cardinality = 18,
 #   property = hasAge,
 #   filler = Person
#)


#INDIVIDUALS
Susan = OWLNamedIndividual(IRI(namespace, "Susan"))
Peter = OWLNamedIndividual(IRI(namespace, "Peter"))
Diego = OWLNamedIndividual(IRI(namespace, "Diego"))
Ann = OWLNamedIndividual(IRI(namespace, "Ann"))
Mary = OWLNamedIndividual(IRI(namespace, "Mary"))
John = OWLNamedIndividual(IRI(namespace, "John"))

onto.add_axiom(OWLDeclarationAxiom(Susan))
onto.add_axiom(OWLDeclarationAxiom(Peter))
onto.add_axiom(OWLDeclarationAxiom(Diego))
onto.add_axiom(OWLDeclarationAxiom(Ann))
onto.add_axiom(OWLDeclarationAxiom(Mary))
onto.add_axiom(OWLDeclarationAxiom(John))
onto.add_axiom(OWLDeclarationAxiom(Male))
onto.add_axiom(OWLDeclarationAxiom(Female))



#TBOX (Object Intersection, Union)
Parent_def = OWLObjectIntersectionOf([Person, OWLObjectSomeValuesFrom(hasChild, Person)])
Father_def = OWLObjectIntersectionOf([Male, Parent_def])
Mother_def = OWLObjectIntersectionOf([Female, Parent_def])
#Grandparent_def = OWLObjectIntersectionOf([Person, OWLObjectSomeValuesFrom(hasChild, Parent)])
#Grandchild_def = OWLObjectIntersectionOf([Person, OWLObjectSomeValuesFrom(OWLObjectInverseOf(hasChild), Parent)])
#Adult_def = OWLObjectIntersectionOf([Person, has_at_least_18_years])
Grandfather_def = OWLObjectIntersectionOf([Male, OWLObjectSomeValuesFrom(hasChild, Parent)])
Grandmother_def = OWLObjectIntersectionOf([Female, OWLObjectSomeValuesFrom(hasChild, Parent)])

onto.add_axiom(OWLEquivalentClassesAxiom([Father, Father_def]))
onto.add_axiom(OWLEquivalentClassesAxiom([Parent, Parent_def]))
onto.add_axiom(OWLEquivalentClassesAxiom([Mother, Mother_def]))
onto.add_axiom(OWLSubClassOfAxiom(Parent, Adult))
#onto.add_axiom(OWLEquivalentClassesAxiom([Grandparent, Grandparent_def]))
#onto.add_axiom(OWLEquivalentClassesAxiom([Grandchild, Grandchild_def]))
#onto.add_axiom(OWLEquivalentClassesAxiom([Adult, Adult_def]))
onto.add_axiom(OWLEquivalentClassesAxiom([Grandfather, Grandfather_def]))
onto.add_axiom(OWLEquivalentClassesAxiom([Grandmother, Grandmother_def]))
onto.add_axiom(OWLDisjointClassesAxiom([Male, Female]))


#ABOX
onto.add_axiom(OWLClassAssertionAxiom(Susan, Female))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Susan, hasChild, Peter))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Susan, hasChild, John))
onto.add_axiom(OWLClassAssertionAxiom(Susan, Parent))
onto.add_axiom(OWLClassAssertionAxiom(Susan, Mother))
onto.add_axiom(OWLClassAssertionAxiom(Susan, Adult))
onto.add_axiom(OWLClassAssertionAxiom(Susan, Person))
onto.add_axiom(OWLClassAssertionAxiom(Susan,OWLObjectAllValuesFrom(hasChild, Male)))

onto.add_axiom(OWLClassAssertionAxiom(Peter, Male))
onto.add_axiom(OWLClassAssertionAxiom(Peter, Adult))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Peter, hasChild, Ann))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Peter, hasChild, Mary))
onto.add_axiom(OWLClassAssertionAxiom(Peter, Parent))
onto.add_axiom(OWLClassAssertionAxiom(Peter, Father))
onto.add_axiom(OWLClassAssertionAxiom(Peter, Person))
onto.add_axiom(OWLClassAssertionAxiom(Peter, Child))

onto.add_axiom(OWLClassAssertionAxiom(Diego, Male))
onto.add_axiom(OWLClassAssertionAxiom(Diego, Person))
onto.add_axiom(OWLClassAssertionAxiom(Diego, Parent))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Diego, hasChild, Peter))
onto.add_axiom(OWLObjectPropertyAssertionAxiom(Diego, hasChild, John))
onto.add_axiom(OWLClassAssertionAxiom(Diego, Father))
onto.add_axiom(OWLClassAssertionAxiom(Diego, Adult))

onto.add_axiom(OWLClassAssertionAxiom(Ann, Female))
onto.add_axiom(OWLClassAssertionAxiom(Ann, Child))
onto.add_axiom(OWLClassAssertionAxiom(Ann, Person))
# In the case of Ann, we know she has no children at all. This has to be stated explicitly
onto.add_axiom(OWLClassAssertionAxiom(Ann,OWLObjectAllValuesFrom(hasChild, OWLNothing)))

onto.add_axiom(OWLClassAssertionAxiom(Mary, Female))
onto.add_axiom(OWLClassAssertionAxiom(Mary, Adult))
onto.add_axiom(OWLClassAssertionAxiom(Mary, Person))
onto.add_axiom(OWLClassAssertionAxiom(Mary, Adult))
onto.add_axiom(OWLClassAssertionAxiom(Mary, Child))

onto.add_axiom(OWLClassAssertionAxiom(John, Male))
onto.add_axiom(OWLClassAssertionAxiom(John, Child)) 
onto.add_axiom(OWLClassAssertionAxiom(John, Person))

onto.save("my_family.owl")




