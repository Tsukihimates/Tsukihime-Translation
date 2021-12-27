#!/usr/bin/env python3
import re
import os

class Color:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    ENDC = '\033[0m'

    def __init__(self, color):
        self.color = color

    def __call__(self, text):
        return f"{self.color}{text}{Color.ENDC}"


class ParsedFile:

    @staticmethod
    def split_pages(raw_text):
        # Split into pages
        pages = []
        current_page = []
        for line in raw_text.split('\n'):
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

        return pages

    @staticmethod
    def ignore_linter(linter_name, line):
        # Does this line have a comment?
        split = line.split('//')
        if len(split) < 2:
            # No comment so can't have a lint-off
            return False

        # Does the comment contain a lint-off pragma for this linter?
        comment = split[1].lower()
        search= f'lint-off:{linter_name}'.lower()
        return search in comment

    def __init__(self, path):
        # Save some file info
        self.path = path
        self.filename = os.path.basename(path)

        # Read file
        with open(path, 'r') as f:
            raw_text = f.read()

        self.pages = self.split_pages(raw_text)

    def __iter__(self):
        for page in self.pages:
            yield page


class LintResult:

    def __init__(self, linter, parsed_file, page, line, message):
        self.linter = linter
        self.filename = parsed_file.filename
        self.page = page
        self.line = line
        self.message = message

    def __repr__(self):
        return f"{self.linter}: {self.filename}: {self.page}:\n\t\"{self.line}\"\n\t{self.message}"

class LintAmericanSpelling:

    BRIT_TO_YANK = {
        'rumour': 'rumor',
        'rumours': 'rumors',
        'colour': 'color',
        'colours': 'colors',
        'defence': 'defense',
        'offence': 'offense',
        'speciality': 'specialty',
        'realise': 'realize',
        'realising': 'realizing',
        'woah': 'whoa',
        'favourable': 'favorable',
        'favour': 'favor',
        'towards': 'toward',
        'leaped': 'leapt',  # Exception since leaped looks dumb
        'anyways': 'anyway',
    }

    def __call__(self, parsed_file):
        errors = []
        for page in parsed_file:
            for line in page:
                if parsed_file.ignore_linter(self.__class__.__name__, line):
                    continue
                for word in line.split(' '):
                    if word.lower() in self.BRIT_TO_YANK:
                        subs = self.BRIT_TO_YANK[word.lower()]
                        errors.append(LintResult(
                        self.__class__.__name__,
                            parsed_file,
                            page[0],
                            line,
                            f"Replace '{word}' with '{subs}'"
                        ))

        return errors


class LintUnclosedQuotes:
    def __call__(self, parsed_file):
        # For each page, just do a dumb check that the quote count is matched
        errors = []
        for page in parsed_file:
            quote_count = len([c for c in ''.join(page) if c == '"'])
            if quote_count & 1:
                errors.append(LintResult(
                    self.__class__.__name__,
                    parsed_file,
                    page[0],
                    '\n'.join(f"\t> {line}" for line in page),
                    f"Found odd number of quotes ({quote_count})"
                ))

        return errors


class LintDanglingCommas:
    def __call__(self, parsed_file):
        # QA has a lot of false positives for this, so maybe ignore for now
        if parsed_file.filename.startswith("QA_"):
            return []

        # Check to see if the final line of the page ends in a , (or ,")
        errors = []
        for page in parsed_file:
            last_line = page[-1]
            if parsed_file.ignore_linter(self.__class__.__name__, last_line):
                continue
            if last_line.endswith(",") or last_line.endswith(",\""):
                errors.append(LintResult(
                    self.__class__.__name__,
                    parsed_file,
                    page[0],
                    last_line,
                    f"Final line ends in trailing ',', replace with CJK dashes '―――'"
                ))

        return errors


class LintVerbotenUnicode:
    VERBOTEN = {
        '　': ' ',
        '…': '...',
        '“': '"',
        '”': '"',
    }

    def __call__(self, parsed_file):
        errors = []
        for page in parsed_file:
            for line in page:
                if parsed_file.ignore_linter(self.__class__.__name__, line):
                    continue
                for find, replace in self.VERBOTEN.items():
                    if find in line.split('//')[0]: # Ignore comments
                        errors.append(LintResult(
                            self.__class__.__name__,
                            parsed_file,
                            page[0],
                            line,
                            f"Replace '{find}' with '{replace}'"
                        ))

        return errors


class LintUnspacedRuby:
    def __call__(self, parsed_file):
        errors = []
        for page in parsed_file:
            for line in page:
                if parsed_file.ignore_linter(self.__class__.__name__, line):
                    continue
                translated_line = line.split('//')[0]
                match = re.search(r"<([\w\s]+)\|([\w\s]+)>", translated_line)
                if match:
                    base = match.group(1)
                    ruby = match.group(2)
                    spaced_ok = True
                    for i in range(len(ruby)-1):
                        if ruby[i] != ' ' and ruby[i+1] != ' ':
                            spaced_ok = False
                            break
                    if not spaced_ok:
                        errors.append(LintResult(
                            self.__class__.__name__,
                            parsed_file,
                            page[0],
                            line,
                            f"Ruby '{ruby}' is not 's p a c e d' properly"
                        ))

        return errors


def process_file(path):
    # Parse it
    parsed_file = ParsedFile(path)

    # Run it through each of the linters
    linters = [
        LintAmericanSpelling(),
        LintUnclosedQuotes(),
        LintDanglingCommas(),
        LintVerbotenUnicode(),
        LintUnspacedRuby(),
    ]

    lint_results = []
    for linter in linters:
        lint_results += linter(parsed_file)

    return lint_results


def report_results(lint_results):
    for result in lint_results:
        indent = f"\t" if result.line[0] != '\t' else ""
        print(
            Color(Color.RED)(f"{result.linter}: {result.filename}: {result.page}\n") +
            f"{indent}" +
            Color(Color.YELLOW)(f"{result.line}\n") +
            Color(Color.CYAN)(f"\t{result.message}\n")
        )

    # Tally total hits for each linter
    linter_hits = {}
    for result in lint_results:
        linter_hits[result.linter] = linter_hits.get(result.linter, 0) + 1

    print("Total stats:")
    for linter, hits in linter_hits.items():
        print(f"\t{linter}: {hits}")


def main():
    lint_results = []
    for root, dirs, files in os.walk("."):
        for name in files:
            if name.endswith('.txt'):
                lint_results += process_file(os.path.join(root, name))

    report_results(lint_results)


if __name__ == '__main__':
    main()
