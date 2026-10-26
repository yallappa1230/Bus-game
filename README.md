# Indian Bus Simulator — GameHub Android Edition

This is a lightweight Panda3D Windows-game prototype intended to be tested inside GameHub's Windows compatibility environment on Android. It is **not guaranteed to launch** on every GameHub version/device. Panda3D's Windows runtime and OpenGL support under the compatibility layer are the main unknowns.

## Best way to try it on your Vivo V29e
1. Upload this folder to a GitHub repository from your phone (GitHub mobile site works; creating the repository and uploading files may be easier in a browser).
2. GitHub Actions will build a Windows executable from `main.py`.
3. When the workflow finishes, open its run and download the `IndianBusSimulator-Windows` artifact.
4. Extract the artifact in Android storage.
5. In GameHub, add/import `IndianBusSimulator.exe` (or launch the executable from the imported folder if your GameHub build supports it).
6. Start at 960x540. If it crashes, try the Stable/Compatible preset available in your GameHub version.

## What works in this prototype
- Simple 3D road and sparse scenery
- Government and private coach color schemes
- Large on-screen tap controls: accelerator toggle, brake toggle, steering taps, camera switch, bus switch
- Keyboard controls: W/S/A/D, C, 1/2, Esc
- No external model files required

## Build locally (on a Windows PC)
Install Python 3.11, then:
```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name IndianBusSimulator --collect-all panda3d --collect-all direct main.py
```
The executable is in `dist/IndianBusSimulator/IndianBusSimulator.exe` (onedir build is used because Panda3D packages data/plugins more reliably than a single-file executable).

## Honest limitations
- Not tested inside GameHub or on a Vivo V29e; compatibility is not guaranteed.
- The game is a low-poly arcade prototype, not a complete commercial simulator.
- Touch buttons are tap/toggle controls, not analog steering.
- Multiplayer is not implemented in this mobile build. It should be added after single-player stability is confirmed.
- Building a Windows executable with GitHub Actions does not prove GameHub compatibility; test the artifact on the phone.
- The game has no licensed real bus models or official transport branding.
