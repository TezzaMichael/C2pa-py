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

---

## Trust Verification

The trust command allows you to verify the validity of the file using specific certificate lists.

```bash
python3 c2pa-py.py <image> trust --help
```

######  Example: Verify an Image

```bash
python3 c2pa-py.py my_image.jpg trust
```
This will download the latest trust lists, validate the full history of the image, and output the validation state (Valid, Invalid, or Trusted).

---
 
## Comparison with Rust
To demonstrate the accuracy of this Python implementation, a comparison script is included. This tool runs both the official Rust c2patool and this Python tool against a dataset of images to verify parity in validation results.

##### Usage

```bash
python3 compare_result.py <path_to_dataset_folder>
```

###### Output

The script generates two files containing the results:

##### trust_comparison.csv: 
A CSV file containing the raw validation state for every image (Rust vs. Python).

##### trust_report.html: 
An interactive HTML report visualizing the results, highlighting matches/mismatches, and providing accuracy statistics.