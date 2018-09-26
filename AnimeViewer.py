# code: utf-8
"""
Simple Anime Viewer.
All content are scrapped from Dilidili.com
"""

import os, sys, re
import functools
import json
import bs4
from AnimeSpider import CATEGORIES, HEADERS, categories_spider, episodes_spider, video_spider

try:
    import ui
    import console
    import dialogs
except ImportError:
    import dummyui as ui
    import dummyconsole as console

__version__ = '1.0.0'

class FavoriteButton(object):

    def __init__(self, app, cell, anime_title, anime_dict):
        self.app, self.cell = app, cell
        self.anime_title, self.anime_dict = anime_title, anime_dict

        self.btn = ui.Button()
        self.cell.content_view.add_subview(self.btn)

        self.btn.font = ('Helvetica', 15)
        self.btn.background_color = 'white'
        self.btn.border_width = 0
        self.btn.corner_radius = 5
        self.btn.size_to_fit()
        self.btn.width = 55
        self.btn.x = self.app.nav_view.width - self.btn.width - 10
        self.btn.y = (self.cell.height - self.btn.height) / 2

        if self.app.is_marked(self.app.favorite_dict, anime_title):
            self.set_state_unmark()
        else:
            self.set_state_mark()

    def set_state_loading(self):
        self.btn.image = ui.Image('iob:ios7_refresh_empty_32')
        self.btn.action = None
        self.btn.tint_color = 'green'
        self.btn.border_color = 'green'

    def set_state_mark(self):
        self.btn.image = ui.Image('iob:ios7_star_outline_32')
        self.btn.action = functools.partial(self.app.mark, self.anime_dict, self)
        self.btn.tint_color = 'blue'
        #self.btn.border_color = 'blue'

    def set_state_unmark(self):
        self.btn.image = ui.Image('iob:star_32')
        self.btn.action = functools.partial(self.app.unmark, self.anime_dict, self)
        self.btn.tint_color = 'red'
        self.btn.border_color = 'red'

class AnimeDetailView(object):
    def __init__(self, app, cat, title, url, img_url, intro):
        self.app = app
        self.category = cat
        self.anime_title = title
        self.page_url = url
        self.img_url = img_url
        self.introduction = intro
        self.episodes = {}
        self.headers = HEADERS
        self.server_id = 0
        self.video_parsers = [
            'http://www.skyfollowsnow.pro/?url=',
            'https://sg.hackmg.com/index.php?url=',
            'http://jx.618g.com/?url=',
            'https://api.pangujiexi.com/player.php?url='
        ]

        if self.app.display_mode == 'phone':
            space_size = 10
            self.image_frame = (20,20,332,483)
            self.intro_frame = (self.image_frame[0],600,330,330)
            self.btns_xy = (self.intro_frame[0],self.intro_frame[1]+self.intro_frame[-1]+space_size)
            self.btns_each_row = 4
            self.btn_size = (70, 35)
            bounce = (False, True)
            content_size = (0, 1500)
        else:
            space_size = 20
            self.image_frame = (30,30,332,483)
            self.intro_frame = (380,30,580,250)
            self.btns_xy = (self.intro_frame[0], self.intro_frame[1]+self.intro_frame[-1]+space_size)
            self.btns_each_row = 8
            self.btn_size = (60, 30)
            bounce = (True, True)
            content_size = (1000, 1000)

        self.view = ui.ScrollView(frame=(0, 0, 640, 640), name=title)
        self.view.background_color = 'lightgrey'
        self.view.content_size = content_size
        self.view.always_bounce_horizontal = bounce[0]
        self.view.always_bounce_vertical = bounce[1]
        self.view.data_source = self
        self.view.delegate = self
        self.view.add_subview(ui.ImageView(name='image_viewer', frame=self.image_frame))
        self.view['image_viewer'].load_from_url(img_url)
        self.view.add_subview(ui.TextView(name='introduction', frame=self.intro_frame))
        self.view['introduction'].text = intro
        self.view['introduction'].editable = False
        self.view['introduction'].auto_content_inset = True
        self.view['introduction'].font = ('Helvetica', 16)
        self.load()

        self.button_style = {'background_color':'white', 'font':('Helvetica', 12), 'corner_radius':4}
        self.change_server_btns = [ui.Button(name='server'+str(i), title=u'线路'+str(i), action=self.change_parser, **self.button_style) for i in range(len(self.video_parsers))]
        for i, server_btn in enumerate(self.change_server_btns):
            self.view.add_subview(server_btn)
            server_btn.x = 30 + (i%5)*(70+10)
            server_btn.y = 520
            server_btn.width = 70
            server_btn.height = 30
            if i == self.server_id:
                server_btn.background_color = 'lightgreen'

    def change_parser(self, sender):
        self.change_server_btns[self.server_id].background_color = 'white'
        self.server_id = int(sender.title[-1])
        console.hud_alert('Change to Server '+str(self.server_id), 'success', 0.5)
        sender.background_color = 'lightgreen'
        
    @ui.in_background
    def load(self):

        episodes, download = episodes_spider(self.page_url)

        if episodes:
            self.episodes = episodes
        else:
            return 

        if download:
            m = re.search(r'[a-z0-9]{4}', download['txt'])
            page_name = 'BaiduPan ({})'.format(m.group()) if m else 'BaiduPan'

            dl_btn = ui.Button(name='dllink', title=download['txt'], action=functools.partial(self.show_webpage, download['url'], page_name) , **self.button_style)
            dl_btn.x, dl_btn.y = 30, 560
            dl_btn.width, dl_btn.height = 70, 30
            self.view.add_subview(dl_btn)

        for i, (key, value) in enumerate(self.episodes.items()):
            btn_name = 'btn'+str(i)
            self.view.add_subview(ui.Button(name=btn_name, title=key))
            self.view[btn_name].title = key
            self.view[btn_name].x = self.btns_xy[0]+(i%self.btns_each_row)*(self.btn_size[0]+10)
            self.view[btn_name].y = self.btns_xy[1]+(i//self.btns_each_row)*(self.btn_size[1]+15)
            self.view[btn_name].border_width = 1
            self.view[btn_name].corner_radius = 4
            self.view[btn_name].background_color = 'white'
            self.view[btn_name].width = self.btn_size[0]
            self.view[btn_name].height = self.btn_size[1]
            self.view[btn_name].action = functools.partial(self.show_video, self.category, self.anime_title, key, value, btn_name)

    def show_webpage(self, url, name, sender):
        webview = ui.WebView(name=name)
        webview.scales_page_to_fit = True
        webview.frame = (0,0,500,640)
        self.app.nav_view.push_view(webview)
        webview.load_url(url)

    def show_video(self, cat, title, ep, video_page, btn_id, sender):
        original_url = video_spider(video_page)
        if not original_url: return
        
        try:    
            webview = ui.WebView(name=ep)
            webview.right_button_items = [ui.ButtonItem('Next', action=functools.partial(self.show_next_video, btn_id, webview))]
            webview.frame = (0,0,640,640)

            print('video url\n',self.video_parsers[self.server_id]+original_url)
            webview.load_url(self.video_parsers[self.server_id]+original_url)
            self.app.nav_view.push_view(webview)
        except Exception as e:
            console.hud_alert('Load video page error', 'error', 1.0)
            print(e)
        else:
            new_hist = '{};{};{}'.format(cat,title,ep)
            if self.app.hist_list[0] != new_hist:
                self.app.hist_list = [new_hist] + self.app.hist_list
            
            # with open(HISTORY_FILE, 'a', encoding='utf8') as f:
            #    f.write('{};{};{}\n'.format(cat,title,ep))
        
    def show_next_video(self, btn_id, webviewer, sender):
        try:
            next_btn_id = int(btn_id.strip('btn'))+1
            next_title = self.view['btn'+str(next_btn_id)].title
            console.hud_alert(next_title, 'success', 1.0)
        except Exception as e:
            print(e)
        else:
            webviewer.stop()
            self.app.nav_view.pop_view(webviewer)
            self.show_video(self.category, self.anime_title, next_title, self.episodes[next_title], 'btn'+str(next_btn_id), sender)

class AnimeTable(object):
    def __init__(self, app, table_name, category_file, anime_dict=None):
        self.app = app
        self.table_name = table_name
        self.category_file = category_file
        self.view = ui.TableView(name=table_name,frame=(0, 0, 640, 640))
        self.view.allows_selection = True

        self.anime_dict = anime_dict if anime_dict else self.app.get_contents_from_file(category_file)
        self.anime_titles = sorted(self.anime_dict.keys())
        self.anime_titles = list(filter(lambda x: x not in self.app.hide_list, self.anime_titles))

        self.view.data_source = self
        self.view.delegate = self
        #self.load()

    @ui.in_background
    def load(self):
        try:
            title_listdatasource = ui.ListDataSource(
                {'title': title, 'accessory_type': 'None'}
                for title in self.anime_titles
            )

            title_listdatasource.action = self.title_tapped
            title_listdatasource.delete_enabled = False
            self.view.data_source = title_listdatasource
            self.view.delegate = title_listdatasource

            self.view.reload()
        except Exception as e:
            console.hud_alert('Failed to load Detail page', 'error', 1.0)

    #@ui.in_background
    #def title_tapped(self, sender=None):
    def title_tapped(self, selected_title):
        try:
            #selected_title = sender.items[sender.selected_row]['title']
            detail_view = AnimeDetailView(self.app, self.anime_dict[selected_title]['cat'], selected_title, self.anime_dict[selected_title]['url'],
                                        self.anime_dict[selected_title]['img'], self.anime_dict[selected_title]['intro'])
            self.app.nav_view.push_view(detail_view.view)
        except Exception as e:
            console.hud_alert('Failed to load page', 'error', 1.0)
            print(e)

    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_number_of_rows(self, tableview, section):
        return len(self.anime_titles)

    def tableview_cell_for_row(self, tableview, section, row):
        anime_title = self.anime_titles[row]
        cell = ui.TableViewCell('subtitle')
        #anime_url = self.anime_dict[anime_title]['url']
        cell.text_label.text = anime_title
        #cell.detail_text_label.text = self.anime_dict[anime_title]['intro']

        FavoriteButton(self.app, cell, anime_title, self.anime_dict)

        return cell

    def tableview_can_delete(self, tableview, section, row):
        return True

    def tableview_can_move(self, tableview, section, row):
        return False

    def tableview_title_for_delete_button(self, tableview, section, row):
        return 'Hide'

    def tableview_did_select(self, tableview, section, row):
        self.title_tapped(self.anime_titles[row])

    def tableview_delete(self, tableview, section, row):
        try:
            self.app.hide_list.append(self.anime_titles[row])
            self.anime_titles.remove(self.anime_titles[row])
            self.view.reload_data()
        except Exception as e:
            print(e)
        else:
            if self.app.old_hide_list != self.app.hide_list:
                self.app.save_hidden()

class HistoryTable(object):
    def __init__(self, app):
        self.app = app
        self.view = ui.TableView(frame=(0,0,640,640),name='History')
        self.view.allows_selection = True
        self.view.data_source = self
        self.view.delegate = self
        self.view.right_button_items = [ui.ButtonItem(image=ui.Image('typb:Delete'),action=self.clear)]

    def clear(self, sender):
        self.app.hist_list = []
        self.view.reload_data()

    def title_tapped(self, cat, title):
        try:
            category_file = os.path.join(CACHE_DIR_DEFAULT, CATEGORIES[cat]+'.txt')
        except:
            category_file = os.path.join(CACHE_DIR_DEFAULT, cat.lower())
        animes = self.app.get_contents_from_file(category_file)

        try:
            detail = animes[title]
        except:
            console.hud_alert('No anime is found!', 'error', 1.0)
        else:
            detail_view = AnimeDetailView(self.app, cat, title, detail['url'], detail['img'], detail['intro'])
            self.app.nav_view.push_view(detail_view.view)

    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_can_delete(self, tableview, section, row):
        return True

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell('subtitle')
        contents = self.app.hist_list[row].split(';')
        cell.text_label.text = '{} ({})'.format(contents[1], contents[2])
        return cell

    def tableview_did_select(self, tableview, section, row):
        contents = self.app.hist_list[row].split(';')
        self.title_tapped(contents[0], contents[1])

    def tableview_delete(self, tableview, section, row):
        self.app.hist_list.remove(self.app.hist_list[row])
        self.view.reload_data()

    def tableview_number_of_rows(self, tableview, section):
        return len(self.app.hist_list)

class CategoriesTable(object):
    def __init__(self, app):
        self.app = app
        self.view = ui.TableView(frame=(0, 0, 640, 640))
        self.view.name = 'Categories'
        self.categories_dict = CATEGORIES

        self.view.right_button_items = [
            #ui.ButtonItem(image=ui.Image('iow:refresh_'+icon_size), action=self.update_cache),
            ui.ButtonItem(image=ui.Image('iob:star_'+self.app.icon_size), action=self.show_mark_list),
            ui.ButtonItem(image=ui.Image('iob:search_'+self.app.icon_size), action=self.search_diag),
            ui.ButtonItem(image=ui.Image('iob:document_'+self.app.icon_size), action=self.show_history)
        ]
        self.view.left_button_items = [
            ui.ButtonItem(image=ui.Image('iob:close_round_'+self.app.icon_size), action=self.quit)
        ]
        self.load()

    def quit(self, sender):
        self.app.save_history()
        self.app.nav_view.close()

    @ui.in_background
    def update_cache(self, sender):
        categories_spider, episodes(CATEGORIES, HEADERS, CACHE_DIR_DEFAULT)

    def search_diag(self, sender):
        keyword = dialogs.input_alert('Search keyword')
        if not os.path.isfile(SEARCH_FILE):
            print('search file not exists!')
            return
        with open(SEARCH_FILE, 'r', encoding='utf8') as f:
            search_index = json.load(f)
        
        ret_dict = {}
        for key, value in search_index.items():
            if keyword in key:
                #ret_cat.append(value)
                if value in ret_dict.keys():
                    ret_dict[value].append(key)
                else:
                    ret_dict[value] = [key]
        
        if not ret_dict:
            console.hud_alert('Not found!', 'error', 1.0)
            return

        final_search_dict = {}
        for cat, titles in ret_dict.items():
            try:
                contents = self.app.get_contents_from_file(
                                os.path.join(CACHE_DIR_DEFAULT,CATEGORIES[cat]+'.txt'))
                for title in titles:
                    final_search_dict[title] = contents[title]
            except:
                print('title not found in caches')
            
        tools_table = AnimeTable(self.app, 'Search', None, final_search_dict)
        self.app.nav_view.push_view(tools_table.view)

    def show_history(self, sender):
        hist_table = HistoryTable(self.app)
        self.app.nav_view.push_view(hist_table.view)
        
    def show_mark_list(self, sender):
        try:
            if self.app.favorite_dict:
                ani_dict = self.app.get_favorites()
                tools_table = AnimeTable(self.app, 'Favorites', None, ani_dict)
                self.app.nav_view.push_view(tools_table.view)
            else:
                raise FileNotFoundError('No marked items!')
        except Exception as e:
            console.hud_alert(str(e), 'error', 1.0)

    @ui.in_background
    def load(self):
        self.app.activity_indicator.start()
        try:
            categories_listdatasource = ui.ListDataSource(
                {'title': category_name, 'accessory_type': 'disclosure_indicator'}
                for category_name in sorted(self.categories_dict.keys())+['***Reflash Cache***']
            )
            categories_listdatasource.action = self.category_item_tapped
            categories_listdatasource.delete_enabled = False

            self.view.data_source = categories_listdatasource
            self.view.delegate = categories_listdatasource
            self.view.reload()
        except Exception as e:
            print(e)
            console.hud_alert('Failed to load Categories', 'error', 1.0)
        finally:
            self.app.activity_indicator.stop()

    @ui.in_background
    def category_item_tapped(self, sender):
        self.app.activity_indicator.start()

        try:
            if sender.items[sender.selected_row]['title'] == '***Update Cache***':
                if dialogs.alert('Confirm', message='Are u sure to update the cache.\nIt may take a time.',button1='OK'):
                    self.update_cache(None)
            else:
                category_name = sender.items[sender.selected_row]['title']
                category_file = os.path.join(CACHE_DIR_DEFAULT, self.categories_dict[category_name]+'.txt')
                if os.path.isfile(category_file):
                    tools_table = AnimeTable(self.app, category_name, category_file)
                    self.app.nav_view.push_view(tools_table.view)
                else:
                    raise FileNotFoundError('cache file not found'+category_file)
        except FileNotFoundError as e:
            self.update_cache(None)
        except Exception as e:
            console.hud_alert('Failed to load tablelist', 'error', 1.0)
            print(e)
        finally:
            self.app.activity_indicator.stop()

class MainApp(object):

    def __init__(self):
        self.activity_indicator = ui.ActivityIndicator(flex='LTRB')
        self.activity_indicator.style = 10

        self.display_mode = 'pad' if min(ui.get_screen_size())>=768 else 'phone'
        self.icon_size = '24' if self.display_mode == 'phone' else '32'

        categories_table = CategoriesTable(self)
        self.nav_view = ui.NavigationView(categories_table.view)
        self.nav_view.name = 'Anime Spider'

        self.nav_view.add_subview(self.activity_indicator)
        self.activity_indicator.frame = (0, 0, self.nav_view.width, self.nav_view.height)
        self.activity_indicator.bring_to_front()

        self.favorite_dict = MainApp.get_favorites()
        hist_list = self.get_history()
        self.old_hist_list, self.hist_list = hist_list[::-1], hist_list[::-1]
        hiddens = self.get_hiddens()
        self.old_hide_list, self.hide_list = hiddens.copy(), hiddens.copy()


    @staticmethod
    def get_favorites():
        fav_dict = {}
        try:
            if os.path.isfile(FAVORITE_FILE):
                with open(FAVORITE_FILE, 'r', encoding='utf8') as f:
                    fav_dict = json.load(f)
                    #fav_items = list(fav_dict.keys())
            else:
                raise FileNotFoundError('Favorite file not found')
        except Exception as e:
            print(e)

        return fav_dict

    @staticmethod
    def get_history():
        hists = []
        try:
            if os.path.isfile(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf8') as f:
                    hists = list(filter(None, f.read().split('\n')))
            else:
                raise FileNotFoundError('History file not found')
        except Exception as e:
            print(e)
        return hists

    @staticmethod
    def get_hiddens():
        hidden_list = []
        try:
            if os.path.isfile(HIDDEN_FILE):
                with open(HIDDEN_FILE, 'r', encoding='utf8') as f:
                    hidden_list = json.load(f)
            else:
                raise FileNotFoundError('Hiddenlist file not found')
        except Exception as e:
            print(e)
        return hidden_list

    @staticmethod
    def is_marked(all_favorite_dict, anime_title):
        #fav_items = MainApp.get_favorites()
        if anime_title in list(all_favorite_dict.keys()):
            return True
        else:
            return False

    def mark(self, anime_dict, btn, sender):
        btn.set_state_loading()
        self._mark(btn, anime_dict)

    @ui.in_background
    def _mark(self, btn, anime_dict):
        self.activity_indicator.start()

        try:
            # self.favorites.append(btn.anime_title)
            self.favorite_dict[btn.anime_title] = anime_dict[btn.anime_title]
            console.hud_alert('{} is Marked'.format(btn.anime_title), 'success', 1.0)
        except Exception as e:
            btn.set_state_mark()  # revert the state
            # Display some debug messages
            etype, evalue, tb = sys.exc_info()
            sys.stderr.write('%s\n' % repr(e))
            import traceback
            traceback.print_exception(etype, evalue, tb)
            console.hud_alert('Marking failed', 'error', 1.0)
        else:
            btn.set_state_unmark()
            self.save_favor()
        finally:
            self.activity_indicator.stop()

    def unmark(self, anime_dict, btn, sender):
        try:
            # self.favorites.remove(btn.anime_title)
            self.favorite_dict.pop(btn.anime_title)
            console.hud_alert('Unmarked', 'success', 0.5)
        except ValueError:
            console.hud_alert('{} is not marklist?\nUnmark failed'.format(btn.anime_title), 'error', 1.0)
        else:
            btn.set_state_mark()
            self.save_favor()

    def launch(self):
        self.nav_view.present('fullscreen', hide_title_bar=True)

    def get_contents_from_file(self, file):
        if not os.path.isfile(file): return None
        
        with open(file, 'r', encoding="utf8") as f:
            content = json.load(f)
            return content

    def save_favor(self):
        with open(FAVORITE_FILE, 'w', encoding='utf8') as f:
            #print('Save favorites.', self.favorites)
            f.write(json.dumps(self.favorite_dict, indent=2, ensure_ascii=False))

    def save_hidden(self):
        with open(HIDDEN_FILE, 'w', encoding='utf8') as f:
            f.write(json.dumps(self.hide_list, indent=2, ensure_ascii=False))
    
    def save_history(self):
        if self.old_hist_list != self.hist_list:
            with open(HISTORY_FILE, 'w', encoding='utf8') as f:
                for hist in self.hist_list[::-1]:
                    f.write(hist+'\n')
    
if __name__ == '__main__':
    
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    CACHE_DIR_DEFAULT = os.path.join(SCRIPT_DIR, 'bangumi')
    FAVORITE_FILE = os.path.join(CACHE_DIR_DEFAULT, 'favorites')
    HISTORY_FILE = os.path.join(CACHE_DIR_DEFAULT, 'history')
    HIDDEN_FILE = os.path.join(CACHE_DIR_DEFAULT, 'hidden')
    SEARCH_FILE = os.path.join(CACHE_DIR_DEFAULT, 'search')
    
    os.makedirs(CACHE_DIR_DEFAULT, exist_ok=True)

    ptinstaller = MainApp()
    ptinstaller.launch()
