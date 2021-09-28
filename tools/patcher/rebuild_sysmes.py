def rebuild_sysmes(old_sysmes_path, translation_path, new_sysmes_path):
    # the original sysmes here
    sysmes = open(old_sysmes_path, 'rb')
    old_data = sysmes.read()

    # the translated texts here
    translation = open(translation_path, 'rb')
    translations = translation.read().splitlines()

    # output of new sysmes here
    new_sysmes = open(new_sysmes_path, 'wb')

    count_offset = '0x4'
    int_pos = int(count_offset, 16)
    string_count = int.from_bytes(old_data[int_pos:int_pos + 4], byteorder='little')

    print(string_count)

    if len(translations) != string_count:
        raise SystemExit('Wrong number of strings in translation file!')

    header_offset = '0x18'
    first_position = int(header_offset, 16)

    # header offset + string_count * 8
    strings_position = first_position + string_count * 8

    print(hex(strings_position))

    # calculate footer offset
    zero_count = 0
    footer_position = strings_position

    int_pos = strings_position
    while zero_count < string_count:
        value = old_data[int_pos]

        while value != 0:
            int_pos += 1
            value = old_data[int_pos]

        int_pos += 1
        footer_position = int_pos

        zero_count += 1

    # footer_offset = '0x184DA'
    print(hex(footer_position))

    # prepare header and footer
    # we will prepend our new data with this
    header_data = old_data[0:int(header_offset, 16)]
    # we will append our new data with this
    footer_data = old_data[footer_position:len(old_data)]

    # write header
    new_sysmes.write(header_data)
    # write string positions
    pos = first_position
    i = 0
    while pos < first_position + string_count * 8:
        new_sysmes.write(strings_position.to_bytes(8, byteorder='little'))
        pos += 8
        strings_position += len(translations[i]) + 1    # +1 because there will be a 00 byte after each string
        i += 1

    # write strings
    for t in translations:
        new_sysmes.write(t)
        new_sysmes.write(bytes([0x00]))

    # write footer
    new_sysmes.write(footer_data)

    sysmes.close()
    translation.close()
    new_sysmes.close()
