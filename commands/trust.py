import os
import json
import requests
import c2pa
import sys

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
    """
    Download trust files if they do not exist locally
    """
    for key, url in CONFIG_URLS.items():
        if not os.path.exists(FILES[key]):
            try:
                r = requests.get(url)
                with open(FILES[key], 'wb') as f:
                    f.write(r.content)
            except:
                pass

def read_file_content(filename):
    """
    Read content of a file if it exists
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def recursive_find_errors(data, invalid_codes):
    """
    Find if any invalid error codes are present in the data structure
    """
    if isinstance(data, dict):
        if "code" in data and isinstance(data["code"], str):
            code_val = data["code"]
            for bad_code in invalid_codes:
                if bad_code in code_val:
                    return True, f"Found fatal error '{code_val}' in structure."
        for key, value in data.items():
            found, reason = recursive_find_errors(value, invalid_codes)
            if found: return True, reason
    elif isinstance(data, list):
        for item in data:
            found, reason = recursive_find_errors(item, invalid_codes)
            if found: return True, reason
    return False, None

def check_manifest(json_data):
    """
    Check history integrity with strict rules:
    1. No ingredient created by Test software
    2. No ingredient signed by Test certificates
    3. No ingredient marked as Untrusted
    4. No fatal errors in entire manifest
    5. No ingredient delta failures
    """
    active_id = json_data.get("active_manifest", "")
    manifests = json_data.get("manifests", {})

    for man_id, content in manifests.items():
        
        # check manifest not active
        if man_id != active_id:
            
            generator = content.get("claim_generator", "").lower()
            
            # 1. Check if generator is Test software
            if "c2pa testing" in generator or "make_test_images" in generator or "testapp" in generator:
                return False, f"Ingredient '{man_id}' created by Test software: {content.get('claim_generator')}."

            # 2. Check if ingredient is Untrusted
            status = content.get("validation_status", [])
            for err in status:
                if err.get("code") == "signingCredential.untrusted":
                    return False, f"Ingredient '{man_id}' is Untrusted (Chain Broken)."
            
            # 3. Check signature issuer for Test Certificates
            sig_info = content.get("signature_info", {})
            issuer = sig_info.get("issuer", "")
            cn = sig_info.get("common_name", "")
            if "Test Signing" in issuer or "Test Signing" in cn:
                 return False, f"Ingredient '{man_id}' signed by Test Certificate."

    ERRORS = [
        "mismatch",                
        "signingCredential.invalid", 
        "signingCredential.revoked"
    ]

    # 4. Check entire manifest for fatal errors
    found_error, reason = recursive_find_errors(json_data, ERRORS)
    if found_error:
        return False, reason

    # 5. Check ingredient deltas for failures
    val_results = json_data.get("validation_results", {})
    deltas = val_results.get("ingredientDeltas", [])
    #("Deltas:", deltas)
    for delta in deltas:
        failures = delta.get("validationDeltas", {}).get("failure", [])
        if failures:
             return False, f"Ingredient Delta failure: {failures[0].get('code')}"

    return True, "History clean"

def is_valid(json_data):
    """
    Check if active manifest is valid
    """
    active_manifest = json_data.get("validation_results", {}).get("activeManifest", {})
    successes = active_manifest.get("success", [])
    has_valid_sig = any(s.get("code") == "claimSignature.validated" for s in successes)
    
    if not has_valid_sig:
        return False

    errors = json_data.get("validation_status", [])
    for err in errors:
        code = err.get("code", "")
        #print("Active manifest error code:", code)
        if code != "signingCredential.untrusted":
            return False
            
    return True

def update_validation_state(json_data):
    """
    Update validation state based on history integrity and current state
    """
    current_state = json_data.get("validation_state")

    is_history_clean, reason = check_manifest(json_data)
    
    if not is_history_clean:
        json_data["validation_state"] = "Invalid"
        if "validation_status" not in json_data:
            json_data["validation_status"] = []
        
        if not any(e.get("explanation") == reason for e in json_data["validation_status"]):
            json_data["validation_status"].append({
                "code": "custom.historyCheckFailed",
                "explanation": reason
            })
        return json_data

    # If history is clean and current state is Invalid, check if we can upgrade to Valid
    if current_state == "Invalid":
        if is_valid(json_data):
            json_data["validation_state"] = "Valid"

    return json_data

def main(path, trust_opts={}):
    # trust_opts keys: trust_anchors, allowed_list, trust_config
    if trust_opts.get("trust_anchors"):
        CONFIG_URLS["anchors"] = trust_opts["trust_anchors"]
    if trust_opts.get("allowed_list"):
        CONFIG_URLS["allowed"] = trust_opts["allowed_list"]
    if trust_opts.get("trust_config"):
        CONFIG_URLS["config"] = trust_opts["trust_config"]
        
    download_trust_files()

    anchors = read_file_content(FILES["anchors"])
    allowed = read_file_content(FILES["allowed"])
    cfg = read_file_content(FILES["config"])
    
    # Configure C2PA trust settings
    settings = { "verify": { "verify_trust": True }, "trust": {} }
    
    if anchors: settings["trust"]["trust_anchors"] = anchors
    if allowed: settings["trust"]["allowed_list"] = allowed
    if cfg: settings["trust"]["trust_config"] = cfg

    c2pa.load_settings(json.dumps(settings))

    try:
        reader = c2pa.Reader(path)
        raw_output = reader.json()
        if not raw_output: sys.exit(1)

        json_data = json.loads(raw_output)
        # Update validation state based on custom logic
        json_data = update_validation_state(json_data)

        print(json.dumps(json_data, indent=2))

    except Exception:
        print(f"No manifest found in {path}")
        sys.exit(1)

def cmd_trust(path: str, trust_opts: dict[str, any]):
    main(path, trust_opts)

def print_trust_help():
    help_text = f"""Sub-command to configure trust store options, "trust --help for more details"

Usage: python3 c2pa.py <PATH> trust [OPTIONS]

Options:
      --trust_anchors <TRUST_ANCHORS>  URL or path to file containing list of trust anchors in PEM format [env: C2PATOOL_TRUST_ANCHORS={CONFIG_URLS['anchors']}]
      --allowed_list <ALLOWED_LIST>    URL or path to file containing specific manifest signing certificates in PEM format to implicitly trust [env: C2PATOOL_ALLOWED_LIST={CONFIG_URLS['allowed']}]
      --trust_config <TRUST_CONFIG>    URL or path to file containing configured EKUs in Oid dot notation [env: C2PATOOL_TRUST_CONFIG={CONFIG_URLS['config']}]
  -h, --help                           Print help
    """
    print(help_text)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "image.png"
    if os.path.exists(target):
        main(target)
    else:
        sys.exit(1)