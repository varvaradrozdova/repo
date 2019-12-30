import os
import urllib
from typing import List, Any, Tuple

import requests
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import quote
from fake_useragent import UserAgent

API_TOKEN = '1015507032:AAGMzcFEw9o4WrRM89zyyrVKRegYtibUTA4'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
QUERY_BASIC = 'https://www.kinopoisk.ru/index.php?kp_query='


class CinemaInformation:
    def __init__(self, name: str, poster: Any, actors: List[str], description: str, trailer: str, reviews: List[str],
                 rating: float, place: str):
        self.name = name
        self.poster = poster
        self.actors = actors
        self.description = description
        self.trailer_link = trailer
        self.reviews = reviews
        self.rating = rating
        self.place = place

    def __repr__(self):
        actors = "В главных ролях: " + ', '.join(self.actors)
        reviews = "Отзывы: " + '\n'.join([x.rstrip('\n') for x in self.reviews])
        return self.name + '\n' + self.description + '\n' + str(actors) + '\nТрейлер: ' + self.trailer_link + \
               '\nРейтинг фильма: ' + str(self.rating) + '\n' + \
               str(reviews) + '\nПосмотреть можно здесь: ' + self.place

    def __str__(self):
        return self.__repr__()


def find_film_page(movie: str) -> Tuple:
    tokens = movie.split(' ')
    movie_search = QUERY_BASIC + quote(tokens[0])
    for x in tokens[1:]:
        movie_search += '+' + quote(x)

    page_file = urllib.request.urlopen(movie_search)
    soup = BeautifulSoup(page_file, 'html.parser')
    film_id = soup.find('div', attrs={'class': 'element most_wanted'}).findChildren('li')[0].findChild('a')['data-id']
    film_link = 'https://www.kinopoisk.ru/film/' + film_id
    return film_link, film_id


def get_html_page(film_link: str) -> BeautifulSoup:
    film_page = urllib.request.urlopen(film_link)

    film_page = requests.get(film_link, headers={
                'User-Agent': UserAgent().random
    })

    soup = BeautifulSoup(film_page.content.decode('utf-8'), 'html.parser')
    return soup


def parse_film_page(film_link: str, film_id: int) -> CinemaInformation:
    film_html = get_html_page(film_link)
    soup = BeautifulSoup(film_html, 'html.parser')

    movie_info_tag = soup.find('div', attrs={'class': 'movie-info__content'})

    name = movie_info_tag.find('span', attrs={'class': 'moviename-title-wrapper'}).text

    actors_list_tags = movie_info_tag.find('div', attrs={'class': 'movie-info__actors clearfix actorListbg',
                                                         'id': 'actorList'}).find('ul').findAll('a')
    actors_list = [x.text for x in actors_list_tags][0:len(actors_list_tags) - 1]

    description = soup.find('div', attrs={'class': 'brand_words film-synopsys', 'itemprop': 'description'}).text

    trailer = film_link + '/video/'

    reviews = [x.text for x in soup.find('div', attrs={'class': 'criticism'}).findAll('div', attrs={
        'class': 'descr'})]  # nuzhno ispravit' shtob normal'no

    rating = float(soup.find('span', attrs={'class': 'rating_ball'}).text)

    place = film_link

    img = 'https://st.kp.yandex.net/images/film_big/' + str(film_id) + '.jpg'
    p = requests.get(img)
    poster = p.content
    # bot.send_photo(message.chat.id, img)

    return CinemaInformation(name, poster, actors_list, description, trailer, reviews, rating, place)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    await message.reply("Привет!\n Я помогу тебе найти фильм!")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message) -> None:
    await message.reply("Пришли название фильма, ссылку на который хочешь получить.")


@dp.message_handler()
async def film_query(message: types.Message) -> None:
    query = message["text"]
    film_link, film_id = find_film_page(query)
    cinema_info = parse_film_page(film_link, film_id)
    await message.reply(str(cinema_info))

    # await message.reply(message.text)


QUERY_BASIC = 'https://www.kinopoisk.ru/index.php?kp_query='

# @dp.message_handler()
# async def echo_message(msg: types.Message):
#     await bot.send_message(msg.from_user.id, msg.text)

if __name__ == '__main__':
    executor.start_polling(dp)
