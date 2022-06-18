import os
import requests
import shutil
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
import constants


class MPScrapy:

    soup = None
    raw_links_list = []
    track_names_list = []
    album_art = None

    def __init__(self, url=None, download_item=None, target_selection=None, folder_location=None):
        self.url = url
        self.download_item = download_item  # Soup download criteria
        self.target_selection = target_selection
        self.base_url = urlparse(self.url).scheme +"://"+ urlparse(self.url).netloc
        self.folder_name = urlparse(self.url).path.split("/")[-1:][0]
        self.folder_location = folder_location

    def get_url(self):
        return self.url

    def get_download_item(self):
        return self.download_item 

    def get_target_selection(self):
        return self.target_selection

    def get_folder_location(self):
        return self.folder_location 
    
    def get_base_url(self):
        return self.base_url
    
    def get_soup(self):
        return self.soup
    
    def get_url_links(self):
        return self.raw_links_list
    
    def get_track_names_list(self):
        return self.track_names_list

    def set_url(self, url):
        self.url = url

    def set_download_item(self, download_item):
        self.download_item = download_item

    def set_target_select(self, target_selection):
        self.target_selection = target_selection

    def set_folder_loc(self, folder_location):
        self.folder_location = folder_location
        
    def set_album(self, img_path):
        self.album_art = img_path

    def make_request(self, url_req=None):
        if url_req is None:
            url_req = self.url
            
            if url_req is None:
                raise Exception
        
        # main page
        return requests.get(url_req)

    def parse_as_soup(self, requested):
        return BeautifulSoup(requested.text, 'html.parser')

    def make_soup(self):
        req = self.make_request()
        self.soup = self.parse_as_soup(req)
        return self.soup

    def find_soup_id(self):
        if self.download_item is None:
            raise Exception
        
        parsed_data = self.soup.findAll(self.download_item)
        return parsed_data
    
    def determine_album_art(self, file_path):
        img_stream = self.find_soup_id()[0].select("img")[0]["src"]
        album_art = requests.get(img_stream, stream=True)
        image_path = file_path +'//' + 'cover.jpg'

        with open(image_path, 'wb') as f:
            album_art.raw.decode_content = True
            shutil.copyfileobj(album_art.raw, f)
            
        self.album_art = image_path

    def gather_data_links(self, parsed_data):
        for row in range(len(parsed_data)):
            try:
                row_data = parsed_data[row].select(self.target_selection)[0].select("a")[0]["href"]
            except:
                continue
            if len(row_data) == 0:
                continue
                
            track_name = parsed_data[row].select(self.target_selection)[0].select("a")[0].getText()
            
            if track_name in self.track_names_list:
                freq_num = self.track_names_list.count(track_name)
                track_name = track_name + str(freq_num)
                
            self.track_names_list.append(track_name)
            self.raw_links_list.append(row_data)
            
        return self.raw_links_list
        
    def get_individual_music(self, url):
        the_page = self.make_request(self.get_base_url() + url)
        selected_info = self.parse_as_soup(the_page).find_all("a")
        
        for each_tag in selected_info:
            if each_tag["href"].endswith(".mp3"):
                return each_tag["href"]
    
    def add_art(self, music_path):
        audio = MP3(music_path, ID3=ID3)

        try:
            audio.add_tags()
        except error:
            pass

        with open(self.album_art, 'rb') as the_album_art:
            the_art = the_album_art.read()

        # Reference
        # https://stackoverflow.com/questions/51032792/cannot-embed-cover-art-to-mp3-in-python-3-5-2
        audio.tags.add(
            APIC(
                encoding=3, 
                mime='image/png', 
                type=3, 
                desc=u'Cover',
                data=the_art
            )
        )
        audio.save()

    def make_music(self, file_path, file_object):
        with open(file_path, 'wb') as f:
            file_object.raw.decode_content = True
            shutil.copyfileobj(file_object.raw, f)
            
        self.add_art(file_path)
    
    def generate_music(self):
        self.make_soup()
        raw_soup = self.find_soup_id()
        self.gather_data_links(raw_soup)
        
        the_path = self.folder_name
        if self.folder_location is not None:
            the_path = self.folder_location + "//" + self.folder_name
            
        os.mkdir(the_path)
        self.determine_album_art(the_path)

        for each_link in range(len(self.get_url_links())):
            music_url = requests.get(self.get_individual_music(self.get_url_links()[each_link]), stream=True)
            if music_url.status_code == 200:
                track_name = self.get_track_names_list()[each_link] + ".mp3"
                print(track_name)
                self.make_music(the_path + "//" + track_name, music_url)


if __name__ == "__main__":
    ms = MPScrapy(constants.target_url, constants.target_download_item, constants.target_selector_main, constants.target_folder)
    ms.generate_music()
