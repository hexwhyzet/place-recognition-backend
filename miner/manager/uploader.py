import requests

file = open("miner/manager/ids2.txt", "r").readlines()
for pano_id in file:
    url = f"http://158.160.5.153:80/add_pano/google_pano/{pano_id.strip()}"
    print(url)
    resp = requests.post(url)
    print(resp.status_code, resp.content)
