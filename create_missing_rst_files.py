#!/usr/bin/env python3
import yaml
import os

with open('travels.yml', 'r') as f:
    travels = yaml.safe_load(f)

for travel_key, travel_data in travels.items():
    standstills = travel_data.get('standstills', [])
    for standstill in standstills:
        key = standstill.get('key')
        if not key:
            continue
        
        rst_file = f'documents/{key}.rst'
        if not os.path.exists(rst_file):
            address = standstill.get('address', 'Unbekannter Ort')
            print(f"Erstelle {rst_file} für {address}")
            
            with open(rst_file, 'w') as f:
                f.write(f"{address}\n")
                f.write("=" * len(address) + "\n\n")
                f.write("<!-- WordPress Link hier einfügen -->\n")
                f.write('<!-- <a href="https://tagebuch.smallfamilybusiness.net/post-url/">Titel</a> -->\n')

print("Fertig!")
