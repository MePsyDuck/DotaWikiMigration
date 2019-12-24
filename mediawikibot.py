import logging
import sys
import time
from logging.handlers import TimedRotatingFileHandler

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
    line_no = 6476  # Starting line number in sounds.txt
    with open('sounds.txt') as file:
        # Skip till specified line_no
        for _ in range(line_no - 1):
            next(file)

        logger.info('File skipped till line {0}'.format(line_no))

        # Start processing entries
        for i, sound_entry in enumerate(file):
            logger.debug('Processing line : ' + str(line_no + i))
            split_sound_entry = sound_entry.strip().split('/')
            vpk_root = split_sound_entry[0]
            root = split_sound_entry[1]
            header = split_sound_entry[2]
            file_name = split_sound_entry[3]

            page = dotawiki.pages['File:' + file_name]
            if page.exists:
                page = page.resolve_redirect()

                new_page_content = get_new_page_content(page.text(), vpk_root, root, header)
                if new_page_content != page.text():
                    update_page(page, new_page_content)
                else:
                    logger.info('File already up to date: ' + page.page_title)

                new_page_name = root + '_' + header + '_' + file_name
                if new_page_name.lower() != page.page_title.replace(' ', '_').lower():
                    move_page(page, new_page_name)
                else:
                    logger.info('File already moved: ' + page.page_title)
            else:
                logger.warning('Page ' + 'File:' + file_name + ' does not exist.')
    logger.info('All operations completed')


def get_new_page_content(text, vpk_root, root, header):
    new_page_content = ''
    for line in text.split('\n'):
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
    return new_page_content.strip()


@sleep_and_retry
@limits(calls=10, period=60)
def update_page(page, new_page_content):
    logger.info('Update content for : ' + page.page_title)
    logger.debug('Old Page Content:\n' + page.text())
    logger.debug('New Page Content:\n' + new_page_content)
    try:
        page.save(new_page_content, summary='Automated Category replacement (moving files to sound_vo '
                                            'categories)')
    except APIError:
        time.sleep(40)
        page.save(new_page_content, summary='Automated Category replacement (moving files to sound_vo '
                                            'categories)')


@sleep_and_retry
@limits(calls=10, period=60)
def move_page(page, new_page_name):
    logger.info('Moving Page from : ' + page.page_title + 'to : ' + new_page_name)

    try:
        page.move('File:' + new_page_name, reason='Automated move to VPK filepath structure')
    except APIError:
        time.sleep(40)
        page.move('File:' + new_page_name, reason='Automated move to VPK filepath structure')


def get_logger(logger_name):
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s: %(message)s')
    log_file = logger_name + '.log'

    _logger = logging.getLogger(logger_name)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    _logger.addHandler(stream_handler)

    file_handler = TimedRotatingFileHandler(log_file, when='midnight')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    _logger.addHandler(file_handler)

    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False
    return _logger


logger = get_logger('wiki_bot')

if __name__ == '__main__':
    main()
