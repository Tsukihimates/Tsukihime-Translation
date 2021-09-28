import os
import shutil
import subprocess
import rebuild_sysmes

IMAGE_TRANSLATIONS_FOLDER = os.path.join('..', '..', 'images', 'en_user_interface')
SCRIPT_TRANSLATIONS_FOLDER = os.path.join('..', '..', 'script')

if os.name == 'nt':
    QUICKBMS = os.path.join('quickbms', 'quickbms_4gb_files.exe')
    COMPRESSONATOR = os.path.join('compressonator', 'CompressonatorCLI_x64_4.2.5185.exe')
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


# if we don't have allui.mrg extracted yet, extract it with quickbms
quickbms_done = False
if not os.path.exists('_unpatched'):
    os.mkdir('_unpatched')
elif not os.path.exists(os.path.join('_unpatched', 'allui')):
    os.mkdir(os.path.join('_unpatched', 'allui'))
elif os.listdir(os.path.join('_unpatched', 'allui')):
    quickbms_done = True    # is not empty, so I guess stuff is in there

print('Step 1: extract the MRG')

if not quickbms_done:
    quickbms_process = subprocess.Popen([QUICKBMS, '-Y', os.path.join('quickbms', 'tsuki.bms'),
                                         os.path.join('_mrgs', 'allui.hed'), os.path.join('_unpatched', 'allui')],
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)

    return_code, output = run_process(quickbms_process)

    if return_code != 0:
        raise SystemExit('Error while extracting with quickbms')
else:
    print('Files already extracted, continuing to step 2')

print('Step 2: check what to patch')

texture_files = []
for (dirpath, dirnames, filenames) in os.walk('_unpatched/allui'):
    for filename in filenames:
        split = os.path.splitext(filename)
        if split[1] == '.NXGZ' or split[1] == '.NXZ':
            texture_files.append(filename)

want_to_patch = []
for (dirpath, dirnames, filenames) in os.walk(IMAGE_TRANSLATIONS_FOLDER):
    for dirname in dirnames:
        for tf in texture_files:
            split = os.path.splitext(tf)
            if split[0] == dirname:
                want_to_patch.append(tf)

print(want_to_patch)

print('Step 3: Convert png to dds')

if not os.path.exists('_replace'):
    os.mkdir('_replace')

for want in want_to_patch:
    want_dir = os.path.splitext(want)[0]
    for (dirpath, dirnames, filenames) in os.walk(os.path.join(IMAGE_TRANSLATIONS_FOLDER, want_dir)):
        for filename in filenames:
            split = os.path.splitext(filename)
            if split[1] == '.png':  # convert png to dds into the _replace folder
                if not os.path.exists(os.path.join('_replace', want_dir)):
                    os.mkdir(os.path.join('_replace', want_dir))

                dds_path = os.path.join('_replace', want_dir, split[0] + '.dds')

                if not os.path.exists(dds_path):
                    # print(os.path.join('_replace', want_dir, split[0] + '.dds'))
                    comp_process = subprocess.Popen([COMPRESSONATOR, '-fd', 'BC7', os.path.join(dirpath, filename),
                                                     os.path.join('_replace', want_dir, split[0] + '.dds')
                                                     ],
                                                    stdout=subprocess.PIPE,
                                                    universal_newlines=True)
                    return_code, output = run_process(comp_process)

print('Step 4: insert dds to NXGZ')

if not os.path.exists('_patched'):
    os.mkdir('_patched')
if not os.path.exists(os.path.join('_patched', 'allui')):
    os.mkdir(os.path.join('_patched', 'allui'))

for want in want_to_patch:
    want_dir = os.path.splitext(want)[0]
    print('Patching ' + want)
    replace_process = subprocess.Popen(['python3', REPLACER, os.path.join('_unpatched', 'allui', want),
                                        os.path.join('_replace'), os.path.join('_patched', 'allui')],
                                       stdout=subprocess.PIPE,
                                       universal_newlines=True)

    return_code, output = run_process(replace_process)

print('Step 5: insert translated sysmes_text')

rebuild_sysmes.rebuild_sysmes(os.path.join('_unpatched', 'allui', 'SYSMES_TEXT.DAT'),
                              os.path.join(os.path.join(SCRIPT_TRANSLATIONS_FOLDER, 'system_strings', 'sysmes_text.en')),
                              os.path.join('_patched', 'allui', 'SYSMES_TEXT.DAT'))

print('Step 6: rebuild the .mrg and .hed. THIS MIGHT TAKE A LONG TIME so strap yourself in.')

if not os.path.exists('_new_mrgs'):
    os.mkdir('_new_mrgs')

shutil.copyfile(os.path.join('_mrgs', 'allui.mrg'), os.path.join('_new_mrgs', 'allui.mrg'))
shutil.copyfile(os.path.join('_mrgs', 'allui.hed'), os.path.join('_new_mrgs', 'allui.hed'))
shutil.copyfile(os.path.join('_mrgs', 'allui.nam'), os.path.join('_new_mrgs', 'allui.nam'))

quickbms_process = subprocess.Popen([QUICKBMS, '-Y', '-w', '-r', '-r', os.path.join('quickbms', 'tsuki.bms'),
                                     os.path.join('_new_mrgs', 'allui.hed'), os.path.join('_patched', 'allui')],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True)

return_code, output = run_process(quickbms_process)
