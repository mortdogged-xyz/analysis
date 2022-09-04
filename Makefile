MAIN = poetry run python src/main.py

scrape:
	$(MAIN) scrape

import:
	$(MAIN) import
