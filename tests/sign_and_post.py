import json
import rsa
import requests
from email.utils import formatdate
from urllib.parse import urlparse

# 1. Load your actor’s private key (PKCS#1 format)
with open("actor_priv.pem", "rb") as f:
    privkey = rsa.PrivateKey.load_pkcs1(f.read())

# 2. Prepare the ActivityPub payload
activity = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Follow",
    "actor": "https://remote.instance/users/alice",
    "object": "https://localhost:5000/users/t12"
}
body = json.dumps(activity).encode("utf-8")

# 3. Build the signature string
url = "https://localhost:5000/users/t12/inbox"
parsed = urlparse(url)
date_header = formatdate(usegmt=True)
signing_components = [
    f"(request-target): post {parsed.path}",
    f"host: {parsed.netloc}",
    f"date: {date_header}"
]
signing_string = "\n".join(signing_components).encode("utf-8")

# 4. Sign with your RSA key
signature = rsa.sign(signing_string, privkey, "SHA-256").hex()
key_id = "https://localhost:5000/users/t12#main-key"
signature_header = (
    f'keyId="{key_id}",'
    'algorithm="rsa-sha256",'
    'headers="(request-target) host date",'
    f'signature="{signature}"'
)

# 5. Send the signed POST, but don’t follow redirects
headers = {
    "Content-Type": "application/activity+json",
    "Date": date_header,
    "Host": parsed.netloc,
    "Signature": signature_header
    }

resp = requests.post(
    url,
    data=body,
    headers=headers,
    cert=("cert.pem", "key.pem"),
    verify=False,           # skip SSL verify for self‐signed
    allow_redirects=False,  # do not follow any 3xx redirect
    timeout=5,               # fail after 5s if no response
    cookies={}
)

if resp.status_code != 202:
    raise SystemExit("Inbox POST did not return 202 Accepted")
