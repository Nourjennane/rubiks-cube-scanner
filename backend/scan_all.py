from scanner import capture_face
import requests
import time

RESET = "http://127.0.0.1:8000/scan/reset"
COMPLETE = "http://127.0.0.1:8000/scan/complete"

faces = ["U", "R", "F", "D", "L", "B"]

requests.post(RESET)
time.sleep(0.3)

for f in faces:
    capture_face(f)
    time.sleep(0.3)

res = requests.post(COMPLETE)
print(res.json())