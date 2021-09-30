import os
import time
import logging
import requests

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


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
    gitname = homework['homeworks'][0]['homework_name'].split('__')[0]
    message = f'Для github аккаунта "{gitname}" обновилась информация:\n\n'

    # из предположения, что больше одной работы может поменять статус
    # за время опроса
    for homework_number in range(len(homework['homeworks'])):
        homework_name = homework['homeworks'][homework_number]['lesson_name']
        comment = homework['homeworks'][homework_number]['reviewer_comment']

        if homework['homeworks'][homework_number]['status'] == 'reviewing':
            verdict = 'взята на ревью.'

        elif homework['homeworks'][homework_number]['status'] == 'rejected':
            verdict = f'содержит ошибки.\nКомментарий: {comment}'

        else:
            verdict = f'прошла проверку.\nКомментарий: {comment}'

        message += f'Работа "{homework_name}": {verdict}'

        # форматирование для нескольких работ
        if homework_number + 1 != len(homework['homeworks']):
            message += '\n\n'

    return message


def get_homeworks(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    payload = {
        'from_date': current_timestamp
    }
    homework_statuses = requests.get(
        url,
        headers=headers,
        params=payload
    )
    try:
        homework_statuses = requests.get(
            url,
            headers=headers,
            params=payload
        )
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')

    if not len(homework_statuses.json()['homeworks']):
        return False

    return homework_statuses.json()


def send_message(message):
    return bot.send_message(
        chat_id=CHAT_ID,
        text=message,
    )


def main():

    # при запуске, бот выведет информацию по всем работам и начнет мониторить
    # изменения состояний

    logging.debug('Запуск бота')
    current_timestamp = 0

    while True:
        try:
            homework = get_homeworks(current_timestamp)

            if homework:
                message = parse_homework_status(homework)
                send_message(message)
                logging.info(f'Отправлено сообщение: "{message}"')

            current_timestamp = int(time.time())

            time.sleep(15 * 60)

        except Exception as error:
            logging.error(f'{error}')
            send_message(f'Бот упал с ошибкой: {error}')
            time.sleep(5)


if __name__ == '__main__':
    main()
