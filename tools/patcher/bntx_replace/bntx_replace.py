import os
import argparse
import pathlib
import bntx as BNTX


def replace_texture(bntx, dds_path, texture):
    # find the texture in the pack that we want replaced
    texture_to_replace = None
    replace_texture_index = None
    i = 0
    for t in bntx.textures:
        if t.name.lower() == texture.lower():
            texture_to_replace = t
            replace_texture_index = i
            break
        i += 1

    if texture_to_replace is None:
        print('Cannot find texture to replace: ' + texture)
        return bntx

    tile_mode = texture_to_replace.tileMode
    srgb = 1
    sparse_binding = texture_to_replace.sparseBinding
    sparse_residency = texture_to_replace.sparseResidency
    import_mips = 0

    replaced_texture = bntx.replace(texture_to_replace, tile_mode, srgb, sparse_binding, sparse_residency,
                                    import_mips,
                                    dds_path)
    if replaced_texture:
        bntx.textures[replace_texture_index] = replaced_texture

    return bntx


parser = argparse.ArgumentParser(description='Replace a texture in a BNTX file.')
parser.add_argument('bntx_file', type=pathlib.Path, help='File that we replace in.')
parser.add_argument('dds_file', type=pathlib.Path, help='A dds file or folder of ddses that we want to insert.')
parser.add_argument('output_folder', type=pathlib.Path, help='Where to output the new file.')
parser.add_argument('-t', metavar='--texture_name', type=str, help='Name of the texture that you want to replace. If '
                                                                   'not set, it will use the dds file to deduce the '
                                                                   'texture name.')
parser.add_argument('-d', metavar='--directory_name', type=str, help='Name of subdirectory where the dds files are')


args = parser.parse_args()

print(args)

btnx_file_path = args.bntx_file
bntx_file_split = os.path.split(btnx_file_path)
if args.d is None:
    bntx_file_base_name = os.path.splitext(bntx_file_split[1])[0]
else:
    bntx_file_base_name = args.d
dds_file_path = args.dds_file
output_folder = args.output_folder

if not os.path.isdir(output_folder):
    raise SystemExit('Output folder must be a directory!')

if os.path.isdir(dds_file_path):
    if args.t is not None:
        raise SystemExit('-t is valid only for single files, not folders.')

    bntx_file = BNTX.File()
    returnCode = bntx_file.readFromFile(btnx_file_path)
    if returnCode:
        raise SystemExit('Error while opening the BNTX file.')

    found = False
    for (dirpath, dirnames, filenames) in os.walk(dds_file_path):
        for dirname in dirnames:
            if dirname == bntx_file_base_name:
                found = True
                print('found ' + os.path.join(dirpath, dirname))
                for (bf_dirpath, bf_dirnames, bf_filenames) in os.walk(os.path.join(dirpath, dirname)):
                    for filename in bf_filenames:
                        file_path = os.path.join(bf_dirpath, filename)
                        texture_name = os.path.splitext(filename)[0]

                        print('Replacing ' + texture_name)
                        bntx_file = replace_texture(bntx_file, file_path, texture_name)
                break

    if not found:
        raise SystemExit('Folder for patching ' + bntx_file_base_name + ' not found!')
else:
    if args.t is None:
        texture_name = os.path.splitext(os.path.split(dds_file_path)[1])[0]
    else:
        texture_name = args.t

    bntx_file = BNTX.File()
    returnCode = bntx_file.readFromFile(btnx_file_path)
    if returnCode:
        raise SystemExit('Error while opening the BNTX file.')

    bntx_file = replace_texture(bntx_file, dds_file_path, texture_name)

# save to a new file
new_path = os.path.join(output_folder, bntx_file_split[1])

with open(new_path, 'wb') as out:
    out.write(bntx_file.save())
