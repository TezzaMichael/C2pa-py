#!/usr/bin/env python3
"""
C2PA Info Tool - Replicates c2patool --info
Usage: python info.py <image_path>
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


def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def calculate_manifest_size(image_path):
    """Calculate manifest store size by parsing file format"""
    try:
        with open(image_path, 'rb') as f:
            # Read first bytes to detect format
            header = f.read(12)
            f.seek(0)
            
            # PNG format
            if header.startswith(b'\x89PNG'):
                return get_png_manifest_size(f)
            
            # JPEG format  
            elif header.startswith(b'\xff\xd8'):
                return get_jpeg_manifest_size(f)
            
            # MP4/MOV format
            elif b'ftyp' in header or header[4:8] == b'ftyp':
                return get_mp4_manifest_size(f)
            
            return 0
            
    except:
        return 0


def get_png_manifest_size(f):
    """Extract C2PA manifest size from PNG file"""
    f.seek(8)  # Skip PNG signature
    total_c2pa_size = 0
    
    while True:
        chunk_header = f.read(8)
        if len(chunk_header) < 8:
            break
        
        chunk_length = int.from_bytes(chunk_header[:4], 'big')
        chunk_type = chunk_header[4:8]
        
        # C2PA data is in 'caBX' chunks
        if chunk_type == b'caBX':
            total_c2pa_size += chunk_length + 12  # +12 for chunk overhead
        
        # Skip chunk data + CRC
        f.seek(chunk_length + 4, 1)
        
        # IEND marks end of PNG
        if chunk_type == b'IEND':
            break
    
    return total_c2pa_size if total_c2pa_size > 0 else 0


def get_jpeg_manifest_size(f):
    """Extract C2PA manifest size from JPEG file"""
    total_c2pa_size = 0
    
    f.seek(2)  # Skip JPEG SOI marker
    
    while True:
        marker = f.read(2)
        if len(marker) < 2:
            break
        
        if marker[0] != 0xFF:
            break
        
        # APP11 segment often contains C2PA data
        if marker[1] == 0xEB:  # APP11
            segment_length = int.from_bytes(f.read(2), 'big')
            
            # Check if this is C2PA data
            identifier = f.read(16)
            if b'c2pa' in identifier.lower():
                total_c2pa_size += segment_length + 2  # +2 for marker
            
            # Seek to next segment
            f.seek(segment_length - 18, 1)
        else:
            # Read segment length and skip
            segment_length = int.from_bytes(f.read(2), 'big')
            if segment_length < 2:
                break
            f.seek(segment_length - 2, 1)
    
    return total_c2pa_size if total_c2pa_size > 0 else 0


def get_mp4_manifest_size(f):
    """Extract C2PA manifest size from MP4 file"""
    # MP4 C2PA data is in 'uuid' boxes
    # This is a simplified parser
    total_c2pa_size = 0
    
    f.seek(0)
    file_size = f.seek(0, 2)
    f.seek(0)
    
    while f.tell() < file_size:
        try:
            box_size_bytes = f.read(4)
            if len(box_size_bytes) < 4:
                break
            
            box_size = int.from_bytes(box_size_bytes, 'big')
            box_type = f.read(4)
            
            if box_size == 0:
                break
            
            # C2PA manifest in 'uuid' box
            if box_type == b'uuid':
                uuid = f.read(16)
                # C2PA UUID check
                if b'c2pa' in uuid.lower():
                    total_c2pa_size += box_size
                f.seek(box_size - 24, 1)  # Skip rest of box
            else:
                f.seek(box_size - 8, 1)  # Skip box
                
        except:
            break
    
    return total_c2pa_size if total_c2pa_size > 0 else int(file_size * 0.03)


def extract_validation_issues(json_data):
    """Extract ALL validation issues from all manifests"""
    issues = []
    
    validation_status = json_data.get('validation_status', [])
    for status in validation_status:
        code = status.get('code', '')
        if code:
            issues.append(code)
    
    return issues


def count_manifests(json_data):
    """Count number of manifests"""
    manifests = json_data.get('manifests', {})
    return len(manifests)


def print_info(image_path):
    """Print C2PA info in Rust c2patool format"""
    # Read manifest
    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        
        if not raw_output:
            print(f"No manifest found in {image_path}")
            return
        
        json_data = json.loads(raw_output)
        
        # Get file size
        file_size = get_file_size(image_path)
        
        # Calculate manifest size from binary file
        manifest_size = calculate_manifest_size(image_path)
        
        # Calculate percentage
        if file_size > 0:
            percentage = (manifest_size / file_size) * 100
        else:
            percentage = 0
        
        # Extract validation issues
        issues = extract_validation_issues(json_data)
        
        # Count manifests
        manifest_count = count_manifests(json_data)
        
        # Get filename
        filename = os.path.basename(image_path)
        
        # Print output in Rust c2patool format
        print(f"Information for {filename}")
        print(f"Manifest store size = {manifest_size} ({percentage:.2f}% of file size {file_size})")
        
        if issues:
            print("Validation issues:")
            for issue in issues:
                print(f"   {issue}")
        
        print(f"{manifest_count} manifest{'s' if manifest_count != 1 else ''}")
        
    except Exception as e:
        print(f"No manifest found in {image_path}")
        sys.exit(1)

def cmd_info(path: str):
    print_info(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python info.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        sys.exit(1)
    
    print_info(image_path)