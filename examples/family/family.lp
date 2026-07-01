% -------------------------------------------------------------------
% ClingOWL example program
% -------------------------------------------------------------------
% This program demonstrates how OWL theory atoms can be used inside
% ASP rules to query an OWL ontology and check ontology entailments.
%
% &owlquery{ ... } = X
%   retrieves individuals satisfying a DL/OWL class expression.
%
% &owl{ ... }
%   checks whether an OWL axiom or assertion is entailed.
% -------------------------------------------------------------------


% -------------------------------------------------------------------
% Class expression queries
% -------------------------------------------------------------------

% Retrieve all individuals that are adults and either fathers or mothers.
parent(X) :-
    &owlquery{ adult & (father | mother) } = X.

% Retrieve all individuals that are both adults and mothers.
parent_mother(X) :-
    &owlquery{ adult & mother } = X.

% Retrieve all individuals that are not classified as female.
not_female(X) :-
    &owlquery{ ~female } = X.

% Retrieve all individuals having at least one child classified as male.
% DL meaning: exists hasChild.Male
male_children(X) :-
    &owlquery{ hasChild ! male } = X.

% Retrieve all individuals whose children, if any, are not in OWL Nothing.
% This can be used to identify individuals related through hasChild.
% DL meaning: forall hasChild.not(Nothing)
has_child(X) :-
    &owlquery{ hasChild ? ~nothing } = X.


% -------------------------------------------------------------------
% Subsumption and equivalence checks
% -------------------------------------------------------------------

% Check whether father is a subclass of person.
check_father :-
    &owl{ father <: person }.

% Check whether mother is a subclass of person.
check_mother :-
    &owl{ mother <: person }.

% Check whether parent is equivalent to:
% person and having some child that is a person.
check_parent :-
    &owl{ parent = (person & (hasChild ! person)) }.

% Derive false if the ontology entails that mother is a subclass of father.
% This can be used as an ontology-aware consistency check.
false :-
    &owl{ mother <: father }.


% -------------------------------------------------------------------
% Class and object property assertion checks
% -------------------------------------------------------------------

% Check whether peter is an instance of father.
is_father :-
    &owl{ (peter) :: father }.

% Check whether the ontology entails hasChild(susan, peter).
is_parent(susan, peter) :-
    &owl{ (susan, peter) :: hasChild }.


% -------------------------------------------------------------------
% Additional OWL constructs
% -------------------------------------------------------------------

% Query individuals connected through the inverse of hasChild to OWL Thing.
% DL meaning: exists inverse(hasChild).Thing
p(X) :-
    &owlquery{ -hasChild ! thing } = X.

% Query individuals whose friends are in OWL Nothing.
% DL meaning: forall friend.Nothing
r(X) :-
    &owlquery{ friend ? nothing } = X.

% Retrieve the singleton nominal containing peter.
only_peter(X) :-
    &owlquery{ {peter} } = X.

% Retrieve individuals belonging to the enumeration {peter, mary, john}.
chosen(X) :-
    &owlquery{ {peter,mary,john} } = X.

% Retrieve individuals that are related to themselves through talksTo.
% DL meaning: exists talksTo.Self
self_talker(X) :-
    &owlquery{ talksTo ! self } = X.
