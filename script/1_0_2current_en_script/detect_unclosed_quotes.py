#!/usr/bin/env python3
import os


def process_file(filename):
    # Read file
    with open(filename, 'r') as f:
        text = f.read()

    # Split into pages
    pages = []
    current_page = []
    for line in text.split('\n'):
        # If this is a page marker, close accumulator and reset
        if line.startswith('<Page'):
            if current_page:
                pages.append(current_page)
            current_page = [line]
            continue

        # Otherwise, add to current page
        current_page.append(line)

    # Handle final page
    if current_page:
        pages.append(current_page)

    # For each page, just do a dumb check that the quote count is matched
    for page in pages:
        quote_count = len([c for c in ''.join(page) if c == '"'])
        if quote_count & 1:
            msg = '\n'.join(page[1:])
            print(
                f"Possible mismatched quotes in {filename}"
                f" on page {page[0]}:\n"
                f"{msg}\n"
            )


def main():
    for root, dirs, files in os.walk("."):
        for name in files:
            if name.endswith('.txt'):
                process_file(os.path.join(root, name))


if __name__ == '__main__':
    main()
