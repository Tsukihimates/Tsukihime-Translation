import os
import patcher

IMAGE_TRANSLATIONS_FOLDER = os.path.join('..', '..', 'images', 'en_gamecg', 'allpac')

print('Step 1: extract the mrg')

patcher.extract_mrg('allpac', ['-f', '"IMG*"'])

print('Step 2: check what to patch')

want_to_patch = patcher.find_what_to_patch('allpac', IMAGE_TRANSLATIONS_FOLDER, False)

print(want_to_patch)

print('Step 3: Convert png to dds')

patcher.convert_png_to_dds(want_to_patch, IMAGE_TRANSLATIONS_FOLDER, False)

print('Step 4: insert dds to NXGZ')

patcher.replace_textures(want_to_patch, 'allpac')

print('Step 5: rebuild the .mrg and .hed. THIS MIGHT TAKE A LONG TIME so strap yourself in.')

patcher.rebuild_mrg('allpac')

print('All done! Check the _new_mrgs folder.')
