# 🖐️ Hand Gesture AR Filter

[![JavaScript](https://img.shields.io/badge/JavaScript-ES6%2B-F7DF1E?logo=javascript&logoColor=black)](#)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands%20AI-00C4B4?logo=google&logoColor=white)](#)
[![HTML5 Canvas](https://img.shields.io/badge/HTML5-Canvas%202D-E34F26?logo=html5&logoColor=white)](#)
[![Vercel Ready](https://img.shields.io/badge/Vercel-Deployed-black?logo=vercel&logoColor=white)](#-deploy-to-vercel)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare_Pages-Ready-F38020?logo=cloudflare&logoColor=white)](#-deploy-to-cloudflare-pages)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An ultra-responsive, real-time **Augmented Reality Hand Gesture Filter** powered by Google MediaPipe AI Vision and vanilla WebGL/Canvas 2D image processing. Raise both hands to spawn an interactive 3D perspective AR portal quad between your fingertips, tilt in 3D space with volumetric drop shadows, cycle curated visual shaders by touching your fingertips together, and experience futuristic optical filters with zero latency.

---

## ✨ Features

- **👐 Dual-Hand AR Portal Tracking**: Dynamically tracks both hands to create an elastic 4-corner perspective AR quad between your Index and Thumb fingertips ($p_1, p_2, p_3, p_4$).
- **🌌 Real-Time 3D Spatial Depth & Plane Rotation**:
  - Calculates relative $Z$ depth disparities between hands.
  - Pushing one hand closer to the camera tilts the portal plane in 3D (Yaw up to $\pm 60^\circ$, Pitch up to $\pm 45^\circ$).
  - Projects a dynamic **3D volumetric parallax drop shadow** beneath the floating portal glass.
  - Closer hand receives **perspective foreshortening**, thicker borders ($1.4\times$), and intensified neon specular bloom.
- **🤝 Zero-Mistake Fingertip Touch Gesture**:
  - Physically touching both index fingers and thumbs simultaneously triggers an instant, fluid filter cycle with chromatic burst feedback.
  - 350ms debounced state machine prevents accidental re-triggers until hands reopen.
- **⚡ 1-Euro Adaptive Kinematic Filter**:
  - Eliminates idle finger jitter and trembling ($<1\text{px}$ deadband).
  - Maintains ultra-fast responsive tracking when hands move or spread across the screen ($\beta = 0.85$).
  - **10-Frame Temporal Grace Persistence**: Spreading hands far apart or moving fast never drops or stutters the portal.
- **🎨 10 Curated Real-Time Optical Shaders**:
  1. `01` **🩸 Crimson Noir**: Cyberpunk blood red, deep shadow & porcelain skin posterization.
  2. `02` **🌊 Liquid Chrome Body**: Liquid mercury reflections & glowing tri-color quantum particles strictly on the human body, set against a moody greyish-black room.
  3. `03` **🧊 Crystal Ice Glass**: Crisp frosted glass refraction with sharp procedural fracture veins and specular glints.
  4. `04` **🕳️ Matrix Void ASCII**: Luminous character halos & chromatic aberration on silhouettes.
  5. `05` **📰 Vintage Manga**: Burgundy ink on cream paper $45^\circ$ rotated screentone halftone.
  6. `06` **🩻 Medical X-Ray**: Translucent cyan-blue bone density inversion with radiography scanlines.
  7. `07` **⌨ HD ASCII Matrix**: High-definition full-matrix ASCII rasterization.
  8. `08` **▦ Retro Dither**: Classic $8\times 8$ Bayer ordered matrix dithering.
  9. `09` **♨ Thermal JET**: Simulated infrared false-color thermal vision camera.
  10. `10` **🌸 Rosa Halftone**: Vibrant duotone magenta pop-art halftone dots.
- **🪟 Frosted Glass UI & Customization**:
  - Modern dark-mode glassmorphic dock, real-time FPS counter, HUD status pill, and quick keyboard shortcuts.
  - Fully customizable border thickness, neon glow styles, anchor nodes, and elastic membrane bending.
  - Snapshot tool to capture and download high-resolution AR photos.

---

## 🎮 Keyboard Shortcuts

| Key | Action | Description |
| :--- | :--- | :--- |
| **`1` – `9`**, **`0`** | **Direct Filter Select** | Jump directly to Shaders 01 through 10 |
| **`Space`** / **`Enter`** | **Next Filter** | Advance to the next visual shader |
| **`[`** / **`]`** | **Prev / Next Filter** | Step backward or forward through filters |
| **`S`** | **Toggle Skeleton** | Show/hide 21-landmark hand skeletal joint overlay |
| **`C`** | **Capture Photo** | Take and download high-resolution AR snapshot |
| **`F`** | **Fullscreen** | Toggle borderless fullscreen viewport |
| **`O`** | **Settings** | Open frosted glass customization modal |
| **`Esc`** | **Close Modal / Menu** | Dismiss popup or dropdown menu |

---

## 🛠️ Project Structure

```text
├── vercel.json         # Vercel deployment config, security headers & static caching
├── _headers            # Cloudflare Pages security & permissions headers (camera=*)
├── package.json        # Standard project metadata & dev scripts
├── index.html          # Semantic HTML5 UI, frosted glass HUD, tag cloud & modals
├── styles.css          # Ultra-premium CSS3 design system with frosted glass tokens
├── README.md           # Project documentation and quickstart guide
├── AGENTS.md           # Architecture, mathematical formulas & developer specification
├── assets/
│   └── test.jpg        # High-resolution 71-glyph ASCII texture strip (5680x80)
└── js/
    ├── app.js          # Main application lifecycle, render loop & event handlers
    ├── tracking.js     # MediaPipe Hands AI, 1-Euro filter, 3D depth & temporal grace
    ├── geometry.js     # 3D perspective quad rendering, volumetric shadow & touch detector
    └── filters.js      # Curated 10-shader real-time pixel processing pipeline
```

## 💻 Running Locally

### Prerequisites
- Modern web browser (Google Chrome, Microsoft Edge, Brave, Firefox, or Safari) with webcam support.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/AadishY/Hand-Gesture-Filter.git
   cd Hand-Gesture-Filter
   ```

2. **Start a local HTTP server**:
   ```bash
   # Using Python 3
   python -m http.server 8000

   # Or using Node.js
   npx serve .
   ```

3. **Open in browser**:
   Visit [**http://localhost:8000**](http://localhost:8000), allow camera access, and click **"START AR EXPERIENCE"**.

---

## 🔬 Mathematical & Kinematic Pipeline

### 1. 1-Euro Adaptive Temporal Filter
Filters micro-tremors without introducing perceptual latency:
$$\alpha = \frac{2\pi f_c \Delta t}{2\pi f_c \Delta t + 1}, \quad f_c = f_{\min} + \beta \cdot \text{velocity}$$
- $f_{\min} = 0.06\text{ Hz}$ (freezes stationary hand jitter)
- $\beta = 0.85$ (instantaneous responsiveness during fast motion)
- Subpixel deadband: $\Delta d < 1.0\text{ px} \implies \hat{x}_t = \hat{x}_{t-1}$

### 2. Relative 3D Depth Disparity & Yaw/Pitch Rotation
Relative hand depth ($Z$) is estimated from palm physical scale in image coordinates:
$$Z_{\text{hand}} = \frac{1}{\max(0.04, \|\mathbf{p}_{\text{wrist}} - \mathbf{p}_{\text{middle\_mcp}}\|)} \cdot 0.75 + z_{\text{raw}} \cdot 2.5$$
$$\Delta Z = \frac{Z_{\text{right}} - Z_{\text{left}}}{\frac{Z_{\text{right}} + Z_{\text{left}}}{2}}, \quad \theta_{\text{yaw}} = \text{clamp}(\Delta Z \cdot 48^\circ, -60^\circ, 60^\circ)$$

---

## 🛡️ License

Distributed under the **MIT License**. See `LICENSE` for more information.
