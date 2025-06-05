import cv2
import time
import requests
import os
import logging
from datetime import datetime, time as timeobj
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# === LOAD ENV VARIABLES ===
load_dotenv()

rtsp_url = os.getenv("RTSP_URL")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

# === CONFIGURATION ===
grace_period = 10
snapshot_delay = 1
detection_sensitivity = 8000

# === LOGGING SETUP ===
log_dir = os.getenv("LOG_DIR", "/home/rtm/cameraDetection")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "motion_log.txt")
log_handler = RotatingFileHandler(log_file, maxBytes=3_000_000, backupCount=1)
formatter = logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# === TIME WINDOW ===


def is_detection_allowed():
    now = datetime.now().time()
    evening_start = timeobj(19, 0)
    midnight = timeobj(0, 0)
    after_midday_end = timeobj(13, 0)
    return (
        evening_start <= now <= timeobj(23, 59) or
        midnight <= now <= after_midday_end
    )

# === TELEGRAM SEND FUNCTION ===


def send_telegram_notification(image_path):
    msg_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image_path, 'rb') as img:
        files = {'photo': img}
        for chat_id in chat_ids:
            data = {
                'chat_id': chat_id.strip(),
                'caption': 'Motion detected – <a href="http://10.0.0.100:5000/#tapo_100">Livestream</a>',
                'parse_mode': 'HTML'
            }
            response = requests.post(msg_url, files=files, data=data)
            if response.status_code == 200:
                logging.info(f"Snapshot sent to {chat_id}")
            else:
                logging.error(
                    f"Failed to send to {chat_id}: {response.status_code}")
            img.seek(0)


# === CAMERA STREAM SETUP ===
cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    logging.error("Error: Cannot open RTSP stream.")
    exit()

ret, frame1 = cap.read()
ret2, frame2 = cap.read()
if not ret or not ret2:
    logging.error("Failed to read initial frames from stream.")
    exit(1)

motion_detected = False
last_motion_time = None
waiting_to_capture = False
capture_trigger_time = None

# === MAIN LOOP ===
while cap.isOpened():
    current_time = time.time()

    if not is_detection_allowed():
        time.sleep(60)
        continue

    if waiting_to_capture and time.time() >= capture_trigger_time:
        ret, snapshot = cap.read()
        if ret:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            image_path = f"motion_{timestamp}.jpg"
            cv2.imwrite(image_path, snapshot)

            send_telegram_notification(image_path)

            try:
                os.remove(image_path)
                logging.info(f"Snapshot deleted: {image_path}")
            except Exception as e:
                logging.error(f"Could not delete {image_path}: {e}")

            waiting_to_capture = False

    ret, frame = cap.read()
    if not ret:
        logging.error("Stream read failed. Exiting...")
        break

    diff = cv2.absdiff(frame1, frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(
        dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    significant_motion = any(cv2.contourArea(
        c) > detection_sensitivity for c in contours)

    if significant_motion:
        if not motion_detected:
            logging.info("Motion detected!")
            motion_detected = True
            last_motion_time = time.time()
            capture_trigger_time = time.time() + snapshot_delay
            waiting_to_capture = True
        else:
            last_motion_time = time.time()
    elif motion_detected:
        if last_motion_time and (time.time() - last_motion_time) > grace_period:
            logging.info("Motion ended.")
            motion_detected = False
            last_motion_time = None
            waiting_to_capture = False

    frame1 = frame

cap.release()
cv2.destroyAllWindows()
