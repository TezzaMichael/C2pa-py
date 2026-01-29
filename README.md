# C2PA Python: Trust Validation Tool
This project provides a Python implementation of the C2PA Command Line Tool. It is designed to verify the authenticity and provenance of digital media files (images, videos, audio) by analyzing their C2PA (Coalition for Content Provenance and Authenticity) manifests.

---

## What is C2PA?
C2PA stands for the Coalition for Content Provenance and Authenticity. It is an open technical standard that allows publishers to embed tamper-evident metadata into media files. This metadata allows consumers to verify:

Who created or signed the file.

How it was created (e.g., camera, AI, software).

What changes were made to it over time (the history of edits).

---

## The Trust Method
To determine if a file is "Valid," this tool evaluates the Chain of Trust based on three core values:

#### Integrity (Mathematics):

Ensures that the pixel data has not been altered since the signature was applied. This is verified using cryptographic hashes.

#### Identity (Policy):

Verifies who signed the asset. It checks the digital certificate against a list of trusted authorities (Trust Anchors).

If a file is signed by a "Test" certificate or an unknown entity, it is flagged as Untrusted.

#### Provenance (History):

A recursive check of all "Ingredients" (previous versions or assets used).

Strict Logic: If any ingredient in the history is invalid or created by test software, the entire image is marked as Invalid, even if the final signature is correct.

---

## Configuration Used

To establish trust, this tool connects to the official Content Credentials trust store. By default, it uses:

##### Trust Anchors: https://contentcredentials.org/trust/anchors.pem

##### Allowed List: https://contentcredentials.org/trust/allowed.sha256.txt

##### Trust Config: https://contentcredentials.org/trust/store.cfg

---

## Installation & Setup
Follow these steps to set up the environment and run the tool.

#### 1. Clone the Repository

```bash
git clone https://github.com/TezzaMichael/C2pa-py.git
cd C2pa-py
```
#### 2. Create and Activate Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

##### Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```
##### Windows:

```bash
python -m venv venv
venv\Scripts\activate
```
#### 3. Install Dependencies

```bash
pip install -r requirements
```

---

## Usage
To use the tool, run c2pa-py.py with the path to your image and the desired options.

#### General Help

```bash
python3 c2pa-py.py <image> --help
```

###### Output:

```plaintext
c2patool_py - Python implementation of c2patool

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
    python c2pa.py image.png                       # Print JSON manifest
    python c2pa.py image.png --info                # Show info
    python c2pa.py image.png --tree                # Show tree view
    python c2pa.py image.png --output path   # Save to file
    python c2pa.py image.png trust                 # Verify trust
    python c2pa.py image.png trust --help          # Trust options

ENVIRONMENT VARIABLES:
    C2PATOOL_TRUST_ANCHORS    URL or path to trust anchors PEM file
    C2PATOOL_ALLOWED_LIST     URL or path to allowed certificates list
    C2PATOOL_TRUST_CONFIG     URL or path to trust configuration
```

---

## Trust Verification

The trust command allows you to verify the validity of the file using specific certificate lists.

```bash
python3 c2pa-py.py <image> trust --help
```
###### Output:

```plaintext
Sub-command to configure trust store options, "trust --help for more details"

Usage: python3 c2pa.py <PATH> trust [OPTIONS]

Options:
      --trust_anchors <TRUST_ANCHORS>  URL or path to file containing list of trust anchors in PEM format [env: C2PATOOL_TRUST_ANCHORS=https://contentcredentials.org/trust/anchors.pem]
      --allowed_list <ALLOWED_LIST>    URL or path to file containing specific manifest signing certificates in PEM format to implicitly trust [env: C2PATOOL_ALLOWED_LIST=https://contentcredentials.org/trust/allowed.sha256.txt]
      --trust_config <TRUST_CONFIG>    URL or path to file containing configured EKUs in Oid dot notation [env: C2PATOOL_TRUST_CONFIG=https://contentcredentials.org/trust/store.cfg]
  -h, --help                           Print help
  ```
######  Example: Verify an Image

```bash
python3 c2pa-py.py my_image.jpg trust
```
This will download the latest trust lists, validate the full history of the image, and output the validation state (Valid, Invalid, or Trusted).