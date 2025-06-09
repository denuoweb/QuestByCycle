import json
import rsa
import requests
from email.utils import formatdate
from urllib.parse import urlparse

                                                  
with open("actor_priv.pem", "rb") as f:
    privkey = rsa.PrivateKey.load_pkcs1(f.read())

                                    
activity = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Follow",
    "actor": "https://remote.instance/users/alice",
    "object": "https://localhost:5000/users/t12"
}
body = json.dumps(activity).encode("utf-8")

                               
url = "https://localhost:5000/users/t12/inbox"
parsed = urlparse(url)
date_header = formatdate(usegmt=True)
signing_components = [
    f"(request-target): post {parsed.path}",
    f"host: {parsed.netloc}",
    f"date: {date_header}"
]
signing_string = "\n".join(signing_components).encode("utf-8")

                           
signature = rsa.sign(signing_string, privkey, "SHA-256").hex()
key_id = "https://localhost:5000/users/t12#main-key"
signature_header = (
    f'keyId="{key_id}",'
    'algorithm="rsa-sha256",'
    'headers="(request-target) host date",'
    f'signature="{signature}"'
)

                                                     
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
    verify=False,                                            
    allow_redirects=False,                                  
    timeout=5,                                             
    cookies={}
)

if resp.status_code != 202:
    raise SystemExit("Inbox POST did not return 202 Accepted")
