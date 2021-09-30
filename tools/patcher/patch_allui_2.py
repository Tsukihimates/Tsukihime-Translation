#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import stat

import rebuild_sysmes


ALLUI_BASENAME = '_mrgs/allui'
OUTPUT_DIR = '_new_mrgs/'
OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, 'allui')
MRG_TEMP_DIR = '.allui_extracted'
PNG_TEMP_DIR = '.user_interface_dds'
USER_INTERFACE_DIR = '../../images/en_user_interface/'
REPLACER = 'bntx_replace/bntx_replace.py'
SCRIPT_TRANSLATIONS_FOLDER = '../../script'


def main():
    # Make temp dirs
    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Unpack allui
    subprocess.run(['mrg_extract', ALLUI_BASENAME, MRG_TEMP_DIR])

    # Decompress all NXGZ files
    bntx_to_recompress = []
    for entry in os.scandir(MRG_TEMP_DIR):
        if not entry.is_file():
            continue
        if not entry.path.endswith('NXGZ.dat'):
            continue
        decompressed_filename = re.sub('NXGZ.dat', 'BNTX', entry.path)
        print("Decompressing %s..." % entry.path)
        subprocess.run(['nxx_decompress', entry.path, decompressed_filename])
        bntx_to_recompress.append((decompressed_filename, entry.path))

    # Convert PNG resources into DDS
    resources_to_inject = []
    for subdir, dirs, files in os.walk(USER_INTERFACE_DIR):
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

            # If the target is newer than the source, skip
            if os.path.exists(output_path):
                in_stat = os.stat(input_path)
                out_stat = os.stat(output_path)
                if in_stat[stat.ST_MTIME] < out_stat[stat.ST_MTIME]:
                    print("Output file %s newer than input, skipping" % output_path)
                    continue

            subprocess.run([
                "compressonator", "-fd", "BC7", input_path, output_path])

    # Inject textures into the BNTX files using harphield's tools
    for (nxgz_name, file_name, file_path) in resources_to_inject:
        # Get all the BNTX files that need to be modified
        bntx_matches = [
            name for name in os.scandir(MRG_TEMP_DIR)
            if name.is_file()
            and name.path.endswith(nxgz_name + ".BNTX")
        ]

        # Replace (in-place) this texture in the relevant files
        for match in bntx_matches:
            print("Replacing texture %s in pack %s" % (file_name, match.path))
            subprocess.run([sys.executable, REPLACER, match.path, file_path, MRG_TEMP_DIR])

    # Rebuild the SYSMES strings table (in place)
    rebuild_sysmes.rebuild_sysmes(
        os.path.join(MRG_TEMP_DIR, 'allui.0024.SYSMES_TEXT.DAT.dat'),
        os.path.join(
            SCRIPT_TRANSLATIONS_FOLDER,
            'system_strings',
            'sysmes_text.en'),
        os.path.join(MRG_TEMP_DIR, 'allui.0024.SYSMES_TEXT.DAT.dat')
    )

    # Recompress texture files
    for decompressed_file, compressed_file in bntx_to_recompress:
        print("Compressing %s..." % compressed_file)
        subprocess.run(['nxgx_compress', decompressed_file, compressed_file])

    # Re-pack the allui
    mrg_component_files = [
        entry.path for entry in os.scandir(MRG_TEMP_DIR)
        if entry.is_file()
    ]
    sorted(mrg_component_files)
    subprocess.run(['mrg_pack', OUTPUT_BASENAME, '--names', 'mrg_names.txt'] + mrg_component_files)


if __name__ == '__main__':
    main()
