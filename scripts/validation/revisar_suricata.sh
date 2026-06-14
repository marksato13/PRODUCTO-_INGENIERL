#!/usr/bin/env bash
OUT="/home/m4rk/ppi-surikata-producto/scripts/validation/suricata_revision.txt"
{
  echo "REVISION SURICATA"
  echo "Fecha: $(date)"
  echo
  echo "===== suricata -V ====="
  suricata -V
  echo
  echo "===== ps aux | grep suricata ====="
  ps aux | grep suricata
  echo
  echo "===== ip a ====="
  ip a
  echo
  echo "===== sudo ls -lh /var/log/suricata/ ====="
  sudo ls -lh /var/log/suricata/
  echo
  echo "===== sudo tail -n 20 /var/log/suricata/eve.json ====="
  sudo tail -n 20 /var/log/suricata/eve.json
  echo
  echo "===== grep -n \"eve-log\" /etc/suricata/suricata.yaml ====="
  grep -n "eve-log" /etc/suricata/suricata.yaml
  echo
  echo "===== grep -n \"types:\" /etc/suricata/suricata.yaml ====="
  grep -n "types:" /etc/suricata/suricata.yaml
  echo
  echo "===== grep -n \"flow\" /etc/suricata/suricata.yaml ====="
  grep -n "flow" /etc/suricata/suricata.yaml
  echo
  echo "===== grep -n \"alert\" /etc/suricata/suricata.yaml ====="
  grep -n "alert" /etc/suricata/suricata.yaml
  echo
  echo "===== grep -n \"stats\" /etc/suricata/suricata.yaml ====="
  grep -n "stats" /etc/suricata/suricata.yaml
  echo
  echo "===== sudo suricata -T -c /etc/suricata/suricata.yaml ====="
  sudo suricata -T -c /etc/suricata/suricata.yaml
  echo
  echo "===== jq -r '.event_type' /var/log/suricata/eve.json | sort | uniq -c ====="
  jq -r '.event_type' /var/log/suricata/eve.json | sort | uniq -c
  echo
  echo "===== grep '\"event_type\":\"flow\"' /var/log/suricata/eve.json | head -n 5 ====="
  grep '"event_type":"flow"' /var/log/suricata/eve.json | head -n 5
  echo
  echo "===== grep '\"event_type\":\"stats\"' /var/log/suricata/eve.json | head -n 5 ====="
  grep '"event_type":"stats"' /var/log/suricata/eve.json | head -n 5
  echo
} > "$OUT" 2>&1
