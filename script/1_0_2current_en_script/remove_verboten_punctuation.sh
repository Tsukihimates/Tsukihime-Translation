#!/bin/bash
set -xe

# No CJK spaces
find . -type f -name *.txt -exec sed -i 's/　/ /g' {} \;

# No CJK ellipses
find . -type f -name *.txt -exec sed -i 's/…/.../g' {} \;

# No unicode quote marks
find . -type f -name *.txt -exec sed -i 's/“/"/g' {} \;
find . -type f -name *.txt -exec sed -i 's/”/"/g' {} \;
