#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/3/24 下午5:38
# @Author  : egret
# @email   : zhanghang@linghit.com
# 拼多多日账单数据获取
import argparse
import json
import re
import traceback
from datetime import datetime
import requests
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class PDD:
    _username, _password = '', ''
    _binary_location, _callback_url, _headless = '', '', False

    _login_url = 'https://mms.pinduoduo.com/'
    _bill_url = 'https://mms.pinduoduo.com/finance/payment-bills/index?q=1'

    def __init__(self, username, password, binary_location, headless, callback_url):
        self._username = username
        self._password = password
        self._binary_location = binary_location
        self._headless = headless
        self._callback_url = callback_url
        self._init_driver()

    def _init_driver(self):
        chrome_options = webdriver.ChromeOptions()

        if self._binary_location != '':
            chrome_options.binary_location = self._binary_location
        if self._headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 SocketLog(tabid=1007&client_id=1)')
        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.set_window_rect(0, 0, 1792, 1120)
        self._driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

    def close_driver(self):
        self._driver.close()

    def login(self):

        self._driver.get(self._login_url)

        sleep(2)

        last_item = WebDriverWait(self._driver, 5, 0.2).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'last-item'))
        )

        last_item.click()

        sleep(2)

        username = WebDriverWait(self._driver, 5, 0.2).until(
            EC.presence_of_element_located((By.ID, 'usernameId'))
        )

        username.send_keys(self._username)

        password = self._driver.find_element_by_id('passwordId')

        password.send_keys(self._password)

        sleep(1.5)

        self._driver.find_element_by_xpath('//button[@class="BTN_outerWrapper_4-61-1 BTN_danger_4-61-1 '
                                           'BTN_large_4-61-1 BTN_outerWrapperBtn_4-61-1"]').click()

        sleep(2)

        html = self._driver.execute_script("return document.documentElement.outerHTML")

        if re.search('账户密码不匹配', html):
            raise Exception('账户密码不匹配')

        self._check_phone()

        self._driver.get(self._bill_url)

        sleep(4)

        print('当前链接：{}'.format(self._driver.current_url))

        res = self._driver.find_elements_by_xpath('//div[@data-testid="beast-core-tab-itemLabel-wrapper"]')

        res[3].click()

        sleep(2)

    def _check_phone(self):
        html = self._driver.execute_script('return document.documentElement.outerHTML')

        if re.search('需要手机验证', html):
            self._driver.find_element_by_link_text('获取验证码').click()

            print('需要输入手机号验证码登录，请在手机上查看：')

            while True:
                current_url = self._driver.current_url

                if not re.search('login', current_url):
                    print('登录-手机号验证成功')
                    break

                code = input()

                input_area = self._driver.find_element_by_xpath('//input[@placeholder="请输入短信验证码"]')

                input_area.send_keys(code)

                button = self._driver.find_element_by_xpath('//button[@data-testid="beast-core-button"]')

                button.click()

                sleep(2)

        else:
            print('登录不需要手机号校验')

    def get_cookie(self):
        cookie = ''
        for elem in self._driver.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + "; "
        cookie = cookie[:-2]
        return cookie

    def query_order(self, date):
        (year, month) = self.parse_month(date)
        # 选择年
        self._driver.find_element_by_xpath(
            '//div[@data-testid="beast-core-simpleDatePicker-year"]/div[@data-testid="beast-core-select"]').click()
        current_year = datetime.now().year
        diff_year = current_year - int(year)
        sleep(1)
        li_list = self._driver.find_elements_by_xpath(
            '//ul[@role="listbox"]/li[@role="option" and @data-disabled="false"]')
        li_list[diff_year].click()
        # 选择月
        self._driver.find_element_by_xpath(
            '//div[@data-testid="beast-core-simpleDatePicker-month"]/div[@data-testid="beast-core-select"]').click()
        diff_month = int(month) - 1
        sleep(1)
        li_list = self._driver.find_elements_by_xpath(
            '//ul[@role="listbox"]/li[@role="option" and @data-disabled="false"]')
        li_list[diff_month].click()

        sleep(1)
        # 查询数据
        self._driver.find_element_by_xpath('//div[@class="btns"]/button').click()

        sleep(3)

        # 解析数据
        # 保存每一列数据
        bills = []
        for i in range(1, 9):
            res = self._driver.find_elements_by_xpath('//tr[@data-testid="beast-core-table-body-tr"]/td[{}]'.format(i))
            bills.append(res)

        result = []
        for i in range(0, len(bills[0])):
            result.append({
                'date': '{}-{}-{}'.format(year, month, bills[0][i].text),
                'income_amount': float(bills[1][i].text.replace('+', '')),
                'income_number': int(bills[2][i].text),
                'outcome_amount': float(bills[3][i].text),
                'outcome_number': int(bills[4][i].text),
                'profit': float(bills[5][i].text.replace('+', '')),
                'opening_balance': float(bills[6][i].text),
                'closing_balance': float(bills[7][i].text)
            })

        print('获取数据成功：{}'.format(result))

        self._curl_callback(json.dumps(result))

    def _curl_callback(self, content):
        if self._callback_url != '':
            local_headers = {
                'Content-Type': 'application/json'
            }
            try:
                res = requests.post(self._callback_url, headers=local_headers, data=str(content), timeout=10)
                print('请求回调地址响应码：{0}，响应内容：{1}'.format(res.status_code, res.content))
            except Exception:
                print('请求回调地址出现异常：{0}'.format(traceback.print_exc()))

    def parse_month(self, month):

        res = re.match(r'^(\d{4})-(\d{2})', month)

        if not res:
            raise BaseException('日期格式错误（Y-m）: {}'.format(month))

        return res.groups()[0], res.groups()[1]


username, password, binary_location, callback_url = '', '', '', ''

month = ''

headless = False

if __name__ == '__main__':
    parse = argparse.ArgumentParser()
    parse.add_argument('-m', '--month', help='抓取时间，格式为：Y-m', required=True, dest='month')
    parse.add_argument('-u', '--username', help='拼多多商家账号', required=True, dest='username')
    parse.add_argument('-p', '--password', help='拼多多商家密码', required=True, dest='password')
    parse.add_argument('-b', '--binary-location', default='', help='浏览器可执行文件路径', dest='binary_location')
    parse.add_argument('-d', '--headless', action='store_true', help='不开启浏览器执行程序', dest='headless')
    parse.add_argument('-c', '--callback-url', default='', help='结果数据回调链接', dest='callback_url')
    args = parse.parse_args()
    pattern = re.compile(r'^\d{4}-\d{2}$')
    if not pattern.match(args.month):
        print('日期格式必须为Y-m')
        exit(1)
    print("抓取订单日期：{0}".format(args.month))
    print("订单数据回调链接：{0}".format(args.callback_url))
    if args.headless:
        print("不打开浏览器")
    month = args.month
    username = args.username
    password = args.password
    binary_location = args.binary_location
    headless = args.headless
    callback_url = args.callback_url

pdd = PDD(username=username, password=password, binary_location=binary_location, callback_url=callback_url,
          headless=headless)

try:
    pdd.login()
    pdd.query_order(month)
except Exception as e:
    traceback.print_exc()
    print('脚本执行异常：{0}'.format(e))
finally:
    pdd.close_driver()
