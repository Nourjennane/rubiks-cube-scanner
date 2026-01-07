import cv2
import numpy as np
import requests

BACKEND_URL = "http://127.0.0.1:8000/scan/rgb_face"

def average_rgb(region):
    avg = np.mean(region.reshape(-1, 3), axis=0)
    return (int(avg[2]), int(avg[1]), int(avg[0]))

def capture_face(face):
    cap = cv2.VideoCapture(0)
    print(f"[SCAN] Show {face} face and press SPACE")

    size, gap = 60, 10

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        h, w, _ = frame.shape
        x0 = w//2 - (3*size + 2*gap)//2
        y0 = h//2 - (3*size + 2*gap)//2

        for r in range(3):
            for c in range(3):
                x = x0 + c*(size+gap)
                y = y0 + r*(size+gap)
                cv2.rectangle(frame, (x,y), (x+size,y+size), (0,255,0), 2)

        cv2.putText(frame, f"Face {face} – SPACE to capture",
                    (40,40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow("Scanner", frame)
        key = cv2.waitKey(1)

        if key == 32:
            rgb = []
            for r in range(3):
                for c in range(3):
                    x = x0 + c*(size+gap)
                    y = y0 + r*(size+gap)
                    region = frame[y:y+size, x:x+size]
                    rgb.append(average_rgb(region))

            requests.post(BACKEND_URL, json={"face": face, "rgb": rgb})
            break

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()