# Files still to bring into the repo

The repo layout mirrors the `MotoNodeIQ` folder on the PC (reorganized 2026-10-10). Docs, BOMs,
check reports and the telemetry source are in. The KiCad design files and Python generators are
several MB each, so push them from the PC with git rather than through a cloud session.

## What to copy

| PC folder (`MotoNodeIQ\...`) | Repo folder | Notes |
|---|---|---|
| `Boards\generator\` | `Boards/generator/` | Skip `__pycache__/` (ignored) |
| `Boards\hub\`, `front\`, `rear\` | same | `.kicad_*`, `fab/`, `reports/` |
| `Boards\nodeiq_front_revG\` | same | `.kicad_*`, `NodeIQ.kicad_sym`, BOM, PDF, `reports/` |
| `Ignition\RevE\` | `Ignition/RevE/` | Whole folder: project, `MotoNode.pretty/`, `3dmodels/`, `fab/`, `pcb_layout/`, `spice/`, `reports/` |
| `Telemetry\MotoNodeTelemetry\` | `Telemetry/MotoNodeTelemetry/` | Already in. Re-copy only if the PC copy is newer |
| `Docs\` | `Docs/` | Already in, except `NodeIQ_Source_Hashes.csv`, left out because it lists local `C:\Users\...` paths |
| `Archive\` | — | Stays on the PC / Drive (large zips, chat logs). See `Archive/README.md` |
| `_Keys\` | **never** | Signing keystore. `.gitignore` blocks it |

## How (Windows, PowerShell)

```powershell
git clone https://github.com/rhetoricguitar3aiEngineer/MotoNode.git
cd MotoNode
git checkout claude/zealous-galileo-jf7j76      # or main, once merged

$SRC = "D:\MotoNodeIQ"                            # adjust to where the MotoNodeIQ folder lives
robocopy "$SRC\Boards"   Boards   /E /XD __pycache__ .claude
robocopy "$SRC\Ignition" Ignition /E

git add -A
git status          # confirm no _Keys, .exe, __pycache__ or *-backups are staged
git commit -m "Add KiCad projects and generators"
git push
```

`robocopy` doesn't overwrite files that are already identical, and leaves the repo's own README/docs
in place. The `.kicad_pcb` files (2–3 MB) are fine in plain git. Consider Git LFS only if gerber zips
and STEP files start piling up.
