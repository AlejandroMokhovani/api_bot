import os
import time
import logging
import requests
import json

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# в секундах
REQUEST_SLEEP = 15 * 60
ERROR_SLEEP = 5

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='a'
)
logging.StreamHandler()
logging.FileHandler(
    filename='main.log',
)

# homework-ya-bot
bot = Bot(token=TELEGRAM_TOKEN)
url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        logging.error(f'{error}')

    dict_of_verdicts = {
        'reviewing': 'Работа на ревью.',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
    }
    try:
        verdict = dict_of_verdicts[homework['status']]
    except KeyError as error:
        logging.error(f'{error}')

    return f'У вас проверили работу "{homework_name}": {verdict}'


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            url,
            headers=headers,
            params=payload
        )
    except ConnectionError as error:
        logging.error(f'{error}')
    try:
        homework = homework_statuses.json()
    except json.decoder.JSONDecodeError as error:
        print(f'{error}')

    return homework


def send_message(message):
    return bot.send_message(
        chat_id=CHAT_ID,
        text=message,
    )


def main():

    # есть предположение что в ответе, при мониторинге,
    # может быть больше одной работы

    logging.debug('Запуск бота')
    # current_timestamp = int(time.time())
    current_timestamp = 0

    while True:
        try:
            homework = get_homeworks(current_timestamp)
            homeworks = homework['homeworks']

            if homeworks:
                message = 'Oбновилась информация:\n\n'

                for homework in homeworks:
                    message += parse_homework_status(homework)
                    message += '\n\n'

                send_message(message)
                logging.info(f'Отправлено сообщение: "{message}"')

            try:
                current_timestamp = homework['current_date']
            except KeyError as error:
                logging.error(f'{error}')
            time.sleep(REQUEST_SLEEP)

        except Exception as error:
            logging.error(f'{error}')
            send_message(f'Бот упал с ошибкой: {error}')
            time.sleep(ERROR_SLEEP)


if __name__ == '__main__':
    main()
