% ============================================================================
% ClingOWL example program
% ============================================================================
% This program demonstrates ontology assertions and ontology-aware ASP
% reasoning over the family OWL ontology.
%
% &owlassert{ ... }
%   Adds an OWL axiom before ASP reasoning. It is allowed only as a fact in
%   #program ontology and modifies a temporary copy of the ontology.
%
% &owl{ ... }
%   Checks whether an OWL axiom or assertion is entailed.
%
% &owlquery{ ... } = X
%   Retrieves ontology individuals satisfying a DL/OWL class expression.
% ============================================================================

% ---------------------------------------------------------------------------
% Phase 1: ontology construction
% ---------------------------------------------------------------------------
% The following assertions are added to the ontology before #program base is
% translated, grounded, and solved.

#program ontology.

% Class assertion: John is a father.
&owlassert{ john :: father }.

% Object property assertion: John has Ann as a child.
&owlassert{ (john,ann) :: hasChild }.


% ---------------------------------------------------------------------------
% Phase 2: ASP reasoning over the extended ontology
% ---------------------------------------------------------------------------

#program base.

% ---------------------------------------------------------------------------
% Assertion checks
% ---------------------------------------------------------------------------

% Verify the class assertion introduced in #program ontology.
assertion_applied :- &owl{ john :: father }.

% Verify the role assertion introduced in #program ontology.
john_has_child_ann :- &owl{ (john,ann) :: hasChild }.


% ---------------------------------------------------------------------------
% Class expression queries
% ---------------------------------------------------------------------------

% Retrieve adults who are either fathers or mothers.
parent(X) :- &owlquery{ adult & (father | mother) } = X.

% Retrieve adults who are mothers.
parent_mother(X) :- &owlquery{ adult & mother } = X.

% Retrieve individuals that are not classified as female.
not_female(X) :- &owlquery{ ~female } = X.

% DL meaning: exists hasChild.Male.
male_children(X) :- &owlquery{ hasChild ! male } = X.

% DL meaning: forall hasChild.not(Nothing).
% Because not(Nothing) is Thing, this is true independently of hasChild links.
has_child(W) :- &owlquery{ hasChild ? ~nothing } = W.


% ---------------------------------------------------------------------------
% Subsumption and equivalence checks
% ---------------------------------------------------------------------------

check_father :- &owl{ father <: person }.
check_mother :- &owl{ mother <: person }.

% Parent is equivalent to a person having some child that is a person.
check_parent :- &owl{ parent = (person & (hasChild ! person)) }.

% Ontology-aware consistency check.
false :- &owl{ mother <: father }.


% ---------------------------------------------------------------------------
% Existing class and object property assertion checks
% ---------------------------------------------------------------------------

is_father :- &owl{ peter :: father }.
is_parent(susan,peter) :- &owl{ (susan,peter) :: hasChild }.


% ---------------------------------------------------------------------------
% Additional OWL constructors
% ---------------------------------------------------------------------------

% DL meaning: exists inverse(hasChild).Thing.
p(X) :- &owlquery{ -hasChild ! thing } = X.

% DL meaning: forall friend.Nothing.
r(X) :- &owlquery{ friend ? nothing } = X.

% Nominal containing only Peter.
only_peter(X) :- &owlquery{ {peter} } = X.

% Enumeration of named individuals.
chosen(X) :- &owlquery{ {peter,mary,john} } = X.
