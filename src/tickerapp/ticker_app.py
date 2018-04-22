#!/usr/bin/env python
import rgbmatrix as m
import rgbmatrix.graphics as graphics
import time
import requests as req
import json
import logging
import os
import urllib3.exceptions

ENV_TYPE = "cx_ticker"
MODULE_FILE_PATH = os.path.realpath(__file__)
head, tail = os.path.split(MODULE_FILE_PATH)
pathsplit = head.split("/")
del pathsplit[len(pathsplit) - 1]
del pathsplit[len(pathsplit) - 1]
APP_DIR_PATH = "/".join(pathsplit)
DEFAULT_CONFIG_PATH = APP_DIR_PATH + "/config/settings.json"

_log = logging.getLogger(__name__)
_RESPONSE_BUF = []

def logger_config():
    hdlr = logging.FileHandler('/var/log/ticker_logs.log')
    formatter = logging.basicConfig(level=logging.ERROR,
                                    format=("[###%(levelname)s] "
                                            "%(asctime)s: "
                                            "%(filename)s: "
                                            "%(funcName)s(): "
                                            "%(lineno)d: "
                                            "%(message)s\n"))
    hdlr.setFormatter(formatter)
    _log.addHandler(hdlr)


def setup(filepath):
    if not os.path.isfile(filepath):
        _log.error("The file does not exist, %s", filepath)
        raise IOError("The filepath is not a file")
    _log.info("Loading configuation settings from %s", filepath)
    settings = dict()
    try:
        with open(filepath, "r") as f:
            settings = json.load(f)
        return settings
    except IOError as io:
        _log.error("An error has occurred with reading file, %s", io)


settings = setup(DEFAULT_CONFIG_PATH)


class Ticker:
    def __init__(self):
        options = m.RGBMatrixOptions()
        options.chain_length = settings.get("ticker_display_chain_length")
        options.show_refresh_rate = 1
        self.matrix = m.RGBMatrix(options=options)
        self.run()

    def run(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("/home/pi/git/rpi-rgb-led-matrix/fonts/"
                      + settings.get("ticker_display_font"))
        c = settings.get("ticker_display_color")
        text_color = graphics.Color(c[0], c[1], c[2])
        text_y_axis = settings.get("ticker_y_axis")
        ticker_sleep = settings.get("ticker_sleep_time")
        while True:
            try:
                response = get_json_payload(get_data())
                for i in response:
                    payload = i.get('payload')
                    if i.get('display_type') == 'delta':
                        _display_message_delta(self, payload, offscreen_canvas,
                                               font, text_color, text_y_axis,
                                               ticker_sleep)
                    else:
                        _display_message(self, payload, offscreen_canvas, font,
                                         text_color, text_y_axis, ticker_sleep)
            except urllib3.exceptions.MaxRetryError as me:
                _log.error("Max retry error, %s", me)
                pass


def _display_message_delta(self, payload, offscreen_canvas, font, text_color,
                           text_y_axis, ticker_sleep):
        value = payload.get('value')
        arrow_clr = payload.get('arrow_color')
        pos = offscreen_canvas.width
        txt_len = 1
        display_text = payload.get('text') + str(value) + str(arrow_clr)
        _draw_text(self, offscreen_canvas, font, pos, text_y_axis, text_color,
                   display_text, ticker_sleep, txt_len)


def _display_message(self, payload, offscreen_canvas, font, text_color,
                     text_y_axis, ticker_sleep):
    value = payload.get('text')
    pos = offscreen_canvas.width
    txt_len = 1
    display_text = str(value)
    _draw_text(self, offscreen_canvas, font, pos, text_y_axis, text_color,
               display_text, ticker_sleep, txt_len)


def _draw_text(self, offscreen_canvas, font, pos, text_y_axis, text_color,
               display_text, ticker_sleep, txt_len):
    while pos + txt_len > 0:
        offscreen_canvas.Clear()
        txt_len = graphics.DrawText(offscreen_canvas,
                                    font,
                                    pos,
                                    text_y_axis,
                                    text_color,
                                    display_text)
        pos -= 1
        if pos + txt_len < 0:
            pos = offscreen_canvas.width
        time.sleep(ticker_sleep)
        offscreen_canvas = (
            self.matrix.SwapOnVSync(offscreen_canvas))


def _get_percent_change(old, new, change):
    pc = 0.0
    if change != 0:
        if change:
            pc = (new - old)/old * 100
        else:
            pc = (old - new)/old * 100
    return pc


def _get_change_symbol(change):
    symbol = settings.get("ticker_value_no_change")
    if change != 0:
        if change:
            symbol = settings.get("ticker_value_increasing")
        else:
            symbol = settings.get("ticker_value_decreasing")
    return chr(symbol)


def _get_symbol_color(percent_change):
    rgb = settings.get("ticker_display_color")
    if percent_change:
        rgb = [0, 0, 255]
    elif percent_change < 0:
        rgb = [255, 0, 0]
    return rgb


def get_json_payload(response):
    """
    Set the new response json as current response (index 1)
    """
    try:
        resp = response.json()
        return resp
    except ValueError as ve:
        _log.error("No JSON content in response: %s", ve)


def get_data():
    headers = {'x-api-key': settings.get("api_key")}
    response = req.get(settings.get("led_ticker_api_url") + ENV_TYPE,
                       headers=headers)
    if response is None:
        response = list({})
        _log.error("No response from data dashboard API.")
    return response


def main():
    logger_config()
    Ticker()


if __name__ == "__main__":
    main()
