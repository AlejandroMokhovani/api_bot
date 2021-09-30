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
    homework_name = homework['homework_name']

    if homework['status'] == 'reviewing':
        verdict = f'Работа "{homework_name}" на ревью.'
        return verdict

    elif homework['status'] == 'rejected':
        verdict = f'К сожалению, в работе нашлись ошибки.'

    else:
        verdict = f'Ревьюеру всё понравилось, работа зачтена!'

    message = f'У вас проверили работу "{homework_name}": {verdict}'
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

    return homework_statuses.json()


def send_message(message):
    return bot.send_message(
        chat_id=CHAT_ID,
        text=message,
    )


def main():

    # при запуске, бот выведет информацию по всем работам и начнет мониторить
    # изменения состояний

    # есть предположение что в ответе, при мониторинге,
    # может быть больше одной работы

    logging.debug('Запуск бота')
    current_timestamp = 0

    while True:
        try:
            homework = get_homeworks(current_timestamp)
            homeworks = homework['homeworks']

            if homeworks:
                try:
                    gitname = homeworks[0]['homework_name'].split('__')[0]
                    message = f'Для github аккаунта "{gitname}" обновилась информация:\n\n'
                except Exception:
                    logging.warning(
                        f'gitname извлечь не получилось, обновился формат "homework_name"'
                    )
                    message = f'Oбновилась информация:\n\n'

                for homework in homeworks:
                    message += parse_homework_status(homework)
                    message += '\n\n'

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
