#!/bin/bash
for F in *.png; do
  convert -resize 316x285 "$F" "thumb/$F"
done
