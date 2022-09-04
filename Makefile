MAIN = poetry run python src/main.py

scrape:
	$(MAIN) scrape

export:
	$(MAIN) export

load:
	$(MAIN) load

jupyter:
	poetry run jupyter notebook
