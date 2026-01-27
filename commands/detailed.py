#!/usr/bin/env python3
"""
C2PA Detailed View Tool - Replicates c2patool --detailed
Usage: python3 detailed.py <image_path>
"""

import os
import json
import sys
import requests
import c2pa


def print_detailed(image_path):
    """Print detailed C2PA manifest view"""
    
    try: 
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
            
        if not raw_output:
            print(f"No manifest found in {image_path}")
            return
        json_data = json.loads(raw_output)
            
        # Convert to detailed format (matching Rust output structure)
        detailed_output = convert_to_detailed_format(json_data)
            
        # Print as formatted JSON
        print(json.dumps(detailed_output, indent=2, ensure_ascii=False))
    except Exception:
        print(f"No manifest found in {image_path}")
        sys.exit(1)


def convert_to_detailed_format(json_data):
    """Convert manifest to detailed format matching Rust c2patool output"""
    
    detailed = {}
    
    # Add active_manifest
    if 'active_manifest' in json_data:
        detailed['active_manifest'] = json_data['active_manifest']
    
    # Convert manifests to detailed format
    if 'manifests' in json_data:
        detailed['manifests'] = {}
        
        for manifest_id, manifest_data in json_data['manifests'].items():
            detailed_manifest = {}
            
            # Add claim structure
            claim = {}
            
            if 'instance_id' in manifest_data:
                claim['instanceID'] = manifest_data['instance_id']
            
            if 'claim_generator_info' in manifest_data:
                claim_gen = manifest_data['claim_generator_info']
                if isinstance(claim_gen, list) and claim_gen:
                    claim['claim_generator_info'] = claim_gen[0]
                else:
                    claim['claim_generator_info'] = claim_gen
            
            # Add signature reference
            claim['signature'] = f"self#jumbf=/c2pa/{manifest_id}/c2pa.signature"
            
            # Add created_assertions from assertions
            if 'assertions' in manifest_data:
                created_assertions = []
                for assertion in manifest_data['assertions']:
                    label = assertion.get('label', '')
                    created_assertions.append({
                        'url': f"self#jumbf=c2pa.assertions/{label}",
                        'hash': ''  # Hash would need to be calculated
                    })
                claim['created_assertions'] = created_assertions
            
            # Add title
            if 'title' in manifest_data:
                claim['dc:title'] = manifest_data['title']
            
            claim['alg'] = 'sha256'
            
            detailed_manifest['claim'] = claim
            
            # Add assertion_store
            assertion_store = {}
            if 'assertions' in manifest_data:
                for assertion in manifest_data['assertions']:
                    label = assertion.get('label', '')
                    data = assertion.get('data', {})
                    assertion_store[label] = data
            
            detailed_manifest['assertion_store'] = assertion_store
            
            # Add signature info
            if 'signature_info' in manifest_data:
                sig_info = manifest_data['signature_info']
                detailed_manifest['signature'] = {
                    'alg': sig_info.get('alg', '').lower(),
                    'issuer': sig_info.get('issuer', ''),
                    'common_name': sig_info.get('common_name', '')
                }
            
            detailed['manifests'][manifest_id] = detailed_manifest
    
    # Add validation_results
    if 'validation_results' in json_data:
        detailed['validation_results'] = json_data['validation_results']
    
    # Add validation_state
    if 'validation_state' in json_data:
        detailed['validation_state'] = json_data['validation_state']
    
    return detailed

def cmd_detailed(image_path):
    print_detailed(image_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detailed.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    print_detailed(image_path)