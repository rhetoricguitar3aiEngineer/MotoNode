#!/bin/sh
# Fabrication + documentation outputs for both boards (run after route_core.sh / pcb_halo.py)
set -e
cd "$(dirname "$0")/.."
export KICAD9_3DMODEL_DIR=${KICAD9_3DMODEL_DIR:-/usr/share/kicad/3dmodels}
for b in core hub sprig; do
  P=$b/eclipse-$b
  F=$b/fab
  rm -rf $F && mkdir -p $F/gerbers
  kicad-cli pcb export gerbers -o $F/gerbers/ -l F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts \
      --subtract-soldermask $P.kicad_pcb >/dev/null
  kicad-cli pcb export drill -o $F/gerbers/ --format excellon --excellon-separate-th --generate-map \
      --map-format gerberx2 $P.kicad_pcb >/dev/null
  (cd $F/gerbers && rm -f ../eclipse-$b-gerbers.zip && python3 -c "import zipfile,glob; z=zipfile.ZipFile('../eclipse-$b-gerbers.zip','w',zipfile.ZIP_DEFLATED); [z.write(f) for f in sorted(glob.glob('*'))]")
  kicad-cli pcb export pos -o $F/eclipse-$b-pos.csv --format csv --units mm --side both --exclude-dnp $P.kicad_pcb >/dev/null
  kicad-cli sch export pdf -o $F/eclipse-$b-schematic.pdf $P.kicad_sch >/dev/null
  kicad-cli sch export svg -o $F/ $P.kicad_sch >/dev/null
  kicad-cli pcb export pdf -o $F/eclipse-$b-layout.pdf -l F.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts --mode-separate $P.kicad_pcb >/dev/null 2>&1 || \
  kicad-cli pcb export pdf -o $F/eclipse-$b-layout.pdf -l F.Cu,B.Cu,F.SilkS,Edge.Cuts $P.kicad_pcb >/dev/null
  kicad-cli pcb export step --user-origin 150x150mm --subst-models -f -o $P.step $P.kicad_pcb >/dev/null 2>&1
  kicad-cli pcb export glb --user-origin 150x150mm --subst-models --include-tracks --include-pads \
      --include-silkscreen --include-soldermask -f -o $P.glb $P.kicad_pcb >/dev/null 2>&1
  kicad-cli pcb drc --schematic-parity -o $F/drc-report.txt $P.kicad_pcb | grep -E "violations|unconnected|parity"
  kicad-cli sch erc -o $F/erc-report.txt $P.kicad_sch | grep -E "violations" || true
  echo "$b done"
done
