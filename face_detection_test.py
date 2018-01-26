import cv2
import itertools

front_face_cascade = cv2.CascadeClassifier('/usr/share/opencv/lbpcascades/lbpcascade_frontalface.xml')
profile_face_cascade = cv2.CascadeClassifier('/usr/share/opencv/lbpcascades/lbpcascade_profileface.xml')


image = cv2.imread('rec_test3.jpg')

image = cv2.resize(image, (640, 480))

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

front_faces = front_face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
profile_faces = profile_face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

faces = itertools.chain(front_faces, profile_faces)

for (x, y, w, h) in faces:
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

cv2.imshow("Faces found", image)
cv2.waitKey(0)
