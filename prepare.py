import sys
import tomli as tml
import hashlib

print("Processing config.toml, creating secret.js")
try:
    with open('config.toml', mode="rb") as fp:
        cfg = tml.load(fp)
    h = hashlib.new('sha512')    
    h.update(cfg['vuetraccarpw'].encode('utf-8'))
            
    content = f"""import {{ shallowRef }} from 'vue'

export const maps_api_key = shallowRef('{cfg['mapsapikey']}')
export const vuetraccarhash = shallowRef('{h.hexdigest()}')"""

    with open('./frontend/src/secret.js', 'w') as f:
        f.write(content)
except FileNotFoundError:
    print("config.toml not found. Please create it first.")
    sys.exit(1)
