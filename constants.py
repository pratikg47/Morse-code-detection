# The eye aspect ratio threshold 
EYE_AR_THRESH = 0.25
# The consecutive frames that the eyes need to be closed to indicate a blink: dot
EYE_AR_CONSEC_FRAMES_DOT = 3
# for Consec frames the EAR must be below the threshold: dash
EYE_AR_CONSEC_FRAMES_CLOSED_DASH = 10
# pause between two words here eyes must be open
PAUSE_CONSEC_FRAMES = 20

# between words. This is added with PAUSE_CONSEC_FRAMES to detect pause
WORD_PAUSE_CONSEC_FRAMES = 35
# Consec frames eyes must be closed to exit the program
BREAK_LOOP_FRAMES = 60