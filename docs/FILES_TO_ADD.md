# Files still to bring into the repo

The initial import was done from a cloud session that could read Google Drive but not your PC.
Text documentation, BOMs, check reports and the telemetry source came across. The KiCad design files
and the Python generators did not: they are several MB each and should be pushed from the PC with git.

## Where they are on Drive (backup of the PC)

| Repo destination | Drive source | Notes |
|---|---|---|
| `hardware/ignition/` | `MotoNode_ignition_revE_kicad10.zip` (12 MB) → `MotoNode_ignition_revE_kicad10/MotoNode_RevE/` | Everything in that folder: `.kicad_pro/.kicad_sch/.kicad_pcb/.kicad_dru/.kicad_prl`, `MotoNode.kicad_sym`, `MotoNode.pretty/`, `3dmodels/`, `fab/`, `pcb_layout/`, `spice/`, `reports/`, `fp-lib-table`, `sym-lib-table`, `VERIFICATION_footprints.md`, the schematic PDF and 3D renders. The zip also holds `netlist.py`, `kfinal.py` and the check scripts named in the README. Those aren't loose on Drive |
| `hardware/ignition/` (history) | `MotoNode_ignition_revD2_kicad10.zip` | Only if you want Rev D2 in git history: commit it first, then Rev E on top |
| `hardware/motonodeiq/` | folder `MotoNodeIQ/` → `generator/`, `hub/`, `front/`, `rear/` | Skip `generator/__pycache__/` and `.claude/` |
| `hardware/motonodeiq/nodeiq_front_revG/` | `MotoNodeIQ/nodeiq_front_revG/` | `.kicad_*`, `NodeIQ.kicad_sym`, `sym-lib-table`, BOM CSV, schematic PDF, `reports/` |
| `docs/reference/` (optional) | `DRE-001_Moto_Command_Center_Printable.pdf`, `Katana 3D Teardown.html` | Reference material |

Not wanted in git: `kicad-*.exe`, other installers, `~$*.docx` / `*.tmp` lock files, Android
`build/` output (the `stableIds.txt` / `compile-file-map.properties` files on Drive are build output).

## How to add them (Windows, PowerShell)

```powershell
git clone https://github.com/rhetoricguitar3aiEngineer/MotoNode.git
cd MotoNode
git checkout claude/zealous-galileo-jf7j76      # or main, once this is merged

# 1. Ignition Rev E: unzip, then copy the project folder over hardware/ignition
Expand-Archive "$HOME\Downloads\MotoNode_ignition_revE_kicad10.zip" -DestinationPath "$env:TEMP\revE"
Copy-Item "$env:TEMP\revE\MotoNode_ignition_revE_kicad10\MotoNode_RevE\*" hardware\ignition\ -Recurse -Force

# 2. MotoNodeIQ: adjust the source path to wherever the MotoNodeIQ folder lives on your PC
$IQ = "$HOME\Documents\MotoNodeIQ"
foreach ($d in "generator","hub","front","rear","nodeiq_front_revG") {
  Copy-Item "$IQ\$d" hardware\motonodeiq\ -Recurse -Force
}

git add -A
git status            # check nothing unexpected (.exe, __pycache__) is staged; .gitignore covers the usual ones
git commit -m "Add KiCad projects and generators"
git push
```

The `.kicad_pcb` files are 2–3 MB each, which is fine for plain git. If you later version a lot of
gerber zips or STEP files, consider Git LFS for `*.zip` and `*.step`.
