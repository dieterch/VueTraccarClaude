from pprint import pprint as pp
import tomli


cfgfile = "../config.toml"
with open(cfgfile, mode="rb") as fp:
    cfg = tomli.load(fp)
    
pp(cfg)