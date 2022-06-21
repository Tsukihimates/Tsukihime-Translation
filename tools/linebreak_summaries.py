import sys

# max number of characters that can fit on line
MAX_LEN = 33

# get rid of old line breaks and replace them with spaces.
def cleanup_old_breaks(line):
    # skip japanese lines
    if ord(line[0]) >= 255:
        return line

    return line.replace('^', ' ')

# does the /previous/ word end in some punctuation?
def check_for_punctuation(line):
    punctuation = ['.', ',', ';', ':']
    # is the last character punctuation?
    if line[-1] in punctuation:
        return len(line) - 1

    last_split = line.rindex(' ')
    if line[last_split - 1] in punctuation:
        # returns index of splace for quick replacing
        return last_split
    else:
        return -1

# given a line, will break it into segments shorter than or
# equal to MAX_LEN using the break character '^'.
# will try to break on nearby punctuation
def break_up_line(line):
    # skip japanese lines
    if ord(line[0]) >= 255:
        return line

    # simple greedy line layout
    words = line.split(' ')
    new_line = ""
    len_since_split = 0

    for word in words:
        if len_since_split + len(word) + 1 <= MAX_LEN:
            new_line += (" " + word if len(new_line) > 0 else word)
            len_since_split += (len(word) + 1 if len(new_line) > 0 else len(word))
        else:
            if (split_location := check_for_punctuation(new_line)) != -1:
                new_line = new_line[:split_location] + "^" + new_line[split_location + 1:]
                new_line += " " + word
                len_since_split = len(new_line) - split_location
            else:
                new_line += "^" + word
                len_since_split = len(word) + 1

    return new_line

def main():
    if len(sys.argv) < 5:
        print("Usage: linebreak_summaries.py <filename> <output file> <start line> <end line>")
        print("start and end indices are inclusive (1-based)")
        exit(1)

    filename = sys.argv[1]
    result_filename = sys.argv[2]
    # 1 offset to make /both/ start and end inclusive
    start_i = int(sys.argv[3]) - 1
    end_i = int(sys.argv[4])
        

    with open(filename, encoding="utf-8") as f:
        file = f.readlines()
        modified_file = file[start_i:end_i]

        # insert new line breaks
        modified_file = list(map(
            lambda line: break_up_line(cleanup_old_breaks(line)),
            modified_file
        ))

        print(f"successfully wrote to {result_filename}")

        with open(result_filename, "w", encoding="utf-8") as res:
            res.writelines(file[:start_i])

        with open(result_filename, "a", encoding="utf-8") as res:
            res.writelines(modified_file)

        with open(result_filename, "a", encoding="utf-8") as res:
            res.writelines(file[end_i:])

if __name__ == "__main__":
    main()
