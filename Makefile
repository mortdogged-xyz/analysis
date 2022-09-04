MAIN = poetry run python src/main.py

scrape:
	$(MAIN) scrape

export:
	$(MAIN) export
