#!/bin/bash
for F in *.png; do
  convert -resize 316x285 "$F" `echo "$F" | sed 's/\.png/.thumb.png/'`
done
