import datetime
import os
import time
import traceback

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from send_telegram_msg import TelegramCli


USERNAME = os.getenv('PRENOTAMI_USERNAME')
PASSWORD = os.getenv('PRENOTAMI_PASSWORD')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
LONG_TIMEOUT = 60
SHORT_TIMEOUT = 20
STAKEHOLDERS = {
    1: 'he',
    2: 'me'
}


TEL_CLI = TelegramCli(TELEGRAM_TOKEN)


def index(drvr: WebDriver):
    """Open index page"""
    drvr.get("https://prenotami.esteri.it")
    assert "Home Page - Prenot@Mi" == drvr.title


def login(drvr: WebDriver, username: str, password: str):
    """Login"""
    login_elem = drvr.find_element(By.ID, "login-email")
    passw_elem = drvr.find_element(By.ID, "login-password")
    login_form_elem = drvr.find_element(By.ID, "login-form")
    login_btn_elem = login_form_elem.find_element(By.TAG_NAME, "button")

    login_elem.clear()
    passw_elem.clear()
    login_elem.send_keys(username)
    passw_elem.send_keys(password)
    login_btn_elem.submit()


def logout(drvr: WebDriver):
    """Login"""
    logout_form_elem = drvr.find_element(By.ID, "logoutForm")
    logout_btn_elem = logout_form_elem.find_element(By.TAG_NAME, "button")
    logout_btn_elem.submit()


def choose_ru_locale(drvr: WebDriver):
    """Select RU language"""
    ru_lang_elem = WebDriverWait(drvr, LONG_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "/html/body/header/nav[@class='top-nav']/div[@class='top-nav__container']/div[@class='top-nav__languages']/a[text()='RUS']")
        )
    )

    assert ru_lang_elem is not None
    ru_lang_elem.click()


def goto_reservation_options(drvr: WebDriver):
    """Select Reservation"""
    goto_reservation_elem = WebDriverWait(drvr, LONG_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[@id='advanced']/span[text()='Забронируй']")
        )
    )

    goto_reservation_elem.click()


def make_shengen_reservation(drvr: WebDriver, telegram_cli: TelegramCli):
    """Select needed Shengen reservation option"""
    reservation_options_elem = WebDriverWait(drvr, LONG_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@id='myInputTextField']")
        )
    )

    for i in ['Шенгенская', '  виза']:
        time.sleep(1)
        reservation_options_elem.send_keys(i)

    try:
        no_slots_elem = WebDriverWait(drvr, LONG_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//td[text()='Календарь бронирования еще не доступен']")
            )
        )

        if no_slots_elem:
            msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}] Бронирование недоступно! {drvr.current_url}"
            print(msg)
            return
    except TimeoutException:
        shengen_reservation_elem = WebDriverWait(drvr, LONG_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[@href='/Services/Booking/1090']")
            )
        )

        shengen_reservation_elem.click()

    try:
        WebDriverWait(drvr, LONG_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[text()='Al momento non ci sono date disponibili per il servizio richiesto']")
            )
        )

        drvr.find_element(By.XPATH, "//div[@class='jconfirm-buttons']/button[text()='ok']").click()

        msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}] Мест нет! {drvr.current_url}"
        print(msg)
    except TimeoutException:
        traceback.print_exc()

        msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}] Появились места для записи!\n {drvr.current_url}"
        for id in STAKEHOLDERS.keys():
            telegram_cli.msg_to_chat(chat_id=id, msg=msg)


"""Keep trying to reserve a place"""
browser = webdriver.Firefox()

while True:
    try:
        index(browser)
        login(browser, USERNAME, PASSWORD)
        choose_ru_locale(browser)
        goto_reservation_options(browser)
        make_shengen_reservation(drvr=browser, telegram_cli=TEL_CLI)
        logout(browser)

        time.sleep(2 * 60)
    except:
        traceback.print_exc()
