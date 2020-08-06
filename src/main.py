import re
import datetime

import bibtexparser.bparser

abbreviations = {'Crime, Law and Social Change': 'CL&SC',
                 'New York Law School Law Review': 'N.Y.U. L. Rev.',
                 'Utrecht Law Review': 'Utrecht L Rev'}


def get_suffix(number: int) -> str:
    last_number = number % 10
    custom_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    if last_number in custom_suffixes:
        return custom_suffixes[last_number]
    return 'th'


def get_first_page_label(entry: dict, default_value: str = '<FIRST PAGE>') -> str:
    if 'pages' not in entry:
        return default_value

    page_range_pattern = re.compile(r'(?P<firstpage>\d+)-(?P<lastpage>\d+)')
    match = page_range_pattern.match(entry['pages'])
    if match:
        return match.group('firstpage')
    return default_value


def get_number_order_label(number: int) -> str:
    last_number = number % 10
    return str(number) + get_suffix(last_number)


def get_volume_issue_label(entry: dict) -> str:
    issue_opt = None
    if entry['issue'] != '<ISSUE>':
        issue_opt = entry['issue']
    if issue_opt:
        return '{0}/{1}'.format(entry['volume'], issue_opt)
    return entry['volume']


def overwrite_entries(target: dict, source: dict) -> dict:
    for key in target:
        if key in source:
            target[key] = source[key]
    return target


def parse_date(date_text: str) -> datetime.datetime:
    date_format = '%Y-%m-%d'
    return datetime.datetime.strptime(date_text, date_format)


def latex_month_label_to_index(label: str) -> int:
    return {'JAN': 1,
            'FEB': 2,
            'MAR': 3,
            'APR': 4,
            'MAY': 5,
            'JUN': 6,
            'JUL': 7,
            'AUG': 8,
            'SEP': 9,
            'OCT': 10,
            'NOV': 11,
            'DEC': 12}[label.upper()]


def get_date_label(date_time: datetime.datetime) -> str:
    day_label = get_number_order_label(date_time.day)
    month_label = date_time.strftime('%B')
    year_label = str(date_time.year)
    return ' '.join([day_label, month_label, year_label])


def get_written_date_label(entry: dict, default_value: str = '<WRITTEN DATE>') -> str:
    if 'year' in entry:
        year_label = entry['year']
        day_label = None
        if 'day' in entry:
            day_label = get_number_order_label(int(entry['day']))

        month_label = None
        if 'month' in entry:
            month_label = datetime.datetime(2000, latex_month_label_to_index(entry['month']), 1).strftime('%B')

        date_components = []
        if day_label:
            date_components.append(day_label)
        if month_label:
            date_components.append(month_label)
        if year_label:
            date_components.append(year_label)

        if date_components:
            return ' '.join(date_components)
    return default_value


def get_access_date_label(entry: dict, default_value: str = '<ACCESS DATE>') -> str:
    if 'urldate' in entry:
        access_date = parse_date(entry['urldate'])
        return get_date_label(access_date)
    return default_value


def get_journal_label(entry: dict) -> str:
    if entry['journal'] in abbreviations:
        return abbreviations[entry['journal']]
    return entry['journal']


def append_first_page(label: str, entry: dict) -> str:
    if entry['first-page'] != '<FIRST PAGE>':
        label += ' ' + entry['first-page']
    label += '.'
    return label


def format_news_article_entry(article_entry: dict) -> str:
    format_entry = {'author': '<AUTHOR>',
                    'title': '<TITLE>',
                    'url': '<URL>',
                    'journal': '<JOURNAL>',
                    'place': '<PLACE>',
                    'year': '<YEAR>'}

    overwrite_entries(format_entry, article_entry)
    format_entry['first-page'] = get_first_page_label(format_entry)
    format_entry['written-date-label'] = get_written_date_label(article_entry)

    label = '{author}, \'{title}\' \\textit{{{journal}}} ({place}, {written-date-label})'.format(**format_entry)
    label = append_first_page(label, format_entry)
    return label


def format_article_entry(article_entry: dict) -> str:
    format_entry = {'author': '<AUTHOR>',
                    'title': '<TITLE>',
                    'volume': '<VOLUME>',
                    'issue': '<ISSUE>',
                    'documenttype': '<DOCUMENT TYPE>',
                    'url': '<URL>',
                    'journal': '<JOURNAL>',
                    'year': '<YEAR>'}

    overwrite_entries(format_entry, article_entry)

    if 'number' in article_entry:
        format_entry['issue'] = article_entry['number']
    format_entry['first-page'] = get_first_page_label(article_entry)
    format_entry['journal-label'] = get_journal_label(format_entry)
    format_entry['volume-issue-label'] = get_volume_issue_label(format_entry)
    format_entry['written-date-label'] = get_written_date_label(article_entry)
    format_entry['access-date-label'] = get_access_date_label(article_entry)

    is_online_article = 'url' in article_entry
    is_published_article = format_entry['journal'] != '<JOURNAL>'

    if is_published_article:
        label = '{author}, \'{title}\' ({year}) {volume-issue-label}, {journal-label}'.format(**format_entry)
        label = append_first_page(label, format_entry)
        return label
    elif is_online_article:
        return '{author}, \'{title}\' ({documenttype}, ' \
               '{written-date-label}) <{url}> accessed {access-date-label}.'.format(**format_entry)
    else:
        raise Exception('Not implemented')


def format_book_entry(book_entry: dict) -> str:
    format_entry = {'author': '<AUTHOR>',
                    'title': '<TITLE>',
                    'publisher': '<PUBLISHER>',
                    'year': '<YEAR>'}

    overwrite_entries(format_entry, book_entry)

    format_entry['edition'] = get_number_order_label(
        int(book_entry['edition'])) if 'edition' in book_entry else '<EDITION>'
    format_entry['first-page'] = get_first_page_label(entry)

    label = '{author}, \\textit{{{title}}} ({edition}, {publisher}, {year})'.format(**format_entry)
    label = append_first_page(label, format_entry)
    return label


if __name__ == '__main__':
    entry_type_callbacks = {'book': format_book_entry,
                            'article': format_article_entry,
                            'newsarticle': format_news_article_entry}

    with open('/home/pmateusz/dev/bibtex/resources/references.bib') as bibtex_file:
        parser = bibtexparser.bparser.BibTexParser(ignore_nonstandard_types=False)
        bib_database = parser.parse_file(bibtex_file)
        for index, entry in enumerate(bib_database.entries, start=1):
            entry_type = entry['ENTRYTYPE'].lower()

            if entry_type not in entry_type_callbacks:
                print('Unsupported entry type', entry_type)
                continue

            print(entry_type_callbacks[entry_type](entry))
