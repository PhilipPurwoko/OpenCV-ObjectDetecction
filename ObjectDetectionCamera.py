print('Importing Library...')
import numpy as np
import cv2

def detectEdge(insert_images):
    # Copy to avoid destructive move
    source_image = insert_images.copy()
    
    # Calculate for threshold
    medium_value = np.median(source_image)
    lower_value = int(max(0,0.7*medium_value))
    upper_value = int(min(255,1.3*medium_value))
    
    # Use Canny Edge Detection
    edge = cv2.Canny(source_image,threshold1=lower_value,threshold2=upper_value)
    source_image[edge == 255] = [0,255,0]
    return source_image

def detectContour(source):
	# Find Canny Edge
	canny = cv2.Canny(cv2.cvtColor(source, cv2.COLOR_BGR2GRAY),30,200)

	# Find Contour
	contour,hierarchy = cv2.findContours(canny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
	desired_contour = np.zeros(source.shape)

	# Draw Contour
	cv2.drawContours(desired_contour,contour,-1,(0,255,0),3)
	return desired_contour

def detectFace(source):
	# Use frontalface
	face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
	image = source.copy()

	# Convert to gray
	gray = cv2.cvtColor(image.copy(),cv2.COLOR_BGR2GRAY)

	# Run detection
	face = face_cascade.detectMultiScale(gray,scaleFactor=1.2,minNeighbors=5)
	for (x,y,w,h) in face:
		cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),3)
	return image

def detectCorner(source):
	# Convert to gray
	gray = np.float32(cv2.cvtColor(source.copy(),cv2.COLOR_BGR2GRAY))

	# Run detection using corner Harris
	destination = cv2.cornerHarris(src=gray,blockSize=2,ksize=3,k=0.04)
	destination = cv2.dilate(destination,None)

	# Apply detection
	source[destination>0.01*destination.max()] = [0,255,0]
	return source

def applyWatershed(source):
	source = source.astype(np.uint8)
	# Blur image
	image = cv2.cvtColor(cv2.medianBlur(source,5),cv2.COLOR_BGR2RGB)
	
	# Convert to gray
	gray_image = cv2.cvtColor(image.copy(),cv2.COLOR_RGB2GRAY)

	# Threshold image
	_,threshold_image = cv2.threshold(gray_image,0,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

	# Remove noise (just in case)
	kernel = np.ones((3,3),np.uint8)
	clear_threshold_image = cv2.morphologyEx(threshold_image,cv2.MORPH_OPEN,kernel,iterations=2)

	# Find sure background
	sure_background = cv2.dilate(clear_threshold_image,kernel,iterations=3)

	# Distance transform
	distance_transform = cv2.distanceTransform(clear_threshold_image,cv2.DIST_L2,5)

	# Find sure foreground via distance transform
	_, sure_foreground = cv2.threshold(distance_transform,0.7*distance_transform.max(),255,0)
	sure_foreground = np.uint8(sure_foreground)

	# Sure Background - Sure Foreground = Unknown
	unknown = cv2.subtract(sure_background,sure_foreground)

	# Create Marker
	_,marker = cv2.connectedComponents(sure_foreground)
	marker += 1
	marker[unknown == 255] = 0

	# Apply wathershed algorithm
	watershed_marker = cv2.watershed(image,marker)

	# Detect Contour
	contours, hierarchy = cv2.findContours(watershed_marker,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
	cv2.drawContours(image,contours,-1,(255,0,0),5)

	return image


videoCapture = cv2.VideoCapture(0)
while True:
	res,frame = videoCapture.read()
	cv2.imshow('Camera',applyWatershed(frame))
	if cv2.waitKey(1) == 27:
		break

videoCapture.release()
cv2.destroyAllWindows()