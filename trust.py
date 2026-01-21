import os
import json
import requests
import c2pa
import sys

# --- CONFIGURAZIONE ---
CONFIG_URLS = {
    "anchors": "https://contentcredentials.org/trust/anchors.pem",
    "allowed": "https://contentcredentials.org/trust/allowed.sha256.txt",
    "config": "https://contentcredentials.org/trust/store.cfg"
}

FILES = {
    "anchors": "anchors.pem",
    "allowed": "allowed.sha256.txt",
    "config": "store.cfg"
}

def download_trust_files():
    for key, url in CONFIG_URLS.items():
        if not os.path.exists(FILES[key]):
            try:
                r = requests.get(url)
                with open(FILES[key], 'wb') as f:
                    f.write(r.content)
            except:
                pass

def read_file_content(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def recursive_find_errors(data, invalid_codes):
    """
    Cerca ricorsivamente errori fatali (Mismatch, Invalid, Revoked).
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

def check_history_integrity_strict(json_data):
    """
    LOGICA DOWNGRADE:
    1. Generatori di Test (SOLO SU INGREDIENTI).
       - C2PA Testing
       - make_test_images
       - TestApp (NUOVO!)
    2. Ingredienti Untrusted.
    3. Deep Scan per errori fatali.
    """
    
    active_id = json_data.get("active_manifest", "")
    manifests = json_data.get("manifests", {})

    # 1. Scansione Manifesti
    for man_id, content in manifests.items():
        
        # LA REGOLA D'ORO: Siamo severi solo con la STORIA (Ingredienti).
        if man_id != active_id:
            
            # A. Filtro Generatore (Anti-Test AGGIORNATO)
            generator = content.get("claim_generator", "").lower()
            # Aggiunto "testapp" alla lista
            if "c2pa testing" in generator or "make_test_images" in generator or "testapp" in generator:
                return False, f"Ingredient '{man_id}' created by Test software: {content.get('claim_generator')}."

            # B. Controllo UNTRUSTED
            status = content.get("validation_status", [])
            for err in status:
                if err.get("code") == "signingCredential.untrusted":
                    return False, f"Ingredient '{man_id}' is Untrusted (Chain Broken)."
            
            # C. Controllo Issuer Test
            sig_info = content.get("signature_info", {})
            issuer = sig_info.get("issuer", "")
            cn = sig_info.get("common_name", "")
            if "Test Signing" in issuer or "Test Signing" in cn:
                 return False, f"Ingredient '{man_id}' signed by Test Certificate."

    # 2. Deep Scan per errori fatali
    FATAL_SUBSTRINGS = [
        "mismatch",                
        "signingCredential.invalid", 
        "signingCredential.revoked"
    ]
    
    found_error, reason = recursive_find_errors(json_data, FATAL_SUBSTRINGS)
    if found_error:
        return False, reason

    # 3. Controllo Delta Ingredienti (Fallback)
    val_results = json_data.get("validation_results", {})
    deltas = val_results.get("ingredientDeltas", [])
    for delta in deltas:
        failures = delta.get("validationDeltas", {}).get("failure", [])
        if failures:
             return False, f"Ingredient Delta failure: {failures[0].get('code')}"

    return True, "History clean"

def check_active_manifest_trust(json_data):
    """
    LOGICA UPGRADE:
    Se la storia è pulita e l'unico problema è che il capo è Untrusted -> Valid.
    """
    active_manifest = json_data.get("validation_results", {}).get("activeManifest", {})
    successes = active_manifest.get("success", [])
    has_valid_sig = any(s.get("code") == "claimSignature.validated" for s in successes)
    
    if not has_valid_sig:
        return False

    errors = json_data.get("validation_status", [])
    for err in errors:
        code = err.get("code", "")
        if code != "signingCredential.untrusted":
            return False
            
    return True

def align_with_rust_logic(json_data):
    current_state = json_data.get("validation_state")

    # FASE 1: CONTROLLO STORIA (Downgrade)
    is_history_clean, reason = check_history_integrity_strict(json_data)
    
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

    # FASE 2: PROMOZIONE (Upgrade)
    if current_state == "Invalid":
        if check_active_manifest_trust(json_data):
            json_data["validation_state"] = "Valid"

    return json_data

def main(image_path):
    download_trust_files()
    anchors = read_file_content(FILES["anchors"])
    allowed = read_file_content(FILES["allowed"])
    cfg = read_file_content(FILES["config"])
    
    settings = { "verify": { "verify_trust": True }, "trust": {} }
    if anchors: settings["trust"]["trust_anchors"] = anchors
    if allowed: settings["trust"]["allowed_list"] = allowed
    if cfg: settings["trust"]["trust_config"] = cfg

    try:
        if hasattr(c2pa, 'load_settings'):
            c2pa.load_settings(json.dumps(settings))
    except:
        pass

    try:
        reader = c2pa.Reader(image_path)
        raw_output = reader.json()
        if not raw_output: sys.exit(1)

        if isinstance(raw_output, str):
            json_data = json.loads(raw_output)
        elif isinstance(raw_output, dict):
            json_data = raw_output
        else:
            sys.exit(1)
        
        # --- ALLINEAMENTO ---
        json_data = align_with_rust_logic(json_data)

        print(json.dumps(json_data, indent=2))
        with open("python_output.json", "w") as f:
            json.dump(json_data, f, indent=2)

    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "image.png"
    if os.path.exists(target):
        main(target)
    else:
        sys.exit(1)