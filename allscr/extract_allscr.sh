#!/bin/bash

# Exit on errors
set -e

# First we test if the allscr.mrg is in the folder
ALLSCR=./allscr.mrg

# If the file is not here, exit early
if [ ! -f "$ALLSCR" ]; then
	echo "Please put the allscr.mrg file in the folder."
	exit -1
fi

# Check we have the necessary programs
# Include local dir in $PATH temporarily
export PATH=$PATH:`pwd`
if ! command -v mzp_extract &> /dev/null ; then
  echo "Program 'mzp_extract' not found in \$PATH"
  exit -1;
fi
if ! command -v mzx_decompress &> /dev/null ; then
  echo "Program 'mzx_decompress' not found in \$PATH"
  exit -1;
fi

# Make a raw and decompressed folder if they don't exist
mkdir ./raw/ || true
mkdir ./decompressed/ || true

# We extract the allscr.mrg file
echo "Extracting the allscr.mrg file..."
mzp_extract "$ALLSCR" decompressed/

# We move the binary archives to the raw directory
mv ./decompressed/allscr.mrg_0000.bin ./raw
mv ./decompressed/allscr.mrg_0001.bin ./raw
mv ./decompressed/allscr.mrg_0002.bin ./raw

# Extract the text script files
for MZX in ./decompressed/*.bin; do
	# Decompress the mzx files
  echo -ne "Decompressing $MZX\r"
  mzx_decompress "$MZX" "${MZX%.bin}.txt"

	# Replace the ";" by ";\n"
	sed -i -e 's/;/;\n/g' "${MZX%.bin}.txt"

	# Remove the original .bin mzx files
	rm $MZX
done
echo -e "\nDecompression complete"

# Some of the script files seem to have anomalies baked in - explicitly replace
# those lines
echo "Manually patching bad script lines"
sed -i 's/_STCP)21,0);/_STCP(21,0);/' decompressed/allscr.mrg_0143.txt
sed -i 's/_SEFD(5,,,`001:2000)();/_SEFD(5,,,`001:2000);/' decompressed/allscr.mrg_0169.txt
sed -i 's/_MFAD(,,`001:8000,,`011:0)0);/_MFAD(,,`001:8000,,`011:0);/' decompressed/allscr.mrg_0369.txt
sed -i 's/_STZ4(5,498,498,498,498,0,0,0)gb);/_STZ4(5,498,498,498,498,0,0,0);/' decompressed/allscr.mrg_0495.txt
