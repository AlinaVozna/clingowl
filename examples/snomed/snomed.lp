patient(alice).
has_allergy(alice, allergy_to_penicillin).
proposed_drug(alice, amoxicillin).

allergy_causative_agent(allergy_to_penicillin, amoxicillin) :-
    &owl{ allergy_to_penicillin <: causative_agent ! amoxicillin }.

unsafe(P,D) :-
    patient(P),
    has_allergy(P,A),
    proposed_drug(P,D),
    allergy_causative_agent(A,D).

candidate(P,D) :-
    patient(P),
    proposed_drug(P,D),
    not unsafe(P,D).
