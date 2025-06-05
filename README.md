# Motion Detection with Telegram Alerts

This project captures an RTSP video stream, detects motion, and sends an alert with a snapshot to Telegram.

## Features

- RTSP video stream monitoring
- Motion detection using OpenCV
- Telegram bot photo alerts
- Configurable time window for active monitoring
- Log rotation and cleanup
- Secure credentials via `.env` file

## TODO

- Enable multiple cameras

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file based on the `.env` example:

```
RTSP_URL=rtsp://username:password@camera_ip:554/stream1
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_IDS=-123456789
LOG_DIR=/home/rtm/cameraDetection
```

3. Run the script:

```bash
python3 motion_detector.py
```

## Autostart on Boot (Recommended)

Use the `motionbot.service` file and install it with:

```bash
sudo cp motionbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable motionbot.service
sudo systemctl start motionbot.service
```

## How to Create a Telegram Bot

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather)
2. Run `/newbot` and follow the prompts
3. Save the bot token from the message
4. Disable privacy mode via BotFather > Bot Settings > Group Privacy > Turn Off

## Get Your Chat ID

1. Add the bot to your Telegram group
2. Send a message in the group
3. Run:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

4. Look for `"chat": { "id": -XXXXXXXXX }` and use that in your `.env`


## How It Works

The script does the following:

1. Connects to an RTSP video stream (commonly used by security cameras like TP-Link Tapo)
2. Continuously reads frames and compares them to detect movement
3. When motion is detected:
   - It waits a short delay (`snapshot_delay`, default 1 second)
   - Captures a snapshot from the stream
   - Sends the snapshot via a Telegram bot to a group or individual
   - Deletes the snapshot from disk after sending
4. Continues monitoring and suppresses repeated alerts until motion has ended

### Motion Detection Sensitivity

The `detection_sensitivity` parameter controls how sensitive the detection is. It represents the minimum size (area) of movement needed to trigger an alert:

| Value         | Sensitivity Description                     |
|---------------|---------------------------------------------|
| `1000`        | Very sensitive (even small light changes)   |
| `3000`        | Medium sensitivity                          |
| `8000`+       | Low sensitivity (only large movements)      |

You can tweak this parameter in your `.env` or directly in `motion_detector.py` to adjust how aggressively alerts are triggered.

## Camera Compatibility

This project was built and tested using **TP-Link Tapo webcams**. While it should work with any RTSP-compatible camera, you may need to adjust:
- Stream URLs or paths (`/stream1`, `/h264`, etc.)
- RTSP credentials
- Video codec compatibility with OpenCV

Make sure your camera supports RTSP and that the feed is accessible by OpenCV.

## Test stream

The following command will open a window and show the camera stream

```
ffplay rtsp://username:password@camera_ip:554/stream1
```