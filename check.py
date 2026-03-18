import curl_cffi
from curl_cffi import requests

print(f"curl_cffi version: {curl_cffi.__version__}")

# Try different ways to get the list depending on version
try:
    from curl_cffi.const import BrowserType
    print("\nSupported impersonate values:")
    for b in BrowserType:
        print(f"  {b.value}")
except ImportError:
    pass

try:
    from curl_cffi import BrowserType
    print("\nSupported impersonate values:")
    for b in BrowserType:
        print(f"  {b.value}")
except ImportError:
    pass

# Fallback: just print all attributes of the requests module
print("\nAll curl_cffi.requests attributes:")
print([x for x in dir(requests) if "imperson" in x.lower() or "browser" in x.lower()])