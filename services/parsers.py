import logging
import re
from typing import List
from urllib.parse import unquote

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ParseTextFromHtmlService:
    INDENTATION_SIZE = 4
    INDENTATION_SIGN = ' '
    YOUTUBE_URL = 'https://www.youtube.com/watch?v={code}'

    parser = 'html.parser'
    youtube_urls_re = r'^((https?\:\/\/)?((www\.)?youtube\.com|youtu\.be)\/.+)$'
    youtube_tag_re = r'{youtube}([\d\w\-\_]+){\/youtube}'

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
        text = ' '.join(stripped_strings)
        self.parsed_text = self._delete_youtube_tags(text)

    def _delete_youtube_tags(self, text):
        return re.sub(self.youtube_tag_re, '', text)

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
        self.parsed_youtube_urls += self._get_youtube_urls()
        self.parsed_youtube_urls += self._get_youtube_urls_from_tags()
        return self.parsed_youtube_urls

    def _get_youtube_urls(self) -> list:
        try:
            link_urls = self._get_source_of_url_tag('a')
            youtube_pattern = re.compile(self.youtube_urls_re)
            return [link for link in link_urls if youtube_pattern.search(link)]
        except TypeError as e:
            logger.error(f'Error getting youtube urls: {e}')
            return []

    def _get_youtube_urls_from_tags(self) -> list:
        codes = re.findall(self.youtube_tag_re, self.text)
        return [self._create_youtube_url_from_code(code) for code in codes]

    def _create_youtube_url_from_code(self, code) -> str:
        return self.YOUTUBE_URL.format(code=code)


class ParseAbsoluteToDomesticUrlService:
    absolute_url_pattern = r'^http:\/\/chasha.by\/(.+)$'

    def parse_url(self, img_url) -> str:
        url_pattern = re.compile(self.absolute_url_pattern)

        try:
            return url_pattern.search(unquote(img_url))[1]
        except TypeError as e:
            logger.info(f'Parse Absolute To Domestic Url have already received domestic Url.')
            return img_url
