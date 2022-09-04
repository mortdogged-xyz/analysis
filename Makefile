MAIN = poetry run python src/main.py

scrape:
	$(MAIN) scrape

export:
	$(MAIN) export

load:
	$(MAIN) load

scrape-loop:
	$(MAKE) scrape export
	$(shell sleep 120)
	$(MAKE) scrape-loop

jupyter:
	poetry run jupyter notebook
