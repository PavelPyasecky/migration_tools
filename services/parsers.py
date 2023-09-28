import re
from typing import List

from bs4 import BeautifulSoup


class ParseTextFromHtmlService:
    INDENTATION_SIZE = 4
    INDENTATION_SIGN = ' '
    parser = 'html.parser'
    youtube_urls_pattern = r'^((https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+)$'

    def __init__(self, text: str):
        self.text = text
        self.parsed_text = ''
        self.parsed_image_urls = []
        self.parsed_youtube_urls = []
        self.soup = BeautifulSoup(self.text, self.parser)

    def parse_text(self) -> str:
        self._get_parsed_text()
        self._beautify_parsed_text()
        return self.parsed_text

    def _get_parsed_text(self):
        stripped_strings = self.soup.stripped_strings
        self.parsed_text = ' '.join(stripped_strings)

    def _beautify_parsed_text(self):
        self._add_indentation()

    def _add_indentation(self):
        self.parsed_text = self.INDENTATION_SIZE * self.INDENTATION_SIGN + self.parsed_text

    def parse_image_urls(self) -> List[str]:
        self._get_image_urls()
        return self.parsed_image_urls

    def _get_source_of_url_tag(self, tag_name):
        self.parsed_image_urls = [tag.attrs.get('src') if tag.attrs.get('src') else tag.attrs.get('href')
                                  for tag in self.soup.findAll(tag_name)]
        return self.parsed_image_urls

    def _get_image_urls(self):
        return self._get_source_of_url_tag('img')

    def parse_youtube_urls(self) -> List[str]:
        self.parsed_youtube_urls = self._get_youtube_urls()
        return self.parsed_youtube_urls

    def _get_youtube_urls(self):
        link_urls = self._get_source_of_url_tag('a')
        youtube_pattern = re.compile(self.youtube_urls_pattern)
        return [link for link in link_urls if youtube_pattern.search(link)]
