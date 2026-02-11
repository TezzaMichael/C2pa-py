#!/usr/bin/env python3
"""
C2PA Ingredient View Tool - Replicates c2patool --ingredient output
Usage: python ingredient.py <image_path>
"""

import os
import json
import sys
import requests
import c2pa



def print_ingredient(image_path):
    """Print C2PA ingredient information"""
    
    # Read manifest
    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        
        if not raw_output:
            print(f"No manifest found in {image_path}")
            return
        
        json_data = json.loads(raw_output)
        
        # Build ingredient output
        ingredient_output = build_ingredient_output(image_path, json_data)
        
        # Print as formatted JSON
        print(json.dumps(ingredient_output, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error reading manifest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def build_ingredient_output(image_path, json_data):
    """Build ingredient output structure"""
    
    output = {}
    
    # Add basic file info
    filename = os.path.basename(image_path)
    output['title'] = filename
    
    # Detect format from file extension
    ext = os.path.splitext(filename)[1].lower()
    format_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.pdf': 'application/pdf'
    }
    output['format'] = format_map.get(ext, 'application/octet-stream')
    
    # Add instance_id (generate if not present)
    active_manifest_id = json_data.get('active_manifest', '')
    manifests = json_data.get('manifests', {})
    
    if active_manifest_id in manifests:
        active_manifest = manifests[active_manifest_id]
        instance_id = active_manifest.get('instance_id', '')
        if instance_id:
            output['instance_id'] = instance_id
        else:
            # Generate instance_id from filename
            output['instance_id'] = f"xmp:iid:{filename.replace('.', '-')}"
    
    # Add thumbnail info
    thumbnail_filename = filename.replace(ext, '.jpg')
    output['thumbnail'] = {
        'format': 'image/jpeg',
        'identifier': thumbnail_filename
    }
    
    # Add relationship
    output['relationship'] = 'componentOf'
    
    # Add active_manifest
    output['active_manifest'] = active_manifest_id
    
    # Add validation_status
    if 'validation_status' in json_data:
        output['validation_status'] = json_data['validation_status']
    
    # Add validation_results
    if 'validation_results' in json_data:
        output['validation_results'] = json_data['validation_results']
    
    # Add manifest_data
    output['manifest_data'] = {
        'format': 'application/c2pa',
        'identifier': 'manifest_data.c2pa'
    }
    
    return output

def cmd_ingredient(image_path):
    print_ingredient(image_path)
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingredient.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    print_ingredient(image_path)