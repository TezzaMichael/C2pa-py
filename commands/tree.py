#!/usr/bin/env python3
"""
C2PA Tree View Tool - Replicates c2patool --tree output
Usage: python tree.py <image_path>
"""

import os
import json
import sys
import requests
import c2pa



def print_assertions(assertions, prefix=""):
    """Print assertions with tree formatting"""
    for i, assertion in enumerate(assertions):
        is_last = (i == len(assertions) - 1)
        
        # Get assertion label
        label = assertion.get('label', 'unknown')
        
        # Tree characters
        if is_last:
            print(f"{prefix}└── Assertion:{label}")
        else:
            print(f"{prefix}├── Assertion:{label}")


def print_ingredient_tree(ingredient, manifests, prefix="", is_last=False):
    """Recursively print ingredient tree"""
    
    # Get ingredient title and manifest reference
    title = ingredient.get('title', 'unknown')
    active_manifest = ingredient.get('active_manifest', '')
    
    # Tree characters
    connector = "└──" if is_last else "├──"
    extension = "    " if is_last else "│   "
    
    # Print ingredient
    print(f"{prefix}{connector} Asset:{title}, Manifest:{active_manifest}")
    
    # Get the ingredient's manifest data
    if active_manifest in manifests:
        manifest_data = manifests[active_manifest]
        
        # Print assertions for this ingredient
        assertions = manifest_data.get('assertions', [])
        
        # Filter assertions
        visible_assertions = [a for a in assertions 
                             if not a.get('label', '').startswith('c2pa.hash')]
        
        if visible_assertions:
            print_assertions(visible_assertions, prefix + extension)
        
        # Recursively print nested ingredients
        nested_ingredients = manifest_data.get('ingredients', [])
        if nested_ingredients:
            for i, nested_ing in enumerate(nested_ingredients):
                is_last_nested = (i == len(nested_ingredients) - 1)
                print_ingredient_tree(nested_ing, manifests, 
                                    prefix + extension, is_last_nested)


def print_tree(image_path):
    """Print C2PA tree view"""
    
    # Read manifest
    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        
        if not raw_output:
            print(f"No manifest found in {image_path}")
            return
        
        json_data = json.loads(raw_output)
        
        # Get filename
        filename = os.path.basename(image_path)
        
        # Get active manifest
        active_manifest_id = json_data.get('active_manifest', '')
        manifests = json_data.get('manifests', {})
        
        if not active_manifest_id or active_manifest_id not in manifests:
            print("No active manifest found")
            return
        
        # Get active manifest data
        active_manifest = manifests[active_manifest_id]
        
        # Print tree header
        print("Tree View:")
        print(f" Asset:{filename}, Manifest:{active_manifest_id}")
        
        # Get assertions from active manifest
        assertions = active_manifest.get('assertions', [])
        
        # Filter out hash assertions
        visible_assertions = [a for a in assertions 
                             if not a.get('label', '').startswith('c2pa.hash')]
        
        # Get ingredients
        ingredients = active_manifest.get('ingredients', [])
        
        # Print assertions
        if visible_assertions and not ingredients:
            # Only assertions, no ingredients
            print_assertions(visible_assertions, "")
        elif visible_assertions and ingredients:
            # Both assertions and ingredients
            for i, assertion in enumerate(visible_assertions):
                label = assertion.get('label', 'unknown')
                print(f"├── Assertion:{label}")
        
        # Print ingredients tree
        if ingredients:
            for i, ingredient in enumerate(ingredients):
                is_last = (i == len(ingredients) - 1)
                print_ingredient_tree(ingredient, manifests, "", is_last)
        
    except Exception:
        print(f"No manifest found in {image_path}")
        sys.exit(1)


def cmd_tree(path: str):
    print_tree(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tree.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    print_tree(image_path)