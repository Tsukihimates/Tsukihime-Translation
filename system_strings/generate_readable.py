#!/usr/bin/env python3
import hashlib
import sys

def main():
    # Read the two source files
    with open(sys.argv[1], 'r') as f:
        jp_text = f.read()
    with open(sys.argv[2], 'r') as f:
        en_text = f.read()

    # Generate a map of SHA -> EN text
    line_by_sha = {}
    jp_line_by_sha = {}
    for jp, en in zip(jp_text.split("\n"), en_text.split("\n")):
        sha = hashlib.sha1(jp.encode('utf-8')).hexdigest()
        line_by_sha[sha] = en
        jp_line_by_sha[sha] = jp

    for sha, en in line_by_sha.items():
        print(f"[sha:{sha}]" + "{")
        print(f"-- {jp_line_by_sha[sha]}")
        print(f"{en}")
        print("}")

if __name__ == '__main__':
    main()
