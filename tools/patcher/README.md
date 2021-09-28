# HOW TO PATCH YOUR allui.mrg
Well hello there. This tool right here *should* help you in creating your
own nice allui.mrg + allui.hed to put into your emulator's mod folder.

## 1. Download a few tools.

Into the **quickbms** folder you need to download quickbms: http://aluigi.altervista.org/quickbms.htm -
this wonderful swiss army knife tool extracts and rebuilds .mrg files.

Then, for Linux, download compressonatorcli into the **compressonator** folder: https://github.com/GPUOpen-Tools/compressonator/releases/tag/V4.2.5185 -
this tools builds .dds files from .png files to be inserted.
For Windows, just install the CompressonatorCLI software, this script uses the default install path.

## 2. Move the allui 
Put an unaltered allui.mrg, allui.hed and allui.nam into the **_mrgs** folder.

## 3. Run the patch_allui.py
``python3 patch_allui.py``

### Windows issues
Maybe run the .bat on Windows. Might not work. You need python installed. Try opening
Command Prompt as administrator, then running the .py file like that. Working on a better solution orz.

This might take a long time.

## 4. Copy to mod folder
If all went well, you should have your new allui.* files in **_new_mrgs**. Have fun!