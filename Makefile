PYTHON ?= python3
AMAP_KEY ?=

.PHONY: run demo demo-page

run:
	PYTHON=$(PYTHON) AMAP_KEY=$(AMAP_KEY) bash scripts/run_all.sh

demo:
	AMAP_KEY=$(AMAP_KEY) $(PYTHON) scripts/04_build_map.py \
		--trips sample/trips.csv \
		--locations sample/locations.csv \
		--output outputs/trip-map.html

demo-page:
	$(PYTHON) scripts/05_build_demo.py
