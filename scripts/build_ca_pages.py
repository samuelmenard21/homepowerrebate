#!/usr/bin/env python3
"""California city hubs and category pages (/us/ca/<metro>/<city>/...). The engine is scripts/city_pages.py; settings are the
"city_pages" block for ca in data/regions.json; cities, metro folders and utilities are in scripts/ca_cities.py; prose is in
data/ca/pages/<city>/<category>.json. Usage: python3 scripts/build_ca_pages.py [city ...]

Other scripts import shared pieces from here (BASE, FACTS, AUTHOR, CSS, card, words, LABEL); they now live in page_kit.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402
from page_kit import AUTHOR, BASE, CSS, FACTS, PILL, card, words  # noqa: E402,F401  (re-exported for older importers)

LABEL = {"heat-pump": "Heat Pump", "water-heater": "Water Heater", "solar": "Solar", "battery": "Battery Storage", "ev-charger": "EV Charger", "insulation": "Insulation",
         "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "windows-doors": "Windows & Doors", "hrv": "HRV & Ventilation"}

if __name__ == "__main__":
    city_pages.main("ca")
