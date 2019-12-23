import logging
import sys
import time

from mwclient import Site, APIError
from ratelimit import limits, sleep_and_retry


def main():
    # Generate below at https://dota2.gamepedia.com/Special:BotPasswords
    username = 'user'
    password = 'pass'

    dotawiki = Site('dota2.gamepedia.com/', path='', clients_useragent='MePsyDuckDota2WikiEditingBot/1.0')
    dotawiki.login(username=username, password=password)
    process(dotawiki)


def process(dotawiki):
    line_no = 14_630  # Starting line number in sounds.txt
    with open('sounds.txt') as file:
        # Skip till specified line_no
        for _ in range(line_no - 1):
            next(file)

        # Start processing entries
        for sound_entry in file:
            split_sound_entry = sound_entry.strip().split('/')
            vpk_root = split_sound_entry[0]
            root = split_sound_entry[1]
            header = split_sound_entry[2]
            file_name = split_sound_entry[3]

            new_name = root + '_' + header + '_' + file_name

            page = dotawiki.pages['File:' + file_name]
            if page.exists:
                page = page.resolve_redirect()
                new_page_content = ''

                if new_name.lower() != page.page_title.replace(' ', '_').lower():
                    logger.info('Moving ' + file_name + ' to ' + new_name)
                    reader = page.text()
                    for line in reader.split('\n'):
                        if len(line) > 10:
                            logger.debug('scanning ' + line + ' ' + str(line.find('[[Category:')))
                            if line[0:10] == '[[Category':
                                line = '[[Category:' + vpk_root + ' ' + root + ' ' + header.replace('_', ' ') + ']]'
                            elif line.find('[[Category:') != -1:
                                index = line.find('[[Category:')
                                split_line = line[0:index]
                                old_line = line
                                line = split_line + '\n' + '[[Category:' + vpk_root + ' ' + root + ' '
                                line += header.replace('_', ' ') + ']]'
                                logger.debug('replacing ' + old_line + 'with ' + line)
                        new_page_content += line + '\n'
                    update_page(page, new_page_content, new_name)
                else:
                    logger.info('File already processed: ' + new_name)
            else:
                logger.warning('Page ' + 'File:' + file_name + ' does not exist.')
    logger.info('All operations completed')


@sleep_and_retry
@limits(calls=10, period=60)
def update_page(page, new_page_content, new_name):
    logger.debug('New Page Content:\n' + new_page_content)
    logger.debug('Old Page Content:\n' + page.text())
    try:
        page.save(new_page_content.strip(), summary='Automated Category replacement (moving files to sound_vo '
                                                    'categories)')
    except APIError:
        time.sleep(30)
        page.save(new_page_content.strip(), summary='Automated Category replacement (moving files to sound_vo '
                                                    'categories)')
    try:
        page.move('File:' + new_name, reason='Automated move to VPK filepath structure')
    except APIError:
        time.sleep(30)
        page.move('File:' + new_name, reason='Automated move to VPK filepath structure')


def setup_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s '
                                                                      '- %(message)s')


logger = logging.getLogger('wiki_bot')

if __name__ == '__main__':
    setup_logger()
    main()
