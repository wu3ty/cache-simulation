PYTHON_VERSION?=python3

.PHONE run:
run:
	$(PYTHON_VERSION) cache_sim.py -f debug.csv -s 2 -t 1000

.PHONE test:
test:
	pytest
