import os
import xml.etree.ElementTree as ET
import json
from collections import defaultdict

def find_files(directory, ext):
    found = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(ext):
                found.append(os.path.join(root, file))
    return found

def analyze_architecture(base_dir):
    xml_files = find_files(base_dir, '.xml')
    
    # 1. Extract Entities
    entities = {}
    for f in xml_files:
        if 'entity' in f or 'entitydef' in f:
            try:
                tree = ET.parse(f)
                root = tree.getroot()
                for e in root.findall('.//entity'):
                    name = e.get('entity-name')
                    if name:
                        entities[name] = {
                            'package': e.get('package'),
                            'file': f,
                            'load_types': set(),
                            'loaded_by_files': [],
                            'relationships': [],
                            'tier': 'Unknown',
                            'confidence': 0,
                            'evidence': []
                        }
            except Exception:
                pass

    # 2. Extract Data Loaders
    for f in xml_files:
        if 'data' in f:
            try:
                tree = ET.parse(f)
                root = tree.getroot()
                load_type = root.get('type')
                
                # In Moqui, root is <entity-facade-xml>. Children are entity names.
                # In OFBiz, root is <entity-engine-xml>. Children are entity names.
                for child in root:
                    # Strip namespace if any, usually just the tag name is the entity name
                    tag = child.tag.split('}')[-1]
                    # Sometimes tag is full package name, e.g. org.apache.ofbiz.party.party.Party
                    ent_name = tag.split('.')[-1]
                    
                    if ent_name in entities:
                        if load_type:
                            entities[ent_name]['load_types'].add(load_type)
                        entities[ent_name]['loaded_by_files'].append(f)
            except Exception:
                pass
                
    # 3. Classify Entities
    for name, data in entities.items():
        name_lower = name.lower()
        evidence = data['evidence']
        score_t1 = 0
        score_t2 = 0
        score_t3 = 0
        
        # Semantic rules
        if any(x in name_lower for x in ['type', 'status', 'enum', 'uom', 'geo', 'system', 'preference', 'permission']):
            score_t1 += 40
            evidence.append("Semantic match for Tier 1 (Common Framework Data)")
        elif any(x in name_lower for x in ['store', 'facility', 'config', 'setting', 'mapping', 'rule', 'catalog', 'category']):
            score_t2 += 40
            evidence.append("Semantic match for Tier 2 (Configurable ERP Data)")
        elif any(x in name_lower for x in ['product', 'party', 'order', 'inventory', 'shipment', 'invoice', 'return', 'cart', 'payment']):
            score_t3 += 40
            evidence.append("Semantic match for Tier 3 (Highly Mutable Business Data)")
            
        # Data Loader rules
        load_types = data['load_types']
        if any(t in load_types for t in ['seed', 'seed-initial', 'install']):
            score_t1 += 50
            evidence.append(f"Loaded by framework during initial setup ({', '.join(load_types)})")
        if 'ext-seed' in load_types:
            score_t2 += 30
            evidence.append("Loaded by implementers via ext-seed")
        if 'ext' in load_types or 'ext-data' in load_types:
            score_t3 += 20
            evidence.append("Loaded via runtime or demo ext data")
            
        # Shopify influence
        if 'shopify' in name_lower or 'shopify' in str(data['package']).lower():
            if score_t3 > score_t2:
                pass # transactional
            else:
                score_t2 += 30
                evidence.append("Shopify integration entity (Configurable bias)")
                
        # Assignment
        if score_t1 > score_t2 and score_t1 > score_t3:
            data['tier'] = 'Tier 1 - Common Framework Data'
            data['confidence'] = min(100, score_t1)
        elif score_t2 > score_t1 and score_t2 > score_t3:
            data['tier'] = 'Tier 2 - Configurable ERP Data'
            data['confidence'] = min(100, score_t2)
        elif score_t3 > score_t1 and score_t3 > score_t2:
            data['tier'] = 'Tier 3 - Highly Mutable Business Data'
            data['confidence'] = min(100, score_t3)
        else:
            data['tier'] = 'Unclassified'
            data['confidence'] = 0
            
    return entities

def write_report(title, entities, output_file):
    with open(output_file, 'w') as f:
        f.write(f"# {title}\n\n")
        
        f.write("## Entity Inventory & Classification Catalog\n\n")
        f.write("| Entity | Tier | Confidence | Evidence |\n")
        f.write("|---|---|---|---|\n")
        
        # Sort by tier, then name
        sorted_ents = sorted(entities.items(), key=lambda x: (x[1]['tier'], x[0]))
        for name, data in sorted_ents:
            evidence_str = "; ".join(data['evidence']) if data['evidence'] else "No clear evidence"
            f.write(f"| {name} | {data['tier']} | {data['confidence']} | {evidence_str} |\n")
            
        f.write("\n## Data Loading Strategy\n")
        f.write("Based on analysis of XML data files, the following load types were observed across entities:\n")
        load_type_counts = defaultdict(int)
        for data in entities.values():
            for lt in data['load_types']:
                load_type_counts[lt] += 1
        for lt, count in load_type_counts.items():
            f.write(f"- `{lt}`: {count} entities\n")

def main():
    base_dir = '/home/vaibhaviupreti/1-HW/12-new-store-setup'
    out_dir = '/home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch'
    
    setup_a_dir = os.path.join(base_dir, 'moqui-framework', 'runtime', 'component')
    setup_b_dir = os.path.join(base_dir, 'sandbox', 'ofbiz-oms', 'applications')
    
    print("Analyzing Setup A...")
    entities_a = analyze_architecture(setup_a_dir)
    write_report("Deliverable 8 — Moqui-Only Architecture Report", entities_a, os.path.join(out_dir, 'deliverable_8.md'))
    
    print("Analyzing Setup B...")
    entities_b = analyze_architecture(setup_b_dir)
    write_report("Deliverable 7 — Legacy Integrated Architecture Report", entities_b, os.path.join(out_dir, 'deliverable_7.md'))
    
    # Comparison
    print("Generating Comparison...")
    with open(os.path.join(out_dir, 'deliverable_9.md'), 'w') as f:
        f.write("# Deliverable 9 — Architecture Comparison Report\n\n")
        f.write("| Entity | Setup A Tier | Setup B Tier | Impact |\n")
        f.write("|---|---|---|---|\n")
        
        all_names = set(entities_a.keys()).union(set(entities_b.keys()))
        for name in sorted(all_names):
            tier_a = entities_a[name]['tier'] if name in entities_a else "Missing"
            tier_b = entities_b[name]['tier'] if name in entities_b else "Missing"
            
            if tier_a != tier_b:
                impact = "Migration Impact" if tier_a != "Missing" and tier_b != "Missing" else ("New in A" if tier_a != "Missing" else "Deprecated in A")
                f.write(f"| {name} | {tier_a} | {tier_b} | {impact} |\n")

    print("Done. Reports generated in scratch directory.")

if __name__ == '__main__':
    main()
