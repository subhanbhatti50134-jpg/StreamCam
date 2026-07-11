# StreamCam Mobile — Build Instructions

This folder is a ready-to-build Capacitor project. It wraps the `www/`
web app (settings screen + live stream + recording) into a real installable
app. I can't compile the final APK/IPA inside this sandbox — Android builds
need the Android SDK/Gradle, and iOS builds need Xcode on a Mac — but the
project is complete and these steps are copy/paste.

## Prerequisites

- [Node.js](https://nodejs.org) (LTS)
- **For Android:** [Android Studio](https://developer.android.com/studio) (free, Windows/macOS/Linux)
- **For iOS:** a Mac with [Xcode](https://apps.apple.com/app/xcode/id497799835) installed, plus an Apple Developer account to install on a real device or publish

## 1 — Install dependencies

```bash
cd mobile
npm install
```

## 2 — Add the native platforms

```bash
npx cap add android
npx cap add ios      # only if you're on a Mac and want iOS too
```

This generates `android/` and `ios/` native project folders.

## 3 — Android: allow local-network HTTP traffic

Open `android/app/src/main/AndroidManifest.xml` and apply the additions in
`ANDROID_MANIFEST_ADDITIONS.xml` in this folder (permissions + cleartext
traffic flag). This is required because the phone talks to your laptop's
plain `http://` server on your Wi-Fi, not a public HTTPS site.

## 4 — Build & run

```bash
npx cap sync
npx cap open android     # opens Android Studio -> press Run, or Build > Build APK(s)
npx cap open ios         # opens Xcode (Mac only) -> press Run, or Product > Archive
```

- In Android Studio: **Build → Build Bundle(s)/APK(s) → Build APK(s)** gives
  you an installable `.apk` in `android/app/build/outputs/apk/debug/`.
- In Xcode: connect an iPhone and press ▶ to install directly, or
  **Product → Archive** to create an `.ipa` for TestFlight/App Store.

## 5 — Using the app

1. Open the StreamCam tray app on your laptop (see `../desktop/README.md`) —
   note the IP address it shows.
2. Open the StreamCam app on your phone.
3. First launch: type in the laptop's IP (e.g. `192.168.1.42:8080`) → **Connect**.
   It's saved from then on — the app opens straight to the live stream every
   time.
4. Tap the ⚙ icon any time to change the saved address (e.g. new Wi-Fi network).
5. **Start/Stop Recording** captures the stream and opens the native
   share sheet so you can save it to Photos/Files.

## Notes

- Phone and laptop must be on the **same Wi-Fi network**.
- If the laptop's IP changes (new network, DHCP renewal), just re-enter it
  via the ⚙ settings screen — no rebuild needed, since the address is stored
  as app data, not hardcoded.
- Publishing to the Play Store / App Store later just means signing the
  release build with your own keys — the code here doesn't need to change.
