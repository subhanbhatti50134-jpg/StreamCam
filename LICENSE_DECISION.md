# License decision — StreamCam

This repository (a camera-streaming desktop tray app + Android companion app)
does **not** yet carry an open-source license. Until a license is added, all
rights are reserved by default.

## Context

StreamCam streams a laptop webcam to a phone over local Wi-Fi (MJPEG over
HTTP). It involves access to the camera and the local network, so the license
should primarily express a warranty disclaimer (no guarantee the stream is
secure or private) and clarify reuse rights.

## Recommended options

### Option A — Proprietary / "All Rights Reserved" (current state)
- You keep full control; no one may legally reuse or distribute the app.
- Appropriate if this is a personal utility.

### Option B — MIT License (permissive)
- Allows others to use, modify, and redistribute the code, including in
  closed-source products.
- Minimal obligations; strong warranty/liability disclaimer.
- Good if you want other developers to learn from or extend it.

## Recommendation

For a personal camera utility, **Option A (no license)** is reasonable. Choose
MIT if you want others to freely reuse the code.

## How to adopt (if choosing MIT)

1. Add a `LICENSE` file at the repository root with the MIT license text.
2. Add copyright: `Copyright (c) 2026 Muhammad Subhan`.
3. Keep this `LICENSE_DECISION.md` as the decision record.

> Do not treat StreamCam as open-source licensed until a `LICENSE` file is
> present.
