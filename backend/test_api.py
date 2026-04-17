import httpx
r = httpx.get("http://localhost:8000/openapi.json")
print(f"Status: {r.status_code}")
d = r.json()
print(f"Endpoints: {list(d['paths'].keys())}")
