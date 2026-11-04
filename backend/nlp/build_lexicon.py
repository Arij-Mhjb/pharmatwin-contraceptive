"""Generate a replaceable NLP lexicon from RDF/XML (.owl) or Turtle (.ttl).

Run from the project root:
python -m backend.nlp.build_lexicon path/to/ontology.owl
"""

import argparse
import json
import re
from pathlib import Path
import sys

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS


def build_lexicon(source: Path, output: Path, *, language: str = "fr") -> dict:
    graph = Graph().parse(str(source))
    kinds = {
        OWL.Class: "class",
        OWL.NamedIndividual: "individual",
        OWL.ObjectProperty: "objectProperty",
        OWL.DatatypeProperty: "dataProperty",
    }
    entries = {}
    missing = []
    for rdf_type, kind in kinds.items():
        for subject in sorted(set(graph.subjects(RDF.type, rdf_type)), key=str):
            # OWL anonymous union/restriction expressions are not named entities.
            if not isinstance(subject, URIRef):
                continue
            labels = [label for label in graph.objects(subject, RDFS.label)
                      if getattr(label, "language", None) in (None, language)]
            if not labels:
                missing.append(str(subject))
            for label in sorted(labels, key=str):
                key = str(label).strip()
                if not key:
                    continue
                entry = {"iri": str(subject), "kind": kind}
                if key in entries and entries[key] != entry:
                    raise ValueError(f"Ambiguous label {key!r}; cannot represent both terms in this JSON format")
                entries[key] = entry
                # Derive short acronym aliases from labels, e.g. a full label
                # ending in '(ABC)'. No domain-specific alias list is embedded.
                for acronym in re.findall(r"\(([A-Z][A-Z0-9]{1,9})\)", key):
                    if acronym in entries and entries[acronym] != entry:
                        raise ValueError(f"Ambiguous acronym {acronym!r}")
                    entries[acronym] = entry
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for iri in missing:
        print(f"Warning: no {language}/untagged rdfs:label: {iri}", file=sys.stderr)
    return entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path("ontology/pharmatwin.ttl"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("lexicon.json"))
    parser.add_argument("--language", default="fr")
    args = parser.parse_args()
    entries = build_lexicon(args.source, args.output, language=args.language)
    print(f"Generated {len(entries)} labels in {args.output}")
