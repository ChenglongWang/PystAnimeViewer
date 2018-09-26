#-*- coding:utf-8 -*-
import os, sys, json
import urllib.request as request
import urllib.error as error
#import requests
import bs4
from bs4 import BeautifulSoup

HEADERS = {
    'User_Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:62.0) Gecko/20100101 Firefox/62.0'
}
CATEGORIES = {
    '搞笑': 'gaoxiao', '科幻': 'kehuan',
    '运动': 'yundong', '耽美': 'danmei',
    '治愈': 'zhiyuxi', '萝莉': 'luoli',
    '真人': 'zhenren', '装逼': 'zhuangbi',
    '游戏': 'youxi', '推理': 'tuili',
    '青春': 'qingchun', '恐怖': 'kongbu',
    '机战': 'jizhan', '热血': 'rexue',
    '轻小说': 'qingxiaoshuo', '冒险': 'maoxian',
    '后宫': 'hougong', '同年': 'tongnian',
    '恋爱': 'lianai', '美少女': 'meishaonv',
    '理智': 'lizhi', '百合': 'baihe',
    '泡面番': 'paomianfan', '乙女': 'yinv',
    '动作': 'dongzuo'
}

HP_URL = 'http://www.dilidili.wang'

def video_spider(page_url, verbose=True):
    try:
        response = request.Request(page_url, headers=HEADERS)
        html = request.urlopen(response).read().decode('UTF-8')
    except error.HTTPError as e:
        if verbose: console.hud_alert(str(e), 'error', 1.0)
        print(e)
        return None
    except error.URLError as e:
        if verbose: console.hud_alert(str(e), 'error', 1.0)
        print(e)
        return None

    try:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        player = soup.find('iframe', id='player_iframe')
        video_url = player['src'].split('?url=')[1]
    except Exception as e:
        if verbose: console.hud_alert('Fail to parse video url', 'error', 1.0)
        print(e)
    else:
        return video_url

def episodes_spider(page_url, verbose=True):
    ''' scrapy episodes links and dl link from page
        return episodes, None or return episodes, {'txt':dl_txt, 'url':dl_url}
    '''
    try:
        response = request.Request(page_url, headers=HEADERS)
        html = request.urlopen(response).read().decode('UTF-8')
    except error.HTTPError as e:
        if verbose: console.hud_alert('Error: {}'.format(e), 'error', 1.0)
        print('HTTP error:',e)
        return None, None
    except error.URLError as e:
        if verbose: console.hud_alert('Error: {}'.format(e), 'error', 1.0)
        print('URL error:',e)
        return None, None

    episodes = {}
    try:
        soup = bs4.BeautifulSoup(html, 'html.parser')
        ep_list = soup.find("ul", {"class":"clear"})
        for child in ep_list:
            if type(child) is bs4.element.Tag:
                episodes[child.a.em.span.string] = child.a['href']
    except Exception as e:
        if verbose: console.hud_alert('Cannot parse webpage!', 'error', 1.5)
        print(e)
        return

    try:
        dl_link = soup.find('li', {'class':'list_xz'})
        dl_url = dl_link.a['href']
        dl_txt = dl_link.a.string
    except:
        print('No dl link')
        return episodes, None
    else:
        return episodes, {'txt':dl_txt, 'url':dl_url}

def categories_spider(categories, header, out_dir, verbose=True):
    
    search_index = {}
    for i, (key, value) in enumerate(categories.items()):
        sub_url = HP_URL+'/'+value

        try:
            response = request.Request(sub_url, headers=header)
            html = request.urlopen(response).read().decode('UTF-8')
        except error.HTTPError as e:
            print(e)
            continue

        soup = BeautifulSoup(html, 'html.parser')
        anime_list = soup.find("div", {"class":"anime_list"})

        all_contents = {}
        for anime in anime_list:
            #print(type(anime))
            if type(anime) is bs4.element.Tag:
                # print(anime.dd.h3.a.string, anime.dt.img['src'],
                #      anime.dd.h3.a['href'], anime.dd.get_text())

                all_contents[anime.dd.h3.a.string] = {
                    'url': HP_URL + anime.dd.h3.a['href'],
                    'img': anime.dt.img['src'],
                    'cat':key,
                    'intro': anime.dd.get_text()
                }
                search_index[anime.dd.h3.a.string] = key
        if os.path.isdir(out_dir):
            with open(os.path.join(out_dir,value+'.txt'), 'w', encoding='utf8') as f:
                data = json.dumps(all_contents, indent=2, ensure_ascii=False)
                f.write(data)

        if verbose:
            from console import hud_alert as alert
            alert('{}/{}: {}'.format(i+1, len(categories.items()), key), 'success', 1.0)
    
    if os.path.isdir(out_dir):
        with open(os.path.join(out_dir,'search'), 'w', encoding='utf8') as f:
            f.write(json.dumps(search_index, indent=2, ensure_ascii=False))
        
    
    return search_index

if __name__ == '__main__':
    
    categories_spider(CATEGORIES, HEADERS, out_dir='./', verbose=False)
