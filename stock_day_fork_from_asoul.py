import os
import gc
import re
import sys
import csv
import time
import string
import logging
import requests
import argparse
from lxml import html
from datetime import datetime, timedelta

from os import mkdir
from os.path import isdir

class Crawler():
    def __init__(self, prefix="data"):
        ''' Make directory if not exist when initialize '''
        if not isdir(prefix):
            mkdir(prefix)
            mkdir(prefix+'/tse')
            mkdir(prefix+'/otc')
        self.prefix = prefix

    def _clean_row(self, row):
        ''' Clean comma and spaces '''
        for index, content in enumerate(row):
            row[index] = re.sub(",", "", content.strip())
            row[index] = "".join([x for x in row[index] if x in string.printable])
        return row

    def _record(self, stock_id, row, data_type='tse'):
        ''' Save row to csv file '''
        file_name = '{}/{}/{}.csv'.format(self.prefix, data_type, stock_id)

        file_exist_flag = True
        if not os.path.isfile(file_name):
            file_exist_flag = False

        f = open(file_name, 'a')
        cw = csv.writer(f, lineterminator='\n')

        if file_exist_flag == False:
            if data_type == 'tse':
                cw.writerow(['日期', '成交股數', '成交金額', '開盤價', '最高價',
                    '最低價', '收盤價', '漲跌價差', '成交筆數', '最後揭示買價', '最後揭示買量',
                    '最後揭示賣價', '最後揭示賣量', '本益比'])
            elif data_type == 'otc':
                cw.writerow(['日期', '成交股數', '成交金額', '開盤價', '最高價',
                    '最低價', '收盤價', '漲跌價差', '成交筆數'])

        cw.writerow(row)
        f.close()

    def _get_tse_data(self, date_str):
        payload = {
            'download': '',
            'qdate': date_str,
            'selectType': 'ALL'
        }
        url = 'http://www.twse.com.tw/ch/trading/exchange/MI_INDEX/MI_INDEX.php'

        # Get html page and parse as tree
        page = requests.post(url, data=payload)

        if not page.ok:
            logging.error("Can not get TSE data at {}".format(date_str))
            return

        # Parse page
        tree = html.fromstring(page.text)

        for tr in tree.xpath('//table[2]/tbody/tr'):
            tds = tr.xpath('td/text()')

            sign = tr.xpath('td/font/text()')
            sign = '-' if len(sign) == 1 and sign[0] == '－' else ''

            row = self._clean_row([
                date_str, # 日期
                tds[2], # 成交股數
                tds[4], # 成交金額
                tds[5], # 開盤價
                tds[6], # 最高價
                tds[7], # 最低價
                tds[8], # 收盤價
                sign + tds[9], # 漲跌價差
                tds[3], # 成交筆數
                tds[10], # 最後揭示買價
                tds[11], # 最後揭示買量
                tds[12], # 最後揭示賣價
                tds[13], # 最後揭示賣量
                tds[14], # 本益比
            ])
            self._record(tds[0].strip(), row, 'tse')

    def _get_otc_data(self, date_str):
        ttime = str(int(time.time()*100))
        url = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={}&_={}'.format(date_str, ttime)
        page = requests.get(url)

        if not page.ok:
            logging.error("Can not get OTC data at {}".format(date_str))
            return

        result = page.json()

        if result['reportDate'] != date_str:
            logging.error("Get error date OTC data at {}".format(date_str))
            return

        for table in [result['mmData'], result['aaData']]:
            for tr in table:
                row = self._clean_row([
                    date_str,
                    tr[8], # 成交股數
                    tr[9], # 成交金額
                    tr[4], # 開盤價
                    tr[5], # 最高價
                    tr[6], # 最低價
                    tr[2], # 收盤價
                    tr[3], # 漲跌價差
                    tr[10] # 成交筆數
                ])
                self._record(tr[0], row, 'otc')


    def get_data(self, year, month, day):
        date_str = '{0}/{1:02d}/{2:02d}'.format(year - 1911, month, day)
        print('Crawling {}'.format(date_str))
        self._get_tse_data(date_str)
        self._get_otc_data(date_str)


def main():
    # Set logging
    if not os.path.isdir('log'):
        os.makedirs('log')
    logging.basicConfig(filename='log/crawl-error.log',
        level=logging.ERROR,
        format='%(asctime)s\t[%(levelname)s]\t%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    # Get arguments
    parser = argparse.ArgumentParser(description='Crawl data at assigned day')
    parser.add_argument('day', type=int, nargs='*',
        help='assigned day (format: YYYY MM DD), default is today')
    parser.add_argument('-b', '--back', action='store_true',
        help='crawl back from assigned day until 2004/2/11')
    parser.add_argument('-c', '--check', action='store_true',
        help='crawl back 10 days for check data')

    args = parser.parse_args()

    # Day only accept 0 or 3 arguments
    if len(args.day) == 0:
        first_day = datetime.today()
    elif len(args.day) == 3:
        first_day = datetime(args.day[0], args.day[1], args.day[2])
    else:
        parser.error('Date should be assigned with (YYYY MM DD) or none')
        return

    crawler = Crawler()

    # If back flag is on, crawl till 2004/2/11, else crawl one day
    if args.back or args.check:
        # otc first day is 2007/04/20
        # tse first day is 2004/02/11

        last_day = datetime(2004, 2, 11) if args.back else first_day - timedelta(10)
        max_error = 5
        error_times = 0

        while error_times < max_error and first_day >= last_day:
            try:
                crawler.get_data(first_day.year, first_day.month, first_day.day)
                error_times = 0
            except:
                date_str = first_day.strftime('%Y/%m/%d')
                logging.error('Crawl raise error {}'.format(date_str), exc_info=True)
                error_times += 1
                continue
            finally:
                first_day -= timedelta(1)
            gc.collect()
    else:
        crawler.get_data(first_day.year, first_day.month, first_day.day)

if __name__ == '__main__':
    main()
