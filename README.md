# 📹 StreamCam

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">
</p>

<p align="center">
Turn your laptop webcam into a powerful local Wi-Fi camera with live streaming, browser-based recording, QR code access, and optional HTTPS support.
</p>

---

## 📖 Overview

**StreamCam** is a lightweight Python application that transforms your laptop or desktop webcam into a **live network camera**. Any smartphone, tablet, or computer connected to the same Wi-Fi network can instantly view the live stream using a web browser—no additional apps required.

The project also includes a modern dashboard, automatic QR code generation, browser-based recording, automatic reconnection, and optional HTTPS support for iOS devices.

---

## ✨ Features

- 📹 Live webcam streaming over local Wi-Fi
- 🌐 Works in any modern web browser
- 📱 Compatible with Android, iPhone, tablets, and desktops
- 🎥 Browser-side video recording
- 💾 Videos download directly to the receiving device
- 🔳 QR code for instant connection
- 📡 Automatic local IP detection
- 🔄 Auto reconnect if the stream disconnects
- 🔒 Optional HTTPS support for Safari on iOS
- ⚡ High-performance MJPEG streaming using OpenCV
- 🎨 Clean and responsive user interface

---

# 📸 Preview

> **Add screenshots after uploading your project to GitHub**

```
Dashboard
────────────────────────────────
Server Status
QR Code
Local Network Address
Uptime
────────────────────────────────

            ↓

Phone Browser

────────────────────────────────
📹 Live Camera Feed

● Start Recording
■ Stop Recording

Downloads Video Automatically
────────────────────────────────
```

---

# 🛠 Technologies Used

- Python
- Flask
- OpenCV
- HTML5
- CSS3
- JavaScript
- MediaRecorder API

---

# 📂 Project Structure

```
StreamCam/
│
├── launcher.py          # Launches the application
├── server.py            # Flask streaming server
├── setup.bat            # Windows setup script
├── setup.sh             # Linux/macOS setup script
├── SETUP_GUIDE.md       # Detailed documentation
├── README.md
└── requirements.txt
```

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/subhanbhatti50134-jpg/StreamCam.git

cd StreamCam
```

---

## 2. Install Dependencies

### Windows

```cmd
setup.bat
```

### Linux / macOS

```bash
bash setup.sh
```

Or install manually:

```bash
pip install flask opencv-python pyopenssl qrcode pillow
```

---

## 3. Run StreamCam

```bash
python launcher.py
```

If you're running on a remote machine:

```bash
python launcher.py --no-browser
```

---

# 📱 Connecting Your Phone

1. Connect your phone to the **same Wi-Fi network** as your computer.
2. Launch StreamCam.
3. Open the dashboard.
4. Scan the QR code.

or manually open

```
http://YOUR_LOCAL_IP:8080
```

Example

```
http://192.168.1.100:8080
```

The live camera feed will appear instantly.

---

# 🎥 Recording

Click

```
Start Recording
```

to begin recording.

Click

```
Stop Recording
```

Your browser will automatically download the recorded video.

The server never stores your recordings.

---

# 🍏 iPhone / Safari Support

Safari requires HTTPS to allow browser downloads.

Enable HTTPS by changing:

```python
USE_HTTPS = True
```

inside

```python
server.py
```

Then open

```
https://YOUR_LOCAL_IP:8443
```

Trust the temporary certificate once and you're ready to record.

---

# ⚙️ Configuration

Inside **server.py**

```python
CAMERA_INDEX = 0
STREAM_WIDTH = 1280
STREAM_HEIGHT = 720
STREAM_FPS = 30
JPEG_QUALITY = 85
USE_HTTPS = False
```

You can modify these values to suit your hardware and network.

---

# 🌐 Browser Compatibility

| Browser | Streaming | Recording |
|----------|-----------|-----------|
| Google Chrome | ✅ | ✅ |
| Microsoft Edge | ✅ | ✅ |
| Firefox | ✅ | ✅ |
| Safari (HTTPS) | ✅ | ✅ |
| Android Chrome | ✅ | ✅ |

---

# 📋 Troubleshooting

### Black Screen

Try another camera index.

```python
CAMERA_INDEX = 1
```

---

### Phone Can't Connect

- Ensure both devices are connected to the same Wi-Fi network.
- Allow ports **8080**, **8079**, and **8443** through your firewall.

---

### Stream is Slow

Lower

```python
JPEG_QUALITY
```

or

```python
STREAM_FPS
```

inside `server.py`.

---

### HTTPS Doesn't Work

Install OpenSSL or disable HTTPS:

```python
USE_HTTPS = False
```

---

# 💡 Future Improvements

- 🎤 Audio Streaming
- 📷 Multiple Camera Support
- 🔐 Password Protected Streams
- ☁️ Internet Streaming
- 📸 Snapshot Capture
- 📁 Recording History
- 🌙 Dark & Light Themes
- 📊 Streaming Statistics

---

# 🤝 Contributing

Contributions are welcome!

1. Fork this repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push your branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

# ⭐ Support

If you found this project useful, please consider giving it a **Star ⭐** on GitHub.

It helps support future development and makes the project easier for others to discover.

---

# 📌 Repository

**GitHub Repository**

https://github.com/subhanbhatti50134-jpg/StreamCam

---

# 🏷 GitHub Topics

```
python
flask
opencv
webcam
camera
video-streaming
mjpeg
wifi
local-network
streaming
browser
```

---

# 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
Made with ❤️ by <b>Subhan Bhatti</b>

If you like this project, don't forget to ⭐ the repository!
</p>