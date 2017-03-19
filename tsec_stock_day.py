import urllib.request
import requests
import datetime
import csv
import logging
import os.path
from basic_logger import loggers
from bs4 import BeautifulSoup

logger = loggers.get_rotating_file_logger(name=__name__, path='log_tsec_stock_day.log')
error_logger = loggers.get_rotating_file_logger(name=__name__+'error', level=logging.ERROR, path='log_tsec_stock_day_error.log')

crawl_url = 'http://www.twse.com.tw/ch/trading/exchange/MI_INDEX/MI_INDEX.php'

start_date = datetime.date(1911+93, 2, 11) # should change back to 93, 2, 11
now_datetime = datetime.datetime.now()
end_date = datetime.date(now_datetime.year, now_datetime.month, now_datetime.day)

for query_date in ( start_date + datetime.timedelta(n) for n in range( int((end_date - start_date).days) ) ):
    qdate_string = str(query_date.year-1911) + '/' + str(query_date.month).zfill(2) + '/' + str(query_date.day).zfill(2)
    print(qdate_string)
    logger.info("Start query:" + qdate_string)
    res = requests.post(crawl_url, data={'qdate': qdate_string, 'selectType': 'All', 'download': ''})

    if int(res.status_code) == 200:
        soup = BeautifulSoup(res.text, 'lxml')
        try:
            keys = [key.text.strip() for key in soup.select("table")[0].select("thead tr")[1].select("td")]
            keys.insert(0, "資料日期")
            stock_num_idx = keys.index("證券代號")
            stocks = soup.select("table")[0].select("tbody tr")
            for stock in stocks:
                values_string = [value.text.strip().replace(',', '') for value in stock.select("td")]
                values_string.insert(0, qdate_string)
                values = []
                for index, key in enumerate(keys):
                    try:
                        value = Decimal(values_string[index])
                    except:
                        value = values_string[index]
                    values.append(value)

                stock_num = values[stock_num_idx]
                filename = 'output/' + str(stock_num) + '.csv'
                if os.path.isfile(filename):
                    with open(filename, 'a') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(values)
                else:
                    with open(filename, 'w') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(keys)
                        writer.writerow(values)
        except Exception as e:
            logger.warn('No data warning:', exc_info=True)
            #logger.warn("No data.")
            next
        logger.info("Complete:" + qdate_string)
    else:
        error_logger.error("Web error: " + str(res.status_code) + str(res.reason))
        print(res.status_code, res.reason)
