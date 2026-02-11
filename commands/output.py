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
    # Read manifest
    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        
        if not raw_output:
            print(f"No manifest found in {image_path}")
            sys.exit(1)
        
        json_data = json.loads(raw_output)
        
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
        print(f"No manifest found in {image_path}")
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