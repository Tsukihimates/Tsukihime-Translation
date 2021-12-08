#!/bin/bash
set -xe

# No CJK spaces
find . -type f -name *.txt -exec sed -i 's/　/ /g' {} \;

# No CJK ellipses
find . -type f -name *.txt -exec sed -i 's/…/.../g' {} \;

# No unicode quote marks
find . -type f -name *.txt -exec sed -i 's/“/"/g' {} \;
find . -type f -name *.txt -exec sed -i 's/”/"/g' {} \;

# Strip trailing whitespace on script files
find . -type f -name *.txt -exec sed -Ei 's/[[:blank:]]+$//' {} \;

# Detect files with condensed ruby
set +x
BAD_RUBY=`find . -type f -exec grep '|[[:alpha:]][[:alpha:]][[:alpha:] ]*>' {} \;`
if [ ! -z "$BAD_RUBY" ]; then
  echo "The following files have unspaced ruby:"
  find . -type f -exec grep --color '|[[:alpha:]][[:alpha:]][[:alpha:] ]*>' {} \;
fi
