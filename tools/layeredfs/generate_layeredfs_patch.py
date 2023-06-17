#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

IPS_FILENAME = "F4B3318D56031E4550EEDDCB12D28FFB78D8397E.ips"

# Hardcoded to avoid people needing to set up rust.
IPS_DATA = b'PATCH\x0c[\x18\x00\x04\xe0\x03\t\xaa\x0c\x06\xcc\x00\x04\x1f \x03\xd5\x0c[$\x00\x04-\x01\x00\x14\x0b\xe9l\x00\x0c[\x19\x00\x94\x1f\x01\x00q\xe0\x0f\x00T\x0cN\xd8\x000\x1f\x00\x04ql\x00\x00T(\x00\x80R\xc0\x03_\xd6\x1f8@q\xab\x00\x00T\x1f<@ql\x00\x00T(\x00\x80R\xc0\x03_\xd6\x08\x00\x80R\xc0\x03_\xd6\x0f\xc0T\x00\x04s^\x01\x14\x0f\xc0h\x00\x04v^\x01\x14EOF'


def parse_args():
    parser = argparse.ArgumentParser(
        description="LayeredFS Patch Generator",
        epilog=(
            "Given the base game NSP and a translation patch NSP, this "
            "script will generate an atmosphere-compatible LayeredFS patch "
            "for switch. Note that this program requires approx 25GiB free "
            "for temp space, and that the final layeredfs patch will also be "
            "approx 20GiB in size due to the way the game is structured "
            "internally."
        )
    )

    parser.add_argument(
        '--base-nsp',
        dest='base_nsp_path',
        action='store',
        help="Path to base game NSP",
    )

    parser.add_argument(
        '--patch-nsp',
        dest='patch_nsp_path',
        action='store',
        help="Path to patch NSP",
    )

    parser.add_argument(
        '--keys',
        dest='keyfile',
        action='store',
        help="Switch prod keys"
    )

    parser.add_argument(
        '--hactool',
        dest='hactool_bin',
        action='store',
        help="Location of hactool binary"
    )

    parser.add_argument(
        '--tmpdir',
        dest='tmpdir',
        action='store',
        help="Location to use for temporary files",
        default=tempfile.gettempdir()
    )

    return parser.parse_args(sys.argv[1:])


def find_hactool():
    # May or may not have extension depending on host OS
    candidate_names = [
        'hactool', 'hactool.exe'
    ]

    # Try both default $PATH and current dir
    path_hints = [None, os.getcwd()]

    for name in candidate_names:
        for path in path_hints:
            hactool_bin = shutil.which(name, path=path)
            if hactool_bin:
                print(f"Found hactool: {hactool_bin}")
                return hactool_bin

    # Not found - complain
    print(
        "Failed to find hactool.\n"
        "Please ensure that the binary is either in $PATH, or copied into "
        "the same directory as this script.\n"
        "Alternatively, provide the location of the binary with the --hactool "
        "flag."
    )
    sys.exit(-1)


def find_keys():
    candidate_keyfile_names = [
        'prod.keys',
        'switch.keys',
    ]
    candidate_basepath_names = [
        os.getcwd(),
        os.path.dirname(__file__),
        os.path.expanduser('~')
    ]

    for filename in candidate_keyfile_names:
        for basepath in candidate_basepath_names:
            keyfile = os.path.join(basepath, filename)
            if os.path.exists(keyfile):
                print(f"Guessing switch keys are in {keyfile}")
                return keyfile

    # Not found - complain
    print(
        "Failed to find keyfile.\n"
        "Please ensure that your switch prod.keys file is in the same "
        "directory as this script, or provide a path to the keys using "
        "the --keys flag."
    )
    sys.exit(-1)


def list_nsps():
    ret = []
    search_paths = [
        os.getcwd(),
        os.path.dirname(__file__)
    ]
    for search_path in search_paths:
        for filename in os.listdir(search_path):
            if not filename.endswith('nsp'):
                continue
            ret.append(os.path.join(search_path, filename))

    return ret


def find_base_nsp():
    # Any NSP file over 20GiB is probably the base game
    candidates = list_nsps()
    for candidate in candidates:
        stats = os.stat(candidate)
        if stats.st_size > 20 * 1024 * 1024 * 1024:
            print(f"Guessing base NSP is {candidate}")
            return candidate

    # Not found - complain
    print(
        "Failed to find base game NSP.\n"
        "Please indicate where it is by specifying --base-nsp."
    )
    sys.exit(-1)


def find_patch_nsp():
    # Any NSP file under 5GiB is probably the patch
    candidates = list_nsps()
    for candidate in candidates:
        stats = os.stat(candidate)
        if stats.st_size < 5 * 1024 * 1024 * 1024:
            print(f"Guessing patch NSP is {candidate}")
            return candidate

    # Not found - complain
    print(
        "Failed to find the patch NSP.\n"
        "Please indicate where it is by specifying --patch-nsp."
    )
    sys.exit(-1)


def generate_layeredfs(args):
    # Extract the basegame NSP to get at the main ROMFS NCA
    base_pfs_tmpdir = os.path.join(args.tmpdir, 'base_pfs')
    base_extract_args = [
        args.hactool_bin,
        '-k', args.keyfile,
        '--intype=pfs0',
        f'--pfs0dir={base_pfs_tmpdir}',
        args.base_nsp_path
    ]
    subprocess.run(base_extract_args, check=True)

    # Extract the patch NSP for its main NCA
    patch_pfs_tmpdir = os.path.join(args.tmpdir, 'patch_pfs')
    patch_extract_args = [
        args.hactool_bin,
        '-k', args.keyfile,
        '--intype=pfs0',
        f'--pfs0dir={patch_pfs_tmpdir}',
        args.patch_nsp_path
    ]
    subprocess.run(patch_extract_args, check=True)

    # The romfs NCA is the biggest from each path
    def find_biggest_nca(path):
        largest = None
        size = None
        for filename in os.listdir(path):
            nca = os.path.join(path, filename)
            stats = os.stat(nca)
            if not size or stats.st_size > size:
                largest = nca
                size = stats.st_size

        return largest
    base_romfs_nca = find_biggest_nca(base_pfs_tmpdir)
    patch_romfs_nca = find_biggest_nca(patch_pfs_tmpdir)
    print("Base ROMFS NCA:  {base_romfs_nca}")
    print("Patch ROMFS NCA: {patch_romfs_nca}")

    # Make sure the output dir exists
    patch_romfs_out = 'atmosphere/contents/01001DC01486A000/romfs'
    try:
        os.makedirs(patch_romfs_out)
    except FileExistsError:
        pass

    # Apply the patch delta to the base NCA
    romfs_extract_args = [
        args.hactool_bin,
        '-k', args.keyfile,
        '-x', patch_romfs_nca,
        '--onlyupdated',
        f'--section1dir={patch_romfs_out}',
        f'--basenca={base_romfs_nca}'
    ]
    subprocess.run(romfs_extract_args, check=True)

    # Clean up the temp dirs
    shutil.rmtree(base_pfs_tmpdir)
    shutil.rmtree(patch_pfs_tmpdir)

    # Also need to stick the IPS patch in the exefs dir.
    exefs_dir = 'atmosphere/exefs_patches/Tsukihimates/'
    try:
        os.makedirs(exefs_dir)
    except FileExistsError:
        pass
    with open(os.path.join(exefs_dir, IPS_FILENAME), 'wb+') as f:
        f.write(IPS_DATA)

    print("Patch generated successfully.")
    print(
        "Merge the contents of the generated atmosphere/ folder with "
        "your switch SD card."
    )


def main():
    args = parse_args()

    # Check we can find our prerequisites
    did_guess = False
    if not args.hactool_bin:
        args.hactool_bin = find_hactool()
        did_guess = True
    if not args.keyfile:
        args.keyfile = find_keys()
        did_guess = True
    if not args.base_nsp_path:
        args.base_nsp_path = find_base_nsp()
        did_guess = True
    if not args.patch_nsp_path:
        args.patch_nsp_path = find_patch_nsp()
        did_guess = True

    # If we had to guess at any of the files, ask if we got it right
    if did_guess:
        print("Do the above values look correct (Y/n)?")
        choice = input().lower()
        if not (choice == 'y' or choice == 'yes' or not choice):
            print("Please specify the incorrect value explicitly.")
            print("See the --help output for more information.")
            sys.exit(-1)

    print("Proceeding with patch generation.")
    generate_layeredfs(args)


if __name__ == '__main__':
    main()
