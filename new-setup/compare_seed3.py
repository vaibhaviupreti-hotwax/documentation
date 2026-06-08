import os
import xml.etree.ElementTree as ET
from collections import defaultdict

base_dir = '/home/vaibhaviupreti/1-HW/12-new-store-setup/moqui-framework'
ext_seed_dir = '/home/vaibhaviupreti/1-HW/12-new-store-setup/moqui-framework/runtime/component/gorjana-maarg/data/'

def extract_entities(directory, is_ext=False):
    entities = defaultdict(list)
    for root_dir, _, files in os.walk(directory):
        if is_ext == False and 'gorjana-maarg' in root_dir:
            continue
        for file in files:
            if file.endswith('.xml'):
                path = os.path.join(root_dir, file)
                try:
                    tree = ET.parse(path)
                    root = tree.getroot()
                    if root.tag == 'entity-facade-xml':
                        # Optionally check type="seed" for seed
                        if not is_ext and root.get('type') != 'seed' and root.get('type') != 'seed-initial':
                            continue
                        for child in root:
                            if not isinstance(child.tag, str): continue
                            if child.tag == 'entity-facade-xml': continue
                            
                            entity_name = child.tag.split('.')[-1]
                            keys = []
                            if entity_name == 'StatusItem':
                                keys.append(child.get('statusId'))
                            elif entity_name == 'Enumeration':
                                keys.append(child.get('enumId'))
                            elif entity_name == 'ProductStore':
                                keys.append(child.get('productStoreId'))
                            else:
                                keys.append(str(child.attrib))
                            entities[entity_name].append(keys[0])
                except Exception as e:
                    pass
    return entities

seed_entities = extract_entities(base_dir, is_ext=False)
ext_seed_entities = extract_entities(ext_seed_dir, is_ext=True)

all_entities = set(seed_entities.keys()).union(set(ext_seed_entities.keys()))

print("Comparison:\n")
for entity in sorted(all_entities):
    if entity in seed_entities and entity in ext_seed_entities:
        print(f"[{entity}] is in BOTH")
        seed_pks = set(seed_entities[entity])
        ext_pks = set(ext_seed_entities[entity])
        overlap = seed_pks.intersection(ext_pks)
        if overlap:
            print(f"  -> OVERLAP FOUND: {overlap}")
        else:
            print(f"  -> NO OVERLAP")
            print(f"  -> Seed samples: {list(seed_pks)[:3]}")
            print(f"  -> Ext-seed samples: {list(ext_pks)[:3]}")

