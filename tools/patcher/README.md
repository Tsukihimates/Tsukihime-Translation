# HOW TO PATCH YOUR allui.mrg OR allpac.mrg
Well hello there. This tool right here *should* help you in creating your
own nice allui.mrg + allui.hed to put into your emulator's mod folder.

## 0. Set up a linux environment

If you're on linux, great! Skip this step.

If you're on Windows, the best way is to install Windows subsystem for Linux (WSL)
https://docs.microsoft.com/en-us/windows/wsl/install

## 1. Download a few tools.

Install python (``sudo apt python`` or your distro equivalent)

You need Ross's mangetsu toolset: https://github.com/rschlaikjer/mangetsu - get it and build it according
to the readme there.

Download compressonatorcli: https://github.com/GPUOpen-Tools/compressonator/releases/tag/V4.2.5185 - and rename the ``compressonatorcli`` script to ``compressonator``.
This tools builds .dds files from .png files to be inserted. **ALSO**, edit the script and remove the first empty line before ``#!/bin/bash``.

If the downloaded version fails to run, you may need to build it yourtself:
```bash
git clone https://github.com/GPUOpen-Tools/compressonator.git
cd compressonator
mkdir build && cd build
cmake \
    -DOPTION_ENABLE_ALL_APPS=OFF \
    -DOPTION_BUILD_APPS_CMP_CLI=ON \
    -DOPTION_CMP_QT=On \
    -DCMAKE_BUILD_TYPE=Debug ..
make
```

If you see errors about `#include <rapidxml.hpp>`, edit
`applications/_plugins/common/cmp_rapidxml.hpp` and change these 3 lines:
```diff
-#include <rapidxml.hpp>
-#include <rapidxml_utils.hpp>
+#include <rapidxml/rapidxml.hpp>
+#include <rapidxml/rapidxml_utils.hpp>
...
-#include <rapidxml_print.hpp>
+#include <rapidxml/rapidxml_print.hpp>
```

The binaries need to be in your PATH system variable for it to work. To do that, edit your ``~/.bashrc``
file and add them at the end of the file, like so:

    export PATH=$PATH:/path/to/compressonator/folder
    export PATH=$PATH:/path/to/mangetsu/build/folder

## 2. Move the allui
Put an unaltered allui.mrg, allui.hed and allui.nam into the **_mrgs** folder.

## 3. Run the patch_allui.py
``python3 patch_allui.py``

The script needs to be where it is: in the Tsukihime-Translation/tools/patcher/ folder. It will get everything it needs
from the repository (images, texts etc.) and compile them into the allui.mrg file.

## 4. Copy to mod folder
If all went well, you should have your new allui.* files in **_new_mrgs**. Have fun!

## 5. Do it again
If you need to rebuild your allui.mrg again, because new stuff has been translated / changed,
you need to delete the .dds files that you want updated from the **.user_interface_dds** folder (or just delete the
whole folder, but this will make the script to redo all the conversions again).

If you only changed the texts in sysmes_strings, you don't need to delete anything - it will rewrite it automatically.

All of these steps are the same for patching allpac.mrg too.
