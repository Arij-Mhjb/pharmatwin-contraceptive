# Validation du mini-projet Web Sémantique

## Périmètre de l’audit

Audit des consignes textuelles transmises par Maha MALLEK. La grille jointe et la liste officielle des thèmes n’ont pas été fournies : l’appartenance de la contraception à cette liste et les éventuels critères supplémentaires restent à confirmer. La conformité technique ne constitue pas une garantie de note.

| Consigne | Preuve dans PharmaTwin | Démonstration |
| --- | --- | --- |
| Choisir un thème autorisé | Domaine : contraception et profils simulés | Confirmer sa présence dans la liste officielle |
| Créer une ontologie | `ontology/pharmatwin.ttl`, source OWL conservée | Ouvrir dans Protégé puis `/ontology` |
| ObjectProperty | 22 propriétés, inventaire RDFLib | Onglet ObjectProperty |
| DataProperty | 24 propriétés | Onglet DataProperty |
| Individus | 80 individus dans l’ontologie source | Onglet Individus |
| Classes et axiomes | 45 classes, sous-classes, équivalences, domaines et portées | Onglets Classes et Axiomes ; inspecter ProfilSOPK |
| Interfaces front et back | Next.js 16, FastAPI, Swagger `/docs` | Naviguer et inspecter les réponses HTTP |
| SPARQL CRUD | `backend/crud.py` : SELECT, INSERT, DELETE, mises à jour | Admin → profils techniques → créer, modifier, supprimer un profil de démonstration |
| Filtrage et recherche | Filtres âge/tabagisme/condition ; recherche Unicode et embeddings | Filtrer les profils puis chercher « pilule » |
| Communication front/back | `frontend/lib/api.ts`, cookies, CORS, endpoints FastAPI | Observer les requêtes dans l’onglet Network du navigateur |
| Question → SPARQL exécutable | `backend/nlp/translator.py`, `templates.py`, `/api/ask` | Poser une question, montrer intention, entités, SPARQL et résultats |
| Pas d’API LLM par prompt | Traduction locale spaCy/RapidFuzz, règles et templates | Présenter les sources et les dépendances NLP |
| Outils explicitement cités | Voir texte de présentation ci-dessous | Intégrer ce texte aux diapositives |

## Texte technique à reprendre dans la présentation

« Le traducteur français utilise spaCy avec le modèle fr_core_news_sm pour le prétraitement linguistique. L’extraction et la résolution d’entités reposent sur le lexique ontologique, les mécanismes spaCy et RapidFuzz. Une classification explicable par scores sélectionne l’intention, puis des templates contrôlés construisent la requête SPARQL. RDFLib sert à manipuler et vérifier le graphe, et Apache Jena Fuseki exécute les requêtes. Aucun appel à une API de LLM n’est utilisé pour traduire les questions. Sentence Transformers et le modèle multilingue paraphrase-multilingual-MiniLM-L12-v2 servent séparément à la recherche sémantique et au pipeline local alternatif ; il ne faut pas les présenter comme le classifieur principal du traducteur à règles. »

Le traducteur gère un ensemble d’intentions et un vocabulaire de domaine ; il n’est pas un traducteur universel de toutes les questions possibles. Les cas inconnus reviennent à une recherche libre. Les inférences applicatives implémentent un sous-ensemble explicite des axiomes ; la validation OWL DL complète doit être montrée dans Protégé avec un raisonneur compatible, par exemple HermiT.

## Parcours de soutenance (8 à 10 minutes)

1. Annoncer le thème, les objectifs et le cadre de simulation.
2. Ouvrir l’ontologie dans Protégé : classes, relations, attributs, individus, axiome d’équivalence ; lancer le raisonneur et montrer sa sortie réelle.
3. Ouvrir `/ontology` pour montrer l’inventaire connecté au backend et une expression OWL détaillée.
4. En administrateur, créer un identifiant temporaire `SOUTENANCE-001`, modifier son âge, filtrer pour le retrouver, puis le supprimer. Ne pas utiliser un scénario patient conservé pour cette suppression technique.
5. Dans `/explorer`, poser « Quelles molécules contient la pilule combinée ? » ; montrer la requête générée et les résultats.
6. Poser « Quels profils ont une endométriose ? » puis « Quels contraceptifs sont contre-indiqués avec une migraine avec aura ? ».
7. Montrer la chaîne navigateur → FastAPI → traducteur local → Fuseki → JSON → interface, avec Network et Swagger.
8. Montrer les tests, les limites du vocabulaire et la séparation entre inférence, similarité et évaluation pédagogique.

## Vérification reproductible

```bash
docker compose build backend frontend
docker compose run --rm --no-deps backend python -m pytest backend -q
docker compose up -d
```

Les tests d’intégration exécutent les routes et les requêtes réelles sur des graphes RDF isolés ; seul le transport externe Fuseki est remplacé dans ces tests. Un contrôle HTTP sur la pile Docker complète complète cette preuve. La vérification visuelle dépend de la disponibilité du navigateur local.
