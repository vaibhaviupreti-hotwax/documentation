import os
import xml.etree.ElementTree as ET
import json

def find_xml_files(directory):
    xml_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    return xml_files

def extract_entities(xml_files):
    entities = []
    for file in xml_files:
        if 'entity' not in file and 'entitydef' not in file:
            continue
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            for entity in root.findall('.//entity'):
                name = entity.get('entity-name')
                package = entity.get('package')
                if name:
                    entities.append({'name': name, 'package': package, 'file': file})
        except Exception as e:
            pass
    return entities

def extract_data_loaders(xml_files):
    data_files = []
    for file in xml_files:
        if 'data' not in file:
            continue
        try:
            tree = ET.parse(file)
            root = tree.getroot()
            # Moqui data format usually has <entity-facade-xml type="...">
            load_type = root.get('type')
            if load_type:
                data_files.append({'file': file, 'type': load_type, 'root': root.tag})
        except Exception as e:
            pass
    return data_files

def main():
    setup_a_dir = '/home/vaibhaviupreti/1-HW/12-new-store-setup/moqui-framework/runtime/component'
    setup_b_dir = '/home/vaibhaviupreti/1-HW/12-new-store-setup/sandbox/ofbiz-oms/applications'
    
    setup_a_xml = find_xml_files(setup_a_dir)
    setup_b_xml = find_xml_files(setup_b_dir)
    
    setup_a_entities = extract_entities(setup_a_xml)
    setup_b_entities = extract_entities(setup_b_xml)
    
    setup_a_data = extract_data_loaders(setup_a_xml)
    
    out = {
        'setup_a_entity_count': len(setup_a_entities),
        'setup_b_entity_count': len(setup_b_entities),
        'setup_a_data_files': len(setup_a_data),
        'setup_a_entities_sample': setup_a_entities[:5],
        'setup_a_data_sample': setup_a_data[:5]
    }
    
    with open('/home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/inventory_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
        
    # Also dump full lists to be read if needed
    with open('/home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/setup_a_entities.json', 'w') as f:
        json.dump(setup_a_entities, f, indent=2)
        
    with open('/home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/setup_b_entities.json', 'w') as f:
        json.dump(setup_b_entities, f, indent=2)

    with open('/home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/setup_a_data.json', 'w') as f:
        json.dump(setup_a_data, f, indent=2)

if __name__ == '__main__':
    main()
