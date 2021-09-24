#!/bin/bash
set -e

# Make build dir if not exists
mkdir -p build/ || true

# Re-compress each of the script text files
for F in $(ls decompressed); do
  echo -ne "Compressing $F\r"
  # Remove newlines
  cat "retimed/$F" | tr -d '\n' > "build/$F"
  # Compress
  mzx_compress "build/$F" build/"`echo $F | sed 's/txt/bin/'`"
done
echo "Finished ompressing script files"

# Add the binary archives into the build dir
echo "Adding binary archives to build"
cp raw/allscr.mrg_0000.bin build/
cp raw/allscr.mrg_0001.bin build/
cp raw/allscr.mrg_0002.bin build/

# Repack all of the files in the build dir into a mrg
# Note that this relies on the glob ordering of the input names being in-order
echo "Packing final mrg file"
mzp_compress allscr_repacked.mrg build/*.bin
