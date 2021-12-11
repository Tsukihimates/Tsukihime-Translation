#!/bin/bash
set -e

# Make build dirs if not exists
mkdir -p patched/ || true
mkdir -p build/ || true

# Copy the retimed files into the build dir
cp retimed/* patched/

# Apply manual patches
pushd patched
for F in $(ls ../manual_tweaks/); do
  patch -p0 < "../manual_tweaks/$F"
done
popd

# Re-compress each of the script text files
for F in $(ls patched/); do
  echo -ne "Compressing $F\r"
  # Remove newlines
  cat "patched/$F" | tr -d '\n' > "build/$F"
  # Compress
  mzx_compress "build/$F" build/"`echo $F | sed 's/txt/bin/'`" &
done
wait
echo "Finished compressing script files       "

# Add the binary archives into the build dir
echo "Adding binary archives to build"
cp raw/allscr.mrg_0000.bin build/
cp raw/allscr.mrg_0001.bin build/
cp raw/allscr.mrg_0002.bin build/

# Repack all of the files in the build dir into a mrg
# Note that this relies on the glob ordering of the input names being in-order
echo "Packing final mrg file"
mzp_compress allscr_repacked.mrg build/*.bin
