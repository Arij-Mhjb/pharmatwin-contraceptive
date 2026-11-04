"""Replaceable ontology bindings for PharmaTwin Contraceptive.

Bindings checked against PharmaTwin_Contraceptive (2).owl. Unavailable
relationships remain explicitly marked placeholders and must not be queried.

Query construction must import these bindings rather than embed ontology IRIs.
Lexical labels and entity IRIs belong in the replaceable lexicon JSON instead.
"""

from rdflib import Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD


# Verified namespace from the corrected RDF/XML file.
ONTOLOGY = Namespace("https://pharmatwin.ai/contraceptive#")

# Classes
C_CONTRACEPTIF = ONTOLOGY["Contraceptif"]
C_MOLECULE = ONTOLOGY["Molecule"]
C_PROFIL = ONTOLOGY["ProfilPatiente"]
C_CONDITION = ONTOLOGY["ConditionClinique"]
C_EFFET = ONTOLOGY["EffetIndesirable"]
C_BENEFICE = ONTOLOGY["EffetBenefique"]
C_SOURCE = ONTOLOGY["Etude"]
C_FACTEUR_RISQUE = ONTOLOGY["FacteurDeRisque"]
C_CONTRE_INDICATION = ONTOLOGY["ContreIndication"]
C_PROFIL_RISQUE = ONTOLOGY["ProfilAvecFacteurDeRisque"]
C_PROFIL_RISQUE_VASCULAIRE = ONTOLOGY["ProfilRisqueVasculaire"]
C_PROFIL_ALERTE_OESTROGENE = ONTOLOGY["ProfilAlerteOestrogene"]

# Object properties. The intended subject -> object is documented here so the
# eventual templates can be checked against the corrected domain and range.
P_CONTRE_INDICATION = ONTOLOGY["aContreIndication"]
# contraceptive -> contraindication record -> clinical condition
P_CONCERNE_CONDITION = ONTOLOGY["concerneCondition"]
P_CONCERNE_CONTRACEPTIF = ONTOLOGY["concerneContraceptif"]
P_A_POUR_CONDITION = ONTOLOGY["aCondition"]
# simulated patient profile -> clinical condition
P_CONTIENT_MOLECULE = ONTOLOGY["contientMolecule"]
# contraceptive -> molecule
P_EFFET = ONTOLOGY["peutProduire"]
# contraceptive -> clinical effect; filter by C_EFFET for adverse effects
P_INTERAGIT = ONTOLOGY["interagitAvecMolecule"]
# molecule -> molecule (direction/symmetry to verify)
P_JUSTIFIE_PAR = ONTOLOGY["justifiePar"]
# resource describing a claim -> evidence source (claim representation to verify)
P_BENEFICE = ONTOLOGY["peutProcurer"]
# contraceptive -> benefit
P_A_POUR_FACTEUR_RISQUE = URIRef("https://example.org/PLACEHOLDER/pharmatwin#aPourFacteurRisque")  # TODO verify after ontology correction
# Not declared: use profile classes/OWL definitions rather than this property.
P_EN_ALERTE_POUR = URIRef("https://example.org/PLACEHOLDER/pharmatwin#enAlertePour")  # TODO verify after ontology correction
# Not declared: use C_PROFIL_ALERTE_OESTROGENE rather than this property.

# Data properties on simulated patient profiles
D_AGE = ONTOLOGY["age"]
D_IMC = ONTOLOGY["imc"]
D_FUME = ONTOLOGY["fume"]

# Stable RDF standards, independent of the project's class/property names.
TYPE = RDF.type
LABEL = RDFS.label
SUBCLASS_OF = RDFS.subClassOf

# Shared prefix bindings for future SPARQL template headers.
PREFIXES: dict[str, URIRef | Namespace] = {
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
    "pt": ONTOLOGY,
}
