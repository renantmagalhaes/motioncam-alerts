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

- [ ] Enable multiple cameras
- [ ] Add time control inside `.env`

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

### Time-Based Detection Control

The script includes a built-in time filter to only perform motion detection during specific hours of the day. This is useful if you only want alerts during working hours, nighttime, or while you're away from home.

#### 📦 How it works
The function `is_detection_allowed()` checks the current system time and allows detection only if it falls within a defined range.

By default, it’s configured like this:

```python3
def is_detection_allowed():
    now = datetime.now().time()
    evening_start = time(19, 0)         # 19:00 (7 PM)
    midnight = time(0, 0)               # 00:00 (midnight)
    after_midday_end = time(13, 0)      # 13:00 (1 PM)

    return (
        evening_start <= now <= time(23, 59) or
        midnight <= now <= after_midday_end
    )
```

This setup allows motion detection during:

- Evening to midnight (19:00 to 23:59)
- Midnight to early afternoon (00:00 to 13:00)

#### How to customize it
If you want detection to happen at different times, just change the values in the function. For example, to detect only from 9 AM to 5 PM:

```python3
def is_detection_allowed():
    now = datetime.now().time()
    return time(9, 0) <= now <= time(17, 0)
```
This gives you full control over when your system should be active — without needing an external scheduler.

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