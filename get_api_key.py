from curl_cffi import requests
import re

JS_URL = "https://trackercdn.com/static-files/trackergg/production/dist/client/assets/index-CAMcpGGm.js"

print("Fetching JS bundle to extract API key...")
r = requests.get(JS_URL, impersonate="chrome124")

# Search for the API key pattern (UUID format)
matches = re.findall(r'["\']TRN-Api-Key["\']\s*[,:]?\s*["\']([a-f0-9-]{36})["\']', r.text, re.IGNORECASE)

if matches:
    print(f"Found API key(s): {matches}")
else:
    # Broader search
    matches = re.findall(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', r.text)
    print(f"Found UUIDs (pick the right one): {matches[:10]}")