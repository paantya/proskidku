
import time
import pytz
import random
from pathlib import Path



import requests

from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from datetime import datetime

from utils import load, save

from config_prod import msg_info, msg_info_log
from config_prod import CHAT_ID, CHAT_ID_LOG, CHAT_TD_LOG
from plot import ger_plot_st

# CHAT_ID = CHAT_ID_LOG

from telegram import bot, send_photo_log, send_message, upd_info, upd_info_log, delete_message, bot_send_message

NEW_UPD = 10


def get_soup(url, **kwargs):
    try:
        response = requests.get(url, **kwargs)
    except Exception as e:
        text = f"Exception get_soup: {e}"
        print(text)
        time.sleep(5)
        bot_send_message(chat_id=CHAT_ID_LOG, text=text, disable_notification=True)
        return None
    soup = None
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, features='html.parser')
    return soup


def crawl_products(categoric, urls = None):
    if urls is None:
        urls = {}
        
    fmt = f'https://www.proskidku.ru/d-catalog/{categoric}/'
#     print(f'categoric: {categoric}', end=', ')
    
    page_url = fmt
    soup = get_soup(page_url, timeout=30)
    # print(soup)
    if soup is None:
        print("break")
        return None, 0
    else:
        # soup.select_one('.pagination-container').ul.select('.page-link')[-1].text
        if soup.select_one('.pagination-container') is not None:
            pages_count = int(soup.select_one('.pagination-container').ul.select('.page-link')[-1].text)
        else:
            pages_count = 1
#         print(f"pages_count = {pages_count}")

        fmt = 'https://www.proskidku.ru/d-catalog/{categoric}/?PAGEN_1={page}'

        for page_n in tqdm(range(pages_count, 0, -1),f"categoric: {categoric}", leave=False):
#             print('page: {}'.format(page_n), fmt.format(page=page_n, categoric=categoric))

            page_url = fmt.format(page=page_n, categoric=categoric)
            soup = get_soup(page_url)
            if soup is None:
                print("break")
                return None, pages_count
        #     print(soup)
            for tag, pp in zip(soup.select('.product-item-title'), soup.select('.product-item-label-ring')):

                pp_log = pp.text.strip()
                title = tag.a.attrs['title']
                href = tag.a.attrs['href']
                url = 'https://www.proskidku.ru{}'.format(href)
                urls[url] = title, pp_log, categoric

        return urls, pages_count


def parse_products(urls):
    values = urls.values()
    keys = urls.keys()
    
    urls = keys
    names = [i[0] for i in values]
    pps = [i[1] for i in values]
    categorics = [i[2] for i in values]
    
    data = {}
    for url, name, pp, categoric in tqdm(zip(urls,names, pps, categorics), total=min(len(urls),len(names),len(pps),len(categorics)) , leave=False):
        print('\rproduct: {}'.format(url), end='')

        soup = get_soup(url)
        if soup is None:
            print('break')
            continue

    #     print(soup.select('.product-item-detail-tab-content .product-item-detail-properties'))
        key_loc = []
        value_loc = []
        select = soup.select('.product-item-detail-tab-content .product-item-detail-properties')[0]
    #     print(select)
        key_loc = [i.text.strip() for i in select.select('dt')]
        value_loc = [i.text.strip() for i in select.select('dd')]
        сharacteristics = {}
        for k,v in zip(key_loc, value_loc):
            сharacteristics[k] = v
        сharacteristics["categoric"] = categoric
        href = soup.select_one('.product-item-detail-slider-image').img['src']
        try:
            price_old = soup.select_one(".product-item-detail-price-old").text.strip()
            price_new = soup.select_one(".product-item-detail-price-current").text.strip()
            price_economy = soup.select_one(".item_economy_price").text.strip()

            item = {
                'name': name,
                'url': url,
                'categoric': categoric,
                'сharacteristics': сharacteristics,
                'img': 'https://www.proskidku.ru{}'.format(href),
                'price_old': price_old,
                'price_new': price_new,
                'price_economy': price_economy,
                'pp': pp,
            }
            data[url] = item
        
        except Exception as e:
            print(f"Exception: {e}")
    print('\r', end='')
    return data


def check_change(old_urls, new_urls):
    delete = set(old_urls.keys()).difference(set(new_urls.keys()))
    new = set(new_urls.keys()).difference(set(old_urls.keys()))
    no_change = set(new_urls.keys()) & set(old_urls.keys())
    
    return delete, no_change, new


def update(urls):
    old_urls = urls

    reload_url = True
    time_sleep = 1.4
    while reload_url:
        reload_url = False
        urls = {}

        length = {}
        for categoric in ['zavisony', 'diskont', 'srochnye-sroki']:
            len_urls = len(urls)
            urls, pages_count = crawl_products(categoric=categoric, urls=urls)
            if urls is None:
                reload_url = True
                if time_sleep < 90:
                    time_sleep *= 2
                time.sleep(min(90,time_sleep))
                break
            else:
                diff_urls = len(urls) - len_urls
                length[categoric] = {
                    'pages': pages_count,
                    'pos': diff_urls,
                }

    total = []
    for k,v in length.items():
        total.append(f"{k}:(pg {v['pages']}, ps {v['pos']})")
    # zavisony, diskont, srochnye-sroki
    
    delete, no_change, new = check_change(old_urls, urls)

    datetime_now = datetime.now().astimezone().astimezone(tz=pytz.timezone('Europe/Moscow'))
    text = f"⏳ `[{datetime_now}]` upd ({len(old_urls)} - > {len(urls)}, diff {len(urls) - len(old_urls)})(del: {len(delete)}, old: {len(no_change)}, new: {len(new)}): {', '.join(total)}."
    print(text)
    time.sleep(4)
    upd_info_log(msg_info_log, text, len(delete), len(no_change), len(new))
    if len(new) > NEW_UPD:
        try:
            time.sleep(4)
            text = f"{f'➖: {len(delete)}'if len(delete) >0 else ''}{', 'if len(delete)>0 and len(new)>0 else ''}{f'➕: {len(new)}.' if len(new)>0 else '.'}"
            bot_send_message(chat_id=CHAT_TD_LOG, text=text, disable_notification=True)
        except:
            pass
    return urls, delete, no_change, new

def one_step(urls, log_upd, time_end = 0, batch_size=16):
    urls_new, delete, no_change, new = update(urls)
    # change = True if len(urls) != len(urls_new) else False
    change = True
    pp_zero = 0

    new_list = list(new)

    if len(new_list) > 0:
        print(f"data_new: len {len(new_list)}", end='')
    batch_range = len(new) // batch_size + int(len(new) % batch_size > 0)
    for i in tqdm(range(batch_range), 'batch up' ,leave=False):
        url_new_batch = new_list[i*batch_size:(i+1)*batch_size]
        url_new = {k:urls_new[k] for k in url_new_batch}
        data_new = parse_products(url_new)
        url_new = {k:url_new[k] for k in data_new.keys()}

        for k,data in tqdm(data_new.items(), 'send new data' ,leave=False):

            # 'price_old': price_old,
            # 'price_new': price_new,
            # 'price_economy': price_economy,
            if data['pp'] == '0%':
                print(f"data['pp'] == '0%' data: {data}")
                pp_zero += 1
                continue

            send_message_json, time_end = send_message(data, time_end, chat_id=CHAT_ID)
            if send_message_json is not None:
                data_new[k]['tg'] = send_message_json

                data_file = f"./{'/'.join(k.split('/')[-3:-1])}"
                data_done = data_new[k]
                urls[k] = urls_new[k]

                tm_tmp = time.time()
                datetime_key = int(tm_tmp - tm_tmp%900)
                if datetime_key not in log_upd:
                    log_upd[datetime_key] = {}
                if 'add' not in log_upd[datetime_key]:
                    log_upd[datetime_key]['add'] = 0

                log_upd[datetime_key]['add'] += 1


                data_dir = f"./{'/'.join(k.split('/')[-3:-2])}"
                is_data_dir = Path(data_dir)
                if not is_data_dir.is_dir():
                    is_data_dir.mkdir(parents=True, exist_ok=True)
                save(data_done, file=f'{data_file}.json')
                save(urls, file='urls.json')
                save(log_upd, file='log_upd.json')
            else:
                print(f"MSG NO SEND: key {k}\nJSON:{data['tg']}")

    if pp_zero > 0:
        text_tmp = f"pp_zero: {pp_zero}"
        print(text_tmp)

    if change:
        upd_info(msg_info, len(urls_new))

    if len(delete) > 0:
        print(f"data_delete: batch len {len(delete)}", end='')
    
    delete_list_false = []
    delete_list_true = []

    for key in tqdm(delete, 'dalate',leave=False):

        data_file = f"./{'/'.join(key.split('/')[-3:-1])}"
        is_file_path = Path(f'{data_file}.json')
        if is_file_path.is_file():
            data_key = load(file=f'{data_file}.json')
            data = data_key
            successful_delete = delete_message(data['tg'])
        else:
            successful_delete = False
        if successful_delete:
            urls.pop(key, None)

            tm_tmp = time.time()
            datetime_key = int(tm_tmp - tm_tmp%900)
            if datetime_key not in log_upd:
                log_upd[datetime_key] = {}
            if 'del' not in log_upd[datetime_key]:
                log_upd[datetime_key]['del'] = 0
            if 'time_lines' not in log_upd[datetime_key]:
                log_upd[datetime_key]['time_lines'] = []

            log_upd[datetime_key]['del'] += 1

            now = datetime.now()
            dmsg = datetime.fromtimestamp(data['tg']['date'])
            log_upd[datetime_key]['time_lines'].append((now - dmsg).total_seconds())

            # save(datas, file='datas.json')
            data_file = f"./{'/'.join(key.split('/')[-3:-1])}"
            is_file_path = Path(f'{data_file}.json')
            if is_file_path.is_file():
                is_file_path.unlink()
            save(urls, file='urls.json')
            save(log_upd, file='log_upd.json')

        else:
            now = datetime.now()
            if is_file_path.is_file():
                dt_object = datetime.fromtimestamp(data['tg']['date'])
                #if (now - dt_object).days >= 1:

                delete_list_false.append(now - dt_object)
                #print(str(now - dt_object))
                #print(f"MSG NO DELETE: key {key} in datas ({key in datas.keys()})\nJSON:{data['tg']}")
    if len(delete_list_false):
        text = f"❌ `delete_list_false` len({len(delete_list_false)}), min: {min(delete_list_false) if len(delete_list_false) > 0 else '-'}, max: {max(delete_list_false) if len(delete_list_false) > 0 else '-'}"
        print(text)
        time.sleep(4)
        try:
            bot_send_message(chat_id=CHAT_TD_LOG, text=text, disable_notification=True)
        except:
            pass
    return urls, log_upd, time_end


# def main_first():
#     datas = {}
#     urls = {}
#     time_end = time.time()
    
#     urls, datas, time_end = one_step(urls, datas, time_end)
#     time.sleep(5)
    
#     return 0
# main_first()


def main():
    # datas = load(file='datas.json')

    try:
        if Path('urls.json').is_file():
            urls = load(file='urls.json')
    except:
        urls = {}

    try:
        if Path('log_upd.json').is_file():
            log_upd = load(file='log_upd.json')
    except:
        log_upd = {}
    photo_log = None
    time_end = time.time()
    
    while True:
        print(f'\r[{datetime.now()}] Start load data', end='')
        urls, log_upd, time_end = one_step(urls, log_upd, time_end, batch_size=12)

        try:
            if photo_log is None or (photo_log.day != datetime.now().day and datetime.now().hour > 20):
                print(f'\r[{datetime.now()}] Start plot.', end='')
                ger_plot_st(file='log_upd.json')
                print(f'\r[{datetime.now()}] End plot, start send.', end='')
                send_photo_log()
                photo_log = datetime.now()
                print(f'\r[{datetime.now()}] End send.', end='')
        except:
            pass
        time_to_sleep = 3*60 + random.randint(1, 7*60)
        print(f'\r[{datetime.now()}] End load data. Go to sleep ({time_to_sleep} [s]).', end='')
        time.sleep(time_to_sleep)
    
    return 0


if __name__ == '__main__':
    main()
