"""
c2patool_py - Python implementation of c2patool
Replicates Rust c2patool behavior using c2pa-python

Usage:
    python c2pa.py <PATH>                              # Print JSON to stdout
    python c2pa.py <PATH> --info                       # Show manifest info
    python c2pa.py <PATH> --tree                       # Show tree view
    python c2pa.py <PATH> --detailed                   # Detailed JSON output
    python c2pa.py <PATH> --ingredient                 # Extract ingredients
    python c2pa.py <PATH> --output <FOLDER>            # Save JSON to file
    python c2pa.py <PATH> trust                        # Trust verification
    python c2pa.py <PATH> trust --help                 # Trust options help
"""

import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import c2pa
from commands.trust import cmd_trust, print_trust_help
from commands.info import cmd_info
from commands.tree import cmd_tree
from commands.detailed import cmd_detailed
from commands.ingredient import cmd_ingredient
from commands.output import cmd_output




def cmd_default(path: str):
    """Default command: print JSON manifest with validation"""
    try:
        reader = c2pa.Reader(path)
        raw_output = reader.json()

        if not raw_output:
            print(f"No manifest found in {path}")
            return
        
        json_data = json.loads(raw_output)
        print(json.dumps(json_data, indent=2))
    except Exception:
        print(f"No manifest found in {path}")
        sys.exit(1)

def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python c2pa.py <PATH> [OPTIONS|COMMAND]")
        print("Try: python c2pa.py --help")
        sys.exit(1)

    if sys.argv[1] in ('--help', '-h'):
        print_help()
        sys.exit(0)
    elif sys.argv[1] == 'trust' and sys.argv[2] in ('--help', '-h'):
        print_trust_help()
        sys.exit(0)

    # Parse arguments manually for c2patool-like behavior
    path = sys.argv[1]
    args = sys.argv[2:]
    
    # Check if path exists
    if not os.path.exists(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse options and commands
    command = None
    trust_opts = {}
    
    i = 0
    if len(args) == 0:
        cmd_default(path)

    while i < len(args):
        arg = args[i]
        
        if arg == '--output':
            if i + 1 < len(args):
                cmd_output(path, args[i + 1])
            else:
                print("Error: --output requires a value", file=sys.stderr)
                sys.exit(1)
        elif arg == '--info':
            cmd_info(path)
        elif arg == '--tree':
            cmd_tree(path)
        elif arg == '--detailed':
            cmd_detailed(path)
        elif arg == '--ingredient':
            cmd_ingredient(path)
        elif arg == 'trust':
            i += 1

            while i < len(args):
                if args[i] == '--help':
                    print_trust_help()
                    sys.exit(0)
                elif args[i] == '--trust_anchors' and i + 1 < len(args):
                    trust_opts['trust_anchors'] = args[i + 1]
                    i += 2
                elif args[i] == '--allowed_list' and i + 1 < len(args):
                    trust_opts['allowed_list'] = args[i + 1]
                    i += 2
                elif args[i] == '--trust_config' and i + 1 < len(args):
                    trust_opts['trust_config'] = args[i + 1]
                    i += 2
                else:
                    print(f"Warning: Unknown trust option: {args[i]}", file=sys.stderr)
                    print("Use 'trust --help' for available options.", file=sys.stderr)
                    sys.exit(1)
            
            cmd_trust(path, trust_opts)
            
        elif arg == '--help' or arg == '-h':
            print_help()
            sys.exit(0)
        else:
            print(f"Warning: Unknown option: {arg}", file=sys.stderr)
            print("Use --help for usage information.", file=sys.stderr)
            sys.exit(1)
            
        sys.exit(0)
    

def print_help():
    """Print main help message"""
    help_text = """c2patool_py - Python implementation of c2patool

USAGE:
    python main.py <PATH> [OPTIONS|COMMAND]

ARGS:
    <PATH>    Path to image file with C2PA manifest

OPTIONS:
    --info          Show manifest store information
    --tree          Show manifest tree structure
    --detailed      Show detailed C2PA-formatted JSON
    --ingredient    Extract ingredient information
    --output <FILE> Save output to file instead of stdout
    --help, -h      Print this help message

COMMANDS:
    trust           Verify trust of C2PA manifest (use 'trust --help' for options)

EXAMPLES:
    python c2pa.py image.png                           # Print JSON manifest
    python c2pa.py image.png --info                    # Show info
    python c2pa.py image.png --tree                    # Show tree view
    python c2pa.py image.png --output path             # Save to file
    python c2pa.py image.png trust                     # Verify trust
    python c2pa.py image.png trust --help              # Trust options

ENVIRONMENT VARIABLES:
    C2PATOOL_TRUST_ANCHORS    URL or path to trust anchors PEM file
    C2PATOOL_ALLOWED_LIST     URL or path to allowed certificates list
    C2PATOOL_TRUST_CONFIG     URL or path to trust configuration
"""
    print(help_text)


if __name__ == "__main__":
    main()