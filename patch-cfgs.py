import yaml
import sys
import os

if len(sys.argv) == 2:
    db = os.path.abspath(sys.argv[1])
    cfg = 'src/report/config/database.yml'

    with open(cfg, 'r') as cfile:
        root = yaml.safe_load(cfile)
    
    root['development']['database'] = db
    root['test']['database'] = db
    root['production']['database'] = db

    with open(cfg, 'w') as cfile:
        cfile.write(yaml.dump(root, default_flow_style=False))
else:
    print("Usage: "+sys.argv[0]+" <path to database>")
