# Bounded Allergy-Name Resolution

Reviewed on 2026-11-02. Mapping version: fda-major-terms-2026-11-02-v1.
The current increment recognizes a deliberately small English vocabulary. It does
not assess individual reactions, food composition, cross-contact, or food safety.

## Source and scope

The reference is FDA's January 2025 Edition 5, sections A.1-A.2, B.9, B.11,
and C.10-C.11. Its major-allergen framework is a bounded US labeling reference,
not a complete global allergy list. The singular/plural and soy name variants
are informed by C.10-C.11. The application authors only a short exact-match subset.

- [FDA guidance](https://www.fda.gov/media/117410/download)
- [FDA current FAQ, checked 2026-11-02](https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-regulatory-information/frequently-asked-questions-food-allergen-labeling-guidance-industry)

The nine internal groups and all 15 recognized names are listed in
backend/services/allergens.py. Names are milk; egg/eggs; fish; crustacean shellfish;
tree nut/tree nuts; peanut/peanuts; wheat; soy/soya/soybean/soybeans; sesame.
A group assignment is a taxonomy result, not a statement of medical equivalence.

## Exact matching and privacy

The resolver shares the existing saved-name normalization: printable bounded text,
whitespace normalization, and case-folding. It requires the same maximum of 20
names with at most 64 characters each. It performs no substring/fuzzy matching,
translation, punctuation splitting, negation interpretation, or model inference.
Multiple reviewed aliases can resolve to one ID while the original saved names
remain unchanged. Results contain immutable sorted IDs and unresolved names,
plus the mapping version. No result or reported name is logged or sent externally.

Unknown terms remain data, not errors when preferences are saved. They cannot be
discarded during future selection. Examples intentionally unresolved include
nuts, shellfish, coconut, lactose, gluten, species names, translations, and phrases
such as milk free. Being unresolved is never a finding that a food is safe.

This increment does not alter database rows, API contracts, or browser forms.
Food ingredient/diet/allergen metadata still needs separate evidence review.
The current nutrient-only catalog must remain blocked from automatic selection.


## Readiness integration

Food readiness now reports allergy_names_unresolved when any reported name is
outside this vocabulary, including partially recognized lists. Recognized lists
do not receive that code, but retain allergy_mapping_unreviewed because matching
names is not ingredient/cross-contact review. Existing composition, ingredient,
diet, allergen, and nutrient blockers remain active. All four nutrient-only seeds
stay blocked, including for known names and none_reported status.

Two targeted readiness tests passed for recognized names retaining their blockers
and mixed/ambiguous lists retaining every unresolved restriction. The original
catalog-use checks also passed; no food selection has been opened.
