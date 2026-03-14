import requests
import json

BASE_URL = "http://localhost:8880" # Default chimera-api port from justfile

def test_vaas_headers():
    print("Testing VaaS Headers...")
    url = f"{BASE_URL}/api/v1/banking/accounts?user_id=attacker"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        # Check for X-Chimera headers
        vaas_headers = {k: v for k, v in response.headers.items() if k.startswith('X-Chimera-')}
        print("VaaS Headers:")
        print(json.dumps(vaas_headers, indent=2))
        
        assert 'X-Chimera-Vuln-ID' in response.headers
        assert 'X-Chimera-Vuln-Type' in response.headers
        assert response.headers['X-Chimera-Patched'] == 'false'
        
    except Exception as e:
        print(f"Error: {e}")

def test_verbose_metadata():
    print("\nTesting Verbose Metadata Envelope...")
    url = f"{BASE_URL}/api/v1/banking/accounts?user_id=attacker"
    headers = {'X-Chimera-Education': 'true'}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if '_chimera' in data:
            print("Found _chimera metadata:")
            print(json.dumps(data['_chimera'], indent=2))
            assert data['_chimera']['vuln_id'] == 'CHM-BANK-002'
        else:
            print("FAILED: _chimera metadata not found in body.")
            
    except Exception as e:
        print(f"Error: {e}")

def test_education_catalog():
    print("\nTesting Education Catalog API...")
    url = f"{BASE_URL}/api/v1/education/vulns"
    
    try:
        response = requests.get(url)
        data = response.json()
        print(f"Catalog contains {len(data)} vulnerabilities.")
        assert len(data) > 0
        assert 'CHM-BANK-001' in data
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: Requires the API to be running
    test_vaas_headers()
    test_verbose_metadata()
    test_education_catalog()
