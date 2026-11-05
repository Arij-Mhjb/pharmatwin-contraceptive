"""Load the ontology, then start the production API process."""

import uvicorn

from backend.scripts.load_ontology import main as load_ontology


def main() -> None:
    load_ontology()
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
