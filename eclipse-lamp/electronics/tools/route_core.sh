#!/bin/sh
# Place -> Freerouting (v1.9, headless via xvfb) -> GND pours -> DRC for the core board.
# Freerouting is not fully deterministic, so retry until DRC is clean.
set -e
cd "$(dirname "$0")"
for attempt in 1 2 3 4 5 6; do
  python3 pcb_core.py place
  rm -f ../core/eclipse-core.ses
  (cd ../core && timeout 240 xvfb-run -a java -jar ${FREEROUTING_JAR:-/opt/fr/fr19.jar} \
      -de eclipse-core.dsn -do eclipse-core.ses -mp 40 > /tmp/freerouting.log 2>&1) || true
  pkill -f "^java -jar /opt/fr" || true
  if [ ! -f ../core/eclipse-core.ses ]; then echo "attempt $attempt: router timed out"; continue; fi
  # router ran with +0.01 mm margin on every class; DRC checks the nominal rules
  sed -i 's/"clearance": 0.21,/"clearance": 0.2,/; s/"clearance": 0.19,/"clearance": 0.18,/' ../core/eclipse-core.kicad_pro
  python3 pcb_core.py finish
  out=$(cd ../core && kicad-cli pcb drc --schematic-parity -o drc-report.txt eclipse-core.kicad_pcb)
  echo "attempt $attempt: $(echo "$out" | grep -E 'violations|unconnected|parity' | tr '\n' ' ')"
  if echo "$out" | grep -q "Found 0 violations" && echo "$out" | grep -q "Found 0 unconnected"; then
    exit 0
  fi
done
exit 1
