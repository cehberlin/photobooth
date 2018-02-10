import cv2
import itertools
import numpy as np
from matplotlib import pyplot as plt

def show_faces():

    front_face_cascade = cv2.CascadeClassifier('/usr/local/share/OpenCV/lbpcascades/lbpcascade_frontalface.xml')
    profile_face_cascade = cv2.CascadeClassifier('/usr/local/share/OpenCV/lbpcascades/lbpcascade_profileface.xml')


    image = cv2.imread('rec_test1.jpg')

    image = cv2.resize(image, (640, 480))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    front_faces = front_face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    profile_faces = profile_face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    faces = itertools.chain(front_faces, profile_faces)

    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow("Faces found", image)
    cv2.waitKey(0)


img1 = cv2.imread('huettchen_gold.png',0)          # queryImage
img2 = cv2.imread('test_match.jpg',0) # trainImage


# Initiate SIFT detector
sift = cv2.ORB_create()

# find the keypoints and descriptors with SIFT
kp1, des1 = sift.detectAndCompute(img1,None)
kp2, des2 = sift.detectAndCompute(img2,None)

# FLANN parameters
FLANN_INDEX_KDTREE = 0
FLANN_INDEX_LSH = 6
index_params = dict(algorithm = FLANN_INDEX_LSH,
                   table_number = 6, # 12
                   key_size = 12,     # 20
                   multi_probe_level = 1) #2
search_params = dict(checks=100)   # or pass empty dictionary

flann = cv2.FlannBasedMatcher(index_params,search_params)

matches = flann.knnMatch(des1,des2,k=2)

# Need to draw only good matches, so create a mask
matchesMask = [[0,0] for i in range(len(matches))]

# ratio test as per Lowe's paper
for i,match in enumerate(matches):
    if len(match)>1:
        (m, n) = match
        if m.distance < 0.7*n.distance:
            matchesMask[i]=[1,0]

draw_params = dict(matchColor = (0,255,0),
                   singlePointColor = (255,0,0),
                   matchesMask = matchesMask,
                   flags = 0)

img3 = cv2.drawMatchesKnn(img1,kp1,img2,kp2,matches,None,**draw_params)

plt.imshow(img3,),plt.show()
