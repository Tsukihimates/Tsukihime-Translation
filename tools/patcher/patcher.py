import os
import shutil
import subprocess
import sys

if os.name == 'nt':
    QUICKBMS = os.path.join('quickbms', 'quickbms_4gb_files.exe')
    COMPRESSONATOR = "\\Compressonator_4.2.5185\\bin\\CLI\\compressonatorcli.exe"
else:
    QUICKBMS = './quickbms/quickbms_4gb_files'
    COMPRESSONATOR = './compressonator/compressonatorcli'

REPLACER = os.path.join('bntx_replace/bntx_replace.py')


def run_process(process):
    out = ''
    while True:
        suboutput = process.stdout.readline()
        print(suboutput.strip())
        out += suboutput
        code = process.poll()
        if code is not None:
            print('RETURN CODE', code)
            # Process has finished, read rest of the output
            for o in process.stdout.readlines():
                print(o.strip())
                out += o
            break

    return code, out


# mrg_name without extension
def extract_mrg(mrg_name, options=None):
    if options is None:
        options = []

    quickbms_done = False
    if not os.path.exists('_unpatched'):
        os.mkdir('_unpatched')
    elif not os.path.exists(os.path.join('_unpatched', mrg_name)):
        os.mkdir(os.path.join('_unpatched', mrg_name))
    elif os.listdir(os.path.join('_unpatched', mrg_name)):
        quickbms_done = True  # is not empty, so I guess stuff is in there

    if not quickbms_done:
        quickbms_process = subprocess.Popen([QUICKBMS] + options + ['-Y', os.path.join('quickbms', 'tsuki.bms'),
                                             os.path.join('_mrgs', mrg_name + '.hed'),
                                             os.path.join('_unpatched', mrg_name)],
                                            stdout=subprocess.PIPE,
                                            universal_newlines=True)

        return_code, output = run_process(quickbms_process)

        if return_code != 0:
            raise SystemExit('Error while extracting with quickbms')
    else:
        print('Files already extracted, continuing.')


# use directories=False if we only have one folder with many PNGs that will go 1:1 with NXGZs (like allpac)
def find_what_to_patch(mrg_name, image_dir, directories=True):
    texture_files = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.join('_unpatched', mrg_name)):
        for filename in filenames:
            split = os.path.splitext(filename)
            if split[1].lower() == '.nxgz' or split[1].lower() == '.nxz':
                texture_files.append(filename)

    want_to_patch = []
    for (dirpath, dirnames, filenames) in os.walk(image_dir):
        if directories:
            for dirname in dirnames:
                for tf in texture_files:
                    split = os.path.splitext(tf)
                    if split[0].lower() == dirname.lower():
                        want_to_patch.append(tf)
        else:
            for filename in filenames:
                file_split = os.path.splitext(filename)
                for tf in texture_files:
                    split = os.path.splitext(tf)
                    if split[0].lower() == file_split[0].lower():
                        want_to_patch.append(tf)

    return want_to_patch


def convert_png_to_dds(want_to_patch, image_dir, directories=True):
    if not os.path.exists('_replace'):
        os.mkdir('_replace')

    for want in want_to_patch:
        want_dir = os.path.splitext(want)[0].upper()

        if directories:
            walk_dir = os.path.join(image_dir, want_dir)
        else:
            walk_dir = image_dir

        for (dirpath, dirnames, filenames) in os.walk(walk_dir):
            for filename in filenames:
                split = os.path.splitext(filename)

                if not directories:
                    want_dir = split[0].upper()

                if split[1].lower() == '.png':  # convert png to dds into the _replace folder
                    if not os.path.exists(os.path.join('_replace', want_dir)):
                        os.mkdir(os.path.join('_replace', want_dir))

                    dds_path = os.path.join('_replace', want_dir, split[0] + '.dds')

                    if not os.path.exists(dds_path):
                        # print(os.path.join('_replace', want_dir, split[0] + '.dds'))
                        comp_process = subprocess.Popen(
                            [COMPRESSONATOR, '-fd', 'BC7', os.path.join(dirpath, filename),
                             dds_path
                             ],
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
                        return_code, output = run_process(comp_process)
                        if return_code != 0:
                            raise SystemExit('DDS conversion failed! ' + filename)


def replace_textures(want_to_patch, mrg_name):
    if not os.path.exists('_patched'):
        os.mkdir('_patched')
    if not os.path.exists(os.path.join('_patched', mrg_name)):
        os.mkdir(os.path.join('_patched', mrg_name))

    for want in want_to_patch:
        print('Patching ' + want)
        replace_process = subprocess.Popen([sys.executable, REPLACER, os.path.join('_unpatched', mrg_name, want),
                                            os.path.join('_replace'), os.path.join('_patched', mrg_name)],
                                           stdout=subprocess.PIPE,
                                           universal_newlines=True)

        return_code, output = run_process(replace_process)
        if return_code != 0:
            raise SystemExit('Texture patching failed! ' + want)


def rebuild_mrg(mrg_name):
    if not os.path.exists('_new_mrgs'):
        os.mkdir('_new_mrgs')

    print('Copying files...')

    shutil.copyfile(os.path.join('_mrgs', mrg_name + '.mrg'), os.path.join('_new_mrgs', mrg_name + '.mrg'))
    shutil.copyfile(os.path.join('_mrgs', mrg_name + '.hed'), os.path.join('_new_mrgs', mrg_name + '.hed'))
    shutil.copyfile(os.path.join('_mrgs', mrg_name + '.nam'), os.path.join('_new_mrgs', mrg_name + '.nam'))

    quickbms_process = subprocess.Popen(
        [QUICKBMS, '-Y', '-w', '-r', '-r', os.path.join('quickbms', 'tsuki.bms'),
         os.path.join('_new_mrgs', mrg_name + '.hed'), os.path.join('_patched', mrg_name)],
        stdout=subprocess.PIPE,
        universal_newlines=True)

    return_code, output = run_process(quickbms_process)
    if return_code != 0:
        raise SystemExit('MRG rebuild failed!')
