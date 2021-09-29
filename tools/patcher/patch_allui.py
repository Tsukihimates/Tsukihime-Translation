import os
import rebuild_sysmes
import patcher

IMAGE_TRANSLATIONS_FOLDER = os.path.join('..', '..', 'images', 'en_user_interface')
SCRIPT_TRANSLATIONS_FOLDER = os.path.join('..', '..', 'script')

# if we don't have allui.mrg extracted yet, extract it with quickbms
patcher.extract_mrg('allui')

print('Step 2: check what to patch')

want_to_patch = patcher.find_what_to_patch('allui', IMAGE_TRANSLATIONS_FOLDER)

print(want_to_patch)

print('Step 3: Convert png to dds')

patcher.convert_png_to_dds(want_to_patch, IMAGE_TRANSLATIONS_FOLDER)

print('Step 4: insert dds to NXGZ')

patcher.replace_textures(want_to_patch, 'allui')

print('Step 5: insert translated sysmes_text')

rebuild_sysmes.rebuild_sysmes(os.path.join('_unpatched', 'allui', 'SYSMES_TEXT.DAT'),
                              os.path.join(os.path.join(SCRIPT_TRANSLATIONS_FOLDER, 'system_strings', 'sysmes_text.en')),
                              os.path.join('_patched', 'allui', 'SYSMES_TEXT.DAT'))

print('Step 6: rebuild the .mrg and .hed. THIS MIGHT TAKE A LONG TIME so strap yourself in.')

patcher.rebuild_mrg('allui')

print('All done! Check the _new_mrgs folder.')
