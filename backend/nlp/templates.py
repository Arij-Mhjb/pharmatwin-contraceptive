"""SPARQL SELECT templates. All ontology bindings come from ontology_map.

Uses explicit type/subclass paths and declared inverse directions; no OWL
reasoner is assumed. This does not implement general OWL inference.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from rdflib import Literal, URIRef

from . import ontology_map as m
from .preprocess import normalize


def iri(value) -> str:
    """Serialize only absolute IRIs, rejecting SPARQL delimiters/injection."""
    value = str(value)
    if not urlsplit(value).scheme or re.search(r'[\s<>"{}|^`\\\x00-\x1f]', value):
        raise ValueError("Invalid absolute IRI")
    if "PLACEHOLDER" in value:
        raise ValueError("Unresolved ontology placeholder")
    return URIRef(value).n3()


def typed(variable, cls):
    explicit = f"{variable} {iri(m.TYPE)}/{iri(m.SUBCLASS_OF)}* {iri(cls)} ."
    forms = m.CLASS_FORM_VALUES.get(URIRef(str(cls)), ())
    if not forms:
        return explicit
    alternatives = ["{ " + explicit + " }"]
    for form in forms:
        alternatives.append(
            "{ " + f"{variable} {iri(m.TYPE)}/{iri(m.SUBCLASS_OF)}* {iri(m.C_CONTRACEPTIF)} . "
            f"{variable} {iri(m.D_FORME)} {Literal(form).n3()} ." + " }")
    return "{ " + " UNION ".join(alternatives) + " }"


def _wrap(body, *, limit=50):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit must be an integer between 1 and 500")
    prefixes = "\n".join(f"PREFIX {name}: {iri(namespace)}" for name, namespace in m.PREFIXES.items())
    return (f"{prefixes}\nSELECT DISTINCT ?result ?label WHERE {{\n{body}\n"
            f"OPTIONAL {{ ?result {iri(m.LABEL)} ?label . }}\n}}\n"
            f"ORDER BY LCASE(STR(?label)) STR(?result)\nLIMIT {limit}")


def _focus(entities):
    # Broad nouns such as 'contraceptives' must not displace the named condition.
    broad = {str(v) for v in (m.C_CONTRACEPTIF, m.C_MOLECULE, m.C_PROFIL,
                             m.C_CONDITION, m.C_EFFET, m.C_SOURCE, m.C_CONTRE_INDICATION)}
    return [e for e in entities if e.get("kind") in {"class", "individual"}
            and e.get("iri") not in broad]


def _filter(variables, entities):
    """OR across recognized targets; class anchors match subclass instances."""
    clauses = []
    for entity in entities:
        target = iri(entity["iri"])
        for variable in variables:
            if entity["kind"] == "class":
                clauses.append("EXISTS { " + typed(variable, entity["iri"]) + " }")
            else:
                clauses.append(f"{variable} = {target}")
    return "FILTER (" + " || ".join(clauses) + ")" if clauses else ""


def _contraceptive_link():
    return f"({iri(m.P_CONTRE_INDICATION)}|^{iri(m.P_CONCERNE_CONTRACEPTIF)})"


def _molecule_link():
    return "(" + "|".join(iri(p) for p in (m.P_CONTIENT_MOLECULE, m.P_CONTIENT_OESTROGENE, m.P_CONTIENT_PROGESTATIF)) + "|^" + iri(m.P_EST_CONTENU_DANS) + ")"


def contre_indications_contraceptif(entities=(), *, limit=50, **_):
    body = f"{typed('?contraceptif', m.C_CONTRACEPTIF)}\n?contraceptif {_contraceptive_link()} ?result .\n{typed('?result', m.C_CONTRE_INDICATION)}"
    return _wrap(body + "\n" + _filter(["?contraceptif"], _focus(entities)), limit=limit)


def effets_indesirables_contraceptif(entities=(), *, limit=50, **_):
    body = f"{typed('?contraceptif', m.C_CONTRACEPTIF)}\n?contraceptif {iri(m.P_EFFET)} ?result .\n{typed('?result', m.C_EFFET)}"
    return _wrap(body + "\n" + _filter(["?contraceptif"], _focus(entities)), limit=limit)


def molecules_contraceptif(entities=(), *, limit=50, **_):
    body = f"{typed('?contraceptif', m.C_CONTRACEPTIF)}\n?contraceptif {_molecule_link()} ?result .\n{typed('?result', m.C_MOLECULE)}"
    return _wrap(body + "\n" + _filter(["?contraceptif"], _focus(entities)), limit=limit)


def interactions_molecule(entities=(), *, limit=50, **_):
    body = (f"{{ ?molecule ({iri(m.P_INTERAGIT)}|^{iri(m.P_INTERAGIT)}) ?result . }} UNION "
            f"{{ ?interaction {iri(m.P_CONCERNE_MOLECULE)} ?molecule, ?result . }}\n"
            f"{typed('?molecule', m.C_MOLECULE)}\n{typed('?result', m.C_MOLECULE)}\n"
            "FILTER (?molecule != ?result)")
    return _wrap(body + "\n" + _filter(["?molecule"], _focus(entities)), limit=limit)


def contraceptifs_contre_indiques_condition(entities=(), *, limit=50, **_):
    body = (f"{typed('?result', m.C_CONTRACEPTIF)}\n?result {_contraceptive_link()} ?ci .\n"
            f"?ci {iri(m.P_CONCERNE_CONDITION)} ?condition .")
    return _wrap(body + "\n" + _filter(["?condition"], _focus(entities)), limit=limit)


def profils_par_condition(entities=(), *, limit=50, **_):
    body = (f"{typed('?result', m.C_PROFIL)}\n"
            f"?result {iri(m.P_A_POUR_CONDITION)} ?condition .")
    return _wrap(body + "\n" + _filter(["?condition", "?result"], _focus(entities)), limit=limit)


def profils_a_risque(entities=(), *, limit=50, risk_kind="general", **_):
    # Known class definitions are expressed explicitly to work without a reasoner.
    if risk_kind == "oestrogenes":
        risk_class, condition_class = m.C_PROFIL_ALERTE_OESTROGENE, m.C_CONDITION_CHC
    elif risk_kind == "vasculaire":
        risk_class, condition_class = m.C_PROFIL_RISQUE_VASCULAIRE, None
    elif risk_kind == "general":
        risk_class, condition_class = m.C_PROFIL_RISQUE, m.C_FACTEUR_RISQUE
    else:
        raise ValueError("Unknown risk kind")
    body = "{ " + typed("?result", risk_class) + " }"
    if condition_class is not None:
        body += (f" UNION {{ {typed('?result', m.C_PROFIL)} "
                 f"?result {iri(m.P_A_POUR_CONDITION)} ?condition . "
                 f"{typed('?condition', condition_class)} }}")
    return _wrap(body, limit=limit)


def benefices_contraceptif(entities=(), *, limit=50, **_):
    body = (f"{typed('?contraceptif', m.C_CONTRACEPTIF)}\n"
            f"?contraceptif ({iri(m.P_BENEFICE)}|{iri(m.P_EFFET)}) ?result .\n"
            f"{typed('?result', m.C_BENEFICE)}")
    return _wrap(body + "\n" + _filter(["?contraceptif"], _focus(entities)), limit=limit)


def sources_preuve(entities=(), *, limit=50, **_):
    # Evidence can justify a CI/effect/interaction or evaluate a contraceptive.
    body = (f"{{ ?claim {iri(m.P_JUSTIFIE_PAR)} ?result . }} UNION "
            f"{{ ?result {iri(m.P_EVALUE_CONTRACEPTIF)} ?claim . }}\n"
            f"{typed('?result', m.C_SOURCE)}\n")
    targets = _focus(entities)
    if targets:
        related = "(" + "|".join(iri(p) for p in (
            m.P_CONCERNE_CONDITION, m.P_CONCERNE_CONTRACEPTIF, m.P_CONCERNE_MOLECULE
        )) + "|^" + iri(m.P_CONTRE_INDICATION) + "|^" + iri(m.P_EFFET) + "|^" + iri(m.P_BENEFICE) + ")"
        body += f"?claim {related}? ?target .\n" + _filter(["?target"], targets)
    return _wrap(body, limit=limit)


def lister_classe(entities=(), *, limit=50, **_):
    classes = [e for e in entities if e.get("kind") == "class"]
    if not classes:
        return recherche_libre(limit=limit)
    body = " UNION ".join("{ " + typed("?result", e["iri"]) + " }" for e in classes)
    return _wrap(body, limit=limit)


def recherche_libre(entities=(), *, keywords=(), limit=50, **_):
    # RDFLib escapes quotes, backslashes and newlines as RDF string literals.
    words = list(dict.fromkeys(normalize(str(word)) for word in keywords if str(word).strip()))[:12]
    label_text = "LCASE(STR(?matchedLabel))"
    for pattern, replacement in (("œ", "oe"), ("æ", "ae"), ("[àâäáãå]", "a"),
                                 ("[éèêë]", "e"), ("[îïíì]", "i"), ("[ôöóòõ]", "o"),
                                 ("[ùûüú]", "u"), ("ç", "c"), ("[ÿý]", "y")):
        label_text = f"REPLACE({label_text}, {Literal(pattern).n3()}, {Literal(replacement).n3()})"
    body = f"?result {iri(m.LABEL)} ?matchedLabel .\nFILTER (isIRI(?result))\n"
    if words:
        body += "FILTER (" + " || ".join(
            f"CONTAINS({label_text}, {Literal(word).n3()})" for word in words
        ) + ")"
    else:
        body += "FILTER (false)"  # Empty input must not expose the entire graph.
    return _wrap(body, limit=limit)


TEMPLATES = {function.__name__: function for function in (
    contre_indications_contraceptif, effets_indesirables_contraceptif,
    molecules_contraceptif, interactions_molecule, contraceptifs_contre_indiques_condition,
    profils_par_condition, profils_a_risque, benefices_contraceptif,
    sources_preuve, lister_classe, recherche_libre,
)}


def build_query(intent, entities=(), **options):
    return TEMPLATES.get(intent, recherche_libre)(entities, **options)


if __name__ == "__main__":
    import argparse
    from rdflib import Graph
    from .entities import EntityExtractor
    from .intent import detect_intent, detect_risk_kind
    from .preprocess import normalize, preprocess

    parser = argparse.ArgumentParser(description="Preview SPARQL; optionally execute against a local ontology")
    parser.add_argument("question")
    parser.add_argument("--ontology", default=None)
    args = parser.parse_args()
    extractor = EntityExtractor()
    data = preprocess(args.question, nlp=extractor.nlp)
    entities = extractor.extract(args.question)
    intent = detect_intent(data, entities)
    risk = detect_risk_kind(args.question)
    query = build_query(intent, entities, keywords=data.keywords, risk_kind=risk)
    print(f"Intent: {intent}\n\n{query}")
    if args.ontology:
        rows = list(Graph().parse(args.ontology).query(query))
        print(f"\nResults: {len(rows)}")
        for row in rows:
            print(" | ".join(str(value) if value is not None else "" for value in row))
