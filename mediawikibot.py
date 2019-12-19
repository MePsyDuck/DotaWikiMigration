from mwclient import Site


def main():
    username = 'user'
    password = 'pass'

    dotawiki = Site('https://dota2.gamepedia.com/api.php', clients_useragent='MePsyDuckDota2WikiEditingBot/1.0')
    dotawiki.login(username=username, password=password)
    process(dotawiki)


def process(dotawiki):
    with open('sounds.txt') as file:
        sound_entry = file.readline()
        split_sound_entry = sound_entry.split('/')
        vpk_root = split_sound_entry[0]
        root = split_sound_entry[1]
        header = split_sound_entry[2]
        file_name = split_sound_entry[3]

        new_name = 'File:' + root + '_' + header + '_' + file_name

        page = dotawiki.pages['File:' + file_name]
        if page.exists:
            if new_name.lower() != page.page_title.replace(' ', '_').lower():
                print('Moving ' + file_name + ' to ' + new_name)
                reader = page.text
                new_page_content = ''
                for line in reader.split('\n'):
                    if len(line) > 10:
                        print('scanning ' + line + ' ' + str(line.find('[[Category:')))
                        if line[0:10] == '[[Category':
                            line = '[[Category:' + vpk_root + ' ' + root + ' ' + header.replace('_', ' ') + ']]'
                        elif line.find('[[Category:') != -1:
                            index = line.find('[[Category:')
                            split_line = line[0:index]
                            old_line = line
                            line = split_line + '\n' + '[[Category:' + vpk_root + ' ' + root + ' '
                            line += header.replace('_', ' ') + ']]'
                            print('replacing ' + old_line + 'with ' + line)
                    new_page_content += line
                    new_page_content = new_page_content.strip()
                print('New Page Content:\n' + new_page_content)
                print('Old Page Content:\n' + page.text)

            page.edit(new_page_content, summary='Automated Category replacement (moving files to sound_vo categories)')
            if new_name.lower() != page.title.replace(' ', '_').lower():
                page.nove(new_name, reason='Automated move to VPK filepath structure')
            else:
                print('File already processed: ' + new_name)
        else:
            print('Page ' + 'File:' + file_name + ' does not exist.')
    print('All operations completed')


if __name__ == '__main__':
    main()