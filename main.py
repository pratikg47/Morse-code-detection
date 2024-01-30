# Libreries 
from imutils import face_utils
import numpy as np
import imutils
import dlib
import cv2
from scipy.spatial import distance as dist
from imutils.video import VideoStream
import argparse
import keyboard
import morse_code
import constants


def main():
	(vs, detector, predictor, lStart, lEnd, rStart,rEnd) = setup_detector_video()
	total_morse = loop_camera(vs, detector, predictor, lStart, lEnd, rStart, rEnd)
	cleanup(vs)
	print_results(total_morse)

# function for ear
def eye_aspect_ratio(eye):
    a = dist.euclidean(eye[1], eye[5])
    b = dist.euclidean(eye[2], eye[4])
    c = dist.euclidean(eye[0], eye[3])
    
    ear = (a + b) / (2 * c)
    return ear

def setup_detector_video():
	# initialize dlib's face detector (HOG-based) and then create
	# the facial landmark predictor
	print("[INFO] loading facial landmark predictor...")
	detector = dlib.get_frontal_face_detector()
	predictor = dlib.shape_predictor('detect_blink.dat')

	# grab the indexes of the facial landmarks for the left and
	# right eye, respectively
	(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
	(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

	# start the video stream thread
	print("[INFO] starting video stream thread...")
	print("[INFO] Type ']' or close eyes for {} frames to exit.".format(
			constants.BREAK_LOOP_FRAMES))
	vs = VideoStream(src=0).start()
	return vs, detector, predictor, lStart, lEnd, rStart, rEnd

def loop_camera(vs, detector, predictor, lStart, lEnd, rStart, rEnd):
	# initialize the frame counters and the total number of blinks
	COUNTER = 0
	BREAK_COUNTER = 0
	EYES_OPEN_COUNTER = 0
	CLOSED_EYES = False
	WORD_PAUSE = False
	PAUSED = False

	total_morse = ""
	morse_word = ""
	morse_char = ""

	while True:
		# grabing frame from the threaded video file stream, resize, and convert it to grayscale channels)
		frame = vs.read()
		frame = imutils.resize(frame, width=450)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		# detect faces in the grayscale frame
		rects = detector(gray, 0)

		# loop over the face detections
		for rect in rects:
			#facial landmark to numpy array
			shape = predictor(gray, rect)
			shape = face_utils.shape_to_np(shape)
			# extracting ear for both eyes
			leftEye = shape[lStart:lEnd]
			rightEye = shape[rStart:rEnd]
			left_eye_ar = eye_aspect_ratio(leftEye)
			right_eye_ar = eye_aspect_ratio(rightEye)
			# average the eye aspect ratio together for both eyes
			eye_ar = (left_eye_ar + right_eye_ar) / 2.0

			# compute the convex hull for the left and right eye, then
			# visualize each of the eyes
			leftEyeHull = cv2.convexHull(leftEye)
			rightEyeHull = cv2.convexHull(rightEye)
			cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
			cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

			# check to see if the eye aspect ratio is below the blink
			# threshold, and if so, increment the blink frame counter
			if eye_ar < constants.EYE_AR_THRESH:
				COUNTER += 1
				BREAK_COUNTER += 1
				if COUNTER >= constants.EYE_AR_CONSEC_FRAMES_DOT:
					CLOSED_EYES = True
				# Reset morse that appears on screen if it had just been "/"
				if not PAUSED:
					morse_char = ""
				# Eyes closed for long enough to close program. 
				if (BREAK_COUNTER >= constants.BREAK_LOOP_FRAMES):
					break
			# otherwise, the eye aspect ratio is not below the blink
			# threshold
			else:
				# Eyes weren't closed for that long 
				if (BREAK_COUNTER < constants.BREAK_LOOP_FRAMES):
					BREAK_COUNTER = 0
				EYES_OPEN_COUNTER += 1
				# Dash detected as eyes closed for long time.
				if COUNTER >= constants.EYE_AR_CONSEC_FRAMES_CLOSED_DASH:
					morse_word += "-"
					total_morse += "-"
					morse_char += "-"
					# reset the eye frame counter
					COUNTER = 0
					CLOSED_EYES = False
					PAUSED = True
					EYES_OPEN_COUNTER = 0
				# Dot detected as eyes closed for short time.
				elif CLOSED_EYES:
					morse_word += "."
					total_morse += "."
					morse_char += "."
					COUNTER = 1
					CLOSED_EYES = False
					PAUSED = True
					EYES_OPEN_COUNTER = 0
				# Only add space between chars if char previously 
				# detected and eyes open for > PAUSE_CONSEC_FRAMES.
				elif PAUSED and (EYES_OPEN_COUNTER >= 
						constants.PAUSE_CONSEC_FRAMES):
					morse_word += "/"
					total_morse += "/"
					morse_char = "/"
					PAUSED = False
					WORD_PAUSE = True
					CLOSED_EYES = False
					EYES_OPEN_COUNTER = 0
					keyboard.write(morse_code.from_morse(morse_word))
					morse_word = ""
				# Add space between words if char space prev added and 
				# eyes open for >= WORD_PAUSE_CONSEC_FRAMES after 
				# already opened for PAUSE_CONSEC_FRAMES .
				elif (WORD_PAUSE and EYES_OPEN_COUNTER >= 
						constants.WORD_PAUSE_CONSEC_FRAMES):
					# "/" already in str from char pause, "¦" is 
					# converted to a " " (space) char.
					total_morse += "¦/"
					morse_char = ""
					WORD_PAUSE = False
					CLOSED_EYES = False
					EYES_OPEN_COUNTER = 0
					keyboard.write(morse_code.from_morse("¦/"))

			# draw the computed eye aspect ratio for the frame and display 
			# the recently detected morse code
			cv2.putText(frame, "EAR: {:.2f}".format(eye_ar), (300, 30),
				cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
			cv2.putText(frame, "{}".format(morse_char), (100, 200),
				cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)

			# print the recent morse to the console on the same line 
			# (unless a part cannot be translated)
			print("\033[K", "morse_word: {}".format(morse_word), end="\r")

		# show the frame
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(0) & 0xFF

		# if the `]` key was pressed, break from the loop
		if key == ord("]") or (
				BREAK_COUNTER >= constants.BREAK_LOOP_FRAMES):
			keyboard.write(morse_code.from_morse(morse_word))
			break
	return total_morse

def cleanup(vs):
	cv2.destroyAllWindows()
	vs.stop()
	
def print_results(total_morse):
	print("Morse Code: ", total_morse.replace("¦", " "))
	print("Translated: ", morse_code.from_morse(total_morse))
	
if __name__ == "__main__":
	main()