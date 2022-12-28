import requests


class TelegramCli:
    def __init__(self, telegram_token):
        self._tok = telegram_token

    def get_updates(self):
        url = f"https://api.telegram.org/bot{self._tok}/getUpdates"
        return requests.get(url).json()

    def msg_to_chat(self, chat_id, msg):
        url = f"https://api.telegram.org/bot{self._tok}/sendMessage?chat_id={chat_id}&text={msg}"
        requests.get(url).json()  # this sends the message
