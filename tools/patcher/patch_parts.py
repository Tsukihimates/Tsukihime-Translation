#!/usr/bin/env python3

import os
import re
import subprocess
import multiprocessing
import sys
import stat


PARTS_BASENAME = '_mrgs/parts'
OUTPUT_DIR = '_new_mrgs/'
OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, 'parts')
MRG_TEMP_DIR = '.parts_extracted'
PNG_TEMP_DIR = '.parts_dds'
PNG_SOURCE_DIR = '../../images/parts/'
REPLACER = 'bntx_replace/bntx_replace.py'


def compress_nxgz(args):
    decompressed_file = args[0]
    compressed_file = args[1]
    # print("Compressing %s..." % compressed_file)
    subprocess.run(['nxgx_compress', decompressed_file, compressed_file])


def main():
    # Make temp dirs
    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Unpack allui
    subprocess.run(['mrg_extract', PARTS_BASENAME, MRG_TEMP_DIR])

    # Decompress all NXGZ files
    bntx_to_recompress = []
    dat_files = []
    for entry in os.scandir(MRG_TEMP_DIR):
        if not entry.is_file():
            continue

        if not entry.path.endswith('.dat'):
            continue
        dat_files.append(entry.path)

    for entry in dat_files:
        decompressed_filename = re.sub('.dat', '.BNTX', entry)
        print("Decompressing %s..." % entry)
        subprocess.run(['nxx_decompress', entry, decompressed_filename])
        bntx_to_recompress.append((decompressed_filename, entry))

    # Convert PNG resources into DDS
    resources_to_inject = []
    patch_dirs = []
    for subdir, dirs, files in os.walk(PNG_SOURCE_DIR):
        for filename in files:
            if not filename.endswith('.png'):
                continue

            new_filename = re.sub('.png', '.dds', filename)
            input_path = os.path.join(subdir, filename)
            input_nxgz = os.path.split(subdir)[-1]
            output_dir = os.path.join(PNG_TEMP_DIR, input_nxgz)
            output_path = os.path.join(output_dir, new_filename)
            os.makedirs(output_dir, exist_ok=True)
            resources_to_inject.append((input_nxgz, new_filename, output_path))
            if input_nxgz not in patch_dirs:
                patch_dirs.append(input_nxgz)

            # If the target is newer than the source, skip
            if os.path.exists(output_path):
                in_stat = os.stat(input_path)
                out_stat = os.stat(output_path)
                if in_stat[stat.ST_MTIME] < out_stat[stat.ST_MTIME]:
                    print("Output file %s newer than input, skipping" % (
                        output_path))
                    continue

            subprocess.run([
                "compressonator", "-fd", "BC7", input_path, output_path])

    # Inject textures into the BNTX files using harphield's tools
    print(patch_dirs)
    for nxgz_name in patch_dirs:
        # Get all the BNTX files that need to be modified
        bntx_matches = [
            name for name in os.scandir(MRG_TEMP_DIR)
            if name.is_file()
            and name.path.endswith(nxgz_name + ".BNTX")
        ]

        # Replace (in-place) this texture in the relevant files
        for match in bntx_matches:
            print("Replacing textures in pack %s" % nxgz_name)
            subprocess.run([
                sys.executable, REPLACER, match.path,
                PNG_TEMP_DIR, MRG_TEMP_DIR, '-d', nxgz_name])

    # Recompress texture files
    print(
        "Performing parallel compression of %d files with %d threads" % (
            len(bntx_to_recompress), multiprocessing.cpu_count()))
    print(bntx_to_recompress)
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        p.map(compress_nxgz, bntx_to_recompress)

    # Re-pack the allui
    mrg_component_files = sorted([
        entry.path for entry in os.scandir(MRG_TEMP_DIR)
        if entry.is_file()
        and entry.path.endswith(".dat")
    ])
    print("Merging final output into %s" % OUTPUT_BASENAME)
    subprocess.run(['mrg_pack', OUTPUT_BASENAME] + mrg_component_files)


if __name__ == '__main__':
    main()
