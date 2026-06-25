
parent(X) :- &owlquery{ adult & (father | mother) } = X.
parent_mother(X) :- &owlquery{ adult & mother } = X.
not_female(X) :- &owlquery{ ~female } = X.
male_children(X) :- &owlquery{ hasChild ! male } = X.
has_child(X) :- &owlquery{ hasChild ? ~nothing } = X.

%subset & equivalence
check_father :- &owl{ father <: person }.
check_mother :- &owl{ mother <: person }.
check_parent  :- &owl{ parent = (person & (hasChild ! person)) }.
false  :-  &owl{ mother <: father }.

is_father :- &owl{ (peter)::father }.
is_parent (susan, peter) :- &owl{(susan, peter) :: hasChild}.

%reverse, thing, nothing
p(X) :- &owlquery{ -hasChild ! thing } = X.
r(X) :- &owlquery{ friend ? nothing } = X.
only_peter(X) :- &owlquery{ {peter} } = X.
chosen(X) :- &owlquery{ {peter,mary,john} } = X.
self_talker(X) :- &owlquery{ talksTo ! self } = X.