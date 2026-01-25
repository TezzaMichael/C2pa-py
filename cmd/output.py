#!/usr/bin/env python3
"""
C2PA Output Tool - Replicates c2patool --output <dir>
Usage: python output.py <image_path> <output_dir>
"""

import os
import json
import sys
import requests
import c2pa

DEFAULT_ANCHORS = 'https://contentcredentials.org/trust/anchors.pem'
DEFAULT_ALLOWED = 'https://contentcredentials.org/trust/allowed.sha256.txt'
DEFAULT_CONFIG = 'https://contentcredentials.org/trust/store.cfg'

CONFIG_URLS = {
    "anchors": os.environ.get('C2PATOOL_TRUST_ANCHORS', DEFAULT_ANCHORS),
    "allowed": os.environ.get('C2PATOOL_ALLOWED_LIST', DEFAULT_ALLOWED),
    "config": os.environ.get('C2PATOOL_TRUST_CONFIG', DEFAULT_CONFIG)
}

FILES = {
    "anchors": "anchors.pem",
    "allowed": "allowed.sha256.txt",
    "config": "store.cfg"
}


def download_trust_files():
    """Download trust configuration files if not present"""
    for key, url in CONFIG_URLS.items():
        if not os.path.exists(FILES[key]):
            try:
                r = requests.get(url, timeout=10)
                with open(FILES[key], 'wb') as f:
                    f.write(r.content)
            except:
                pass


def read_file_content(filename):
    """Read file content"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def extract_manifest_only(json_data):
    """Extract just the manifest structure (without validation)"""
    manifest = {}
    
    if 'active_manifest' in json_data:
        manifest['active_manifest'] = json_data['active_manifest']
    
    if 'manifests' in json_data:
        manifest['manifests'] = json_data['manifests']
    
    return manifest


def save_output(image_path, output_dir):
    """Save manifest to output directory"""
    
    # Download trust files
    download_trust_files()
    
    # Load trust configuration
    anchors = read_file_content(FILES["anchors"])
    allowed = read_file_content(FILES["allowed"])
    cfg = read_file_content(FILES["config"])
    
    settings = {"verify": {"verify_trust": True}, "trust": {}}
    if anchors:
        settings["trust"]["trust_anchors"] = anchors
    if allowed:
        settings["trust"]["allowed_list"] = allowed
    if cfg:
        settings["trust"]["trust_config"] = cfg
    
    # Load settings into c2pa
    try:
        if hasattr(c2pa, 'load_settings'):
            c2pa.load_settings(json.dumps(settings))
    except:
        pass
    
    # Read manifest
    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        
        if not raw_output:
            print(f"No manifest found in {image_path}")
            sys.exit(1)
        
        # Parse JSON
        if isinstance(raw_output, str):
            json_data = json.loads(raw_output)
        elif isinstance(raw_output, dict):
            json_data = raw_output
        else:
            print(f"Invalid manifest data")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save manifest_store.json (full data with validation)
        manifest_store_path = os.path.join(output_dir, 'manifest_store.json')
        with open(manifest_store_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Save manifest.json (just manifests, no validation)
        manifest_only = extract_manifest_only(json_data)
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_only, f, indent=2, ensure_ascii=False)
        
        print(f'Manifest report written to the directory "{output_dir}"')
        
    except Exception as e:
        print(f"Error processing manifest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_output(image_path, output_dir):
    save_output(image_path, output_dir)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python output.py <image_path> <output_dir>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    save_output(image_path, output_dir)