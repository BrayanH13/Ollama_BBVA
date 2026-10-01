import sys

from app.container import ingestion_pipeline

COMMANDS = {"scrape": "scrape", "clean": "clean_step", "index": "index", "all": "run_all"}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"Uso: python -m app.cli [{'|'.join(COMMANDS)}]")
    getattr(ingestion_pipeline(), COMMANDS[sys.argv[1]])()
