import unittest

from services.parsers import ParseTextFromHtmlService, ParseAbsoluteToDomesticUrlService
from tests.services import mocks
from tests.services.mocks import TEST_PARSE_ABSOLUTE_TO_DOMESTIC_URL_SERVICE


class TestParseTextFromHtmlService(unittest.TestCase):
    service = ParseTextFromHtmlService
    TEST_PARSED_TEXT = """    The purpose of the tournament was to foster patriotism and promoting a healthy \
lifestyle among young people through involvement in physical education and sports. Pull-up and push-up tournament \
from the floor was held on February 21, 2023 on the basis of the State Educational Institution “Polotsk Cadet School”, \
whose student was Hero of Belarus Nikita Kukonenko. A pilot of a flight training squadron of the Lida Attack Air Base \
died on May 19, 2021 during a training flight over the city of Baranovichi, taking the plane away from a populated \
area and saving people’s lives.< /span> A total of 15 teams took part in the tournament in the categories “under 18 \
years old” and “over 18 years old”. Based on the results of the tournament, the national team of the Military Academy \
of the Republic of Belarus and the Minsk Diocese of the BOC as part of the head of the Coordination Center for \
Combating Drug Addiction and Alcoholism in honor of Martyr. Boniface of Archpriest Dionysius Pyasetsky, Lieutenant \
Colonel Dmitry Yatsuk, Private Yulia Suraga took 3rd place. All participants and winners of the tournament were \
awarded diplomas and memorable gifts. The organizers and management of the Polotsk Cadet School expressed words \
of gratitude to the command of the Military Academy and the Belarusian Orthodox Church for participation in the \
tournament. Photos and videos from the event """

    TEST_PARSED_URL_LIST = [
        'images/novosti/2023_The_combined_team_of_the_Minsk_diocese_of_the_BOC_and_the_Military_Academy_\
of_the_Republic_of_Belarus_took_part_in_the_Open_Tournament/photo_2023-03-26_21-34-54.jpg',
        'images/novosti/2023_The_combined_team_of_the_Minsk_diocese_of_the_BOC_and_the_Military_Academy_\
of_the_Republic_of_Belarus_took_part_in_the_Open_Tournament/photo_2023-03-26_21-34-54.jpg',
        'images/novosti/2023_The_combined_team_of_the_Minsk_diocese_of_the_BOC_and_the_Military_Academy_\
of_the_Republic_of_Belarus_took_part_in_the_Open_Tournament/photo_2023-03-26_21-34-54.jpg',
    ]

    TEST_PARSED_YOUTUBE_URL_LIST = [
        'https://youtu.be/IeODSXm4s_E',
        'https://www.youtube.com/watch?v=IeODSXm4s_EWd',
    ]

    def setUp(self):
        self.parser = self.service(mocks.TEST_PARSE_TEXT_FROM_HTML_SERVICE['Text'])

    def test_parse_text(self):
        self.assertEqual(self.parser.parsed_text, '')

        parsed_text = self.parser.parse_text()

        self.assertEqual(parsed_text, self.TEST_PARSED_TEXT)

    def test_parse_image_urls(self):
        self.assertEqual(self.parser.parsed_image_urls, [])

        image_urls = self.parser.parse_image_urls()

        self.assertEqual(image_urls, self.TEST_PARSED_URL_LIST)

    def test_youtube_urls(self):
        self.assertEqual(self.parser.parsed_youtube_urls, [])

        image_urls = self.parser.parse_youtube_urls()

        self.assertEqual(image_urls, self.TEST_PARSED_YOUTUBE_URL_LIST)


class TestParseAbsoluteToDomesticUrlService(unittest.TestCase):
    service = ParseAbsoluteToDomesticUrlService

    TEST_PARSED_ABSOLUTE_TO_DOMESTIC_URL_SERVICE = [
        "images/novosti/2023_The_combined_team_of_the_Minsk_diocese_of_the_BOC_and_the_Military_Academy_of_the_Republic_of_Belarus_took_part_in_the_Open_Tournament/photo_2023-03-26_21-34-54.jpg",
        "images/novosti/2023_The_combined_team_of_the_Minsk_diocese_of_the_BOC_and_the_Military_Academy_of_the_Republic_of_Belarus_took_part_in_the_Open_Tournament/photo_2023-03-26_21-34-54.jpg",
    ]

    def test_parse_url(self):
        parsed_urls = [self.service().parse_url(url) for url in TEST_PARSE_ABSOLUTE_TO_DOMESTIC_URL_SERVICE]
        self.assertListEqual(parsed_urls, self.TEST_PARSED_ABSOLUTE_TO_DOMESTIC_URL_SERVICE)
