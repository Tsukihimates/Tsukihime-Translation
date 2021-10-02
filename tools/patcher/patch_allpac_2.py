#!/usr/bin/env python3

import os
import re
import subprocess
import hashlib
import multiprocessing
import sys
import stat


# This script is targeted against the v1.0.2 version of allpac.
# Other file versions may not have the same number of entries
EXPECTED_ALLPAC_MD5 = ''

# Where should we look for the input files
ALLPAC_BASENAME = '_mrgs/allpac'

# Where to place the updated files
OUTPUT_DIR = '_new_mrgs/'
OUTPUT_BASENAME = os.path.join(OUTPUT_DIR, 'allpac')

# Temporary directory for extracted files
MRG_TEMP_DIR = '.allpac_extracted'

# Temporary dir for DDS versions of images to insert
PNG_TEMP_DIR = '.gamecg_dds'

# Source dir with game CG images to replace
GAMECG_DIR = '../../images/en_gamecg/allpac'

# External texture replacement program
REPLACER = 'bntx_replace/bntx_replace.py'


class MrgEntry:
    def __init__(self, index, offset, size, uncompressed_size, name=None):
        self._index = index
        self._offset = offset
        self._size = size
        self._uncompressed_size = uncompressed_size
        self._name = name


def get_mrg_entries(basename):
    raw_csv = subprocess.check_output(['mrg_info', '--csv', basename])
    ret = []
    for row in raw_csv.split(b'\n'):
        split = row.split(b',')
        if len(split) == 1:
            break
        ret.append(MrgEntry(*split))
    return ret


def compress_nxgz(args):
    decompressed_file = args[0]
    compressed_file = args[1]
    # print("Compressing %s..." % compressed_file)
    subprocess.run(['nxgx_compress', decompressed_file, compressed_file])


def md5_file(filename):
    with open(filename, 'rb') as f:
        context = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            context.update(chunk)
            chunk = f.read(8192)
        return context.hexdigest()


def get_images_to_insert():
    ret = {}
    for entry in os.scandir(PNG_TEMP_DIR):
        if entry.is_file():
            ret[entry.name] = entry.path
    return ret


def main():
    # Test that input allpac files exist and are of the expected version
    if False:
        print("Checking integriry of input allpac...")
        input_checksum = md5_file(ALLPAC_BASENAME + ".mrg")
        if input_checksum != EXPECTED_ALLPAC_MD5:
            print(
                "Input allpac has unexpected MD5sum '%s' - "
                "expected a version 1.0.2 allpac with MD5sum '%s'" % (
                    input_checksum,
                    EXPECTED_ALLPAC_MD5
                )
            )

    # Read the MRG entries so that we can scan through for files to replace
    mrg_entries = get_mrg_entries(ALLPAC_BASENAME)

    # Make temp dirs
    for dirname in [MRG_TEMP_DIR, PNG_TEMP_DIR, OUTPUT_DIR]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # Convert PNG resources into DDS
    resources_to_inject = []
    for subdir, dirs, files in os.walk(GAMECG_DIR):
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

    # Fetch the list of image names that we want to substitute
    images_to_insert = get_images_to_insert()

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

    # Recompress texture files
    print("Performing parallel compression of %d files with %d threads" % (len(bntx_to_recompress), multiprocessing.cpu_count()))
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        p.map(compress_nxgz, bntx_to_recompress)

    # Re-pack the allpac
    mrg_component_files = sorted([
        entry.path for entry in os.scandir(MRG_TEMP_DIR)
        if entry.is_file()
        and entry.path.endswith(".dat")
    ])
    print("Merging final output into %s" % OUTPUT_BASENAME)
    subprocess.run(['mrg_pack', OUTPUT_BASENAME, '--names', 'mrg_names.txt'] + mrg_component_files)


if __name__ == '__main__':
    main()
