import cv2

#raspberry pi camera feed
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Camera not detected.")
    exit()

cap.set(3, 640)  # breedte schermpje
cap.set(4, 480)  # hoogte schermpje

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Camera Feed", frame)

    # q drukken om uit scherm te gaan
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
