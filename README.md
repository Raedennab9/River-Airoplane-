# Airplane Shooter — Advanced (River Edition)

A 2-D Pygame shooter featuring:

- Frame-independent movement
- Pause and game-over restart
- Screen shake, particles, and parallax clouds
- Increasing enemy spawn rate and speed
- Health, invincibility frames, and a shield
- Rapid Fire, Spread, and Shield power-ups
- Helicopters, boats, strafers, and enemy projectiles
- Optional image, sound, and music assets

## Quick start (Windows)

Python 3.12 or newer is recommended.

```powershell
cd C:\Games\AirplaneShooter_Advanced
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\run_airplane_advanced.bat
```

If PowerShell blocks activation, use the virtual-environment interpreter directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_airplane_advanced.bat
```

## Controls

- Move: WASD or arrow keys
- Fire: hold Space
- Pause/resume: P
- Restart after game over: R
- Quit: Esc

## Optional assets

Place these files in `assets/`. The game uses drawn graphics and silence when an
asset is absent.

- `player.png` — approximately 64×52, top-down jet
- `enemy.png` — approximately 56×44, helicopter
- `shot.wav`, `explosion.wav`, `powerup.wav`, `hit.wav`
- `music.ogg`

## Packaging

After testing, install PyInstaller and run:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed `
  --add-data "assets;assets" airplane_shooter_advanced.py
```
