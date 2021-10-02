import requests
import urllib.request
import cv2
import numpy as np
import sys
from os import remove as remove_file
from os import mkdir
from os import replace
from datetime import datetime, date, time
from random import randint
from time import sleep

access_token = '3f73363a973f6c6a606ffd786a3d56e2a767d5cadd576c08a3bf0e70488a58a523a5264deb56d5a0c7431'

class VkApiRequestClass:
    def __init__(self, token):
        self.token = token
        self.ApiVersion = '5.130'

    def edit_parameters(self, parameters):
        parameters['access_token'] = self.token
        parameters['v'] = self.ApiVersion

        return parameters

    def newsfeed_search(self, parameters):
        """"
        Available parameters:
        q - поисковой запрос, например, "New Year"
        extended- 1 если необходимо получить информацию о пользователе или сообществе, разместившем запись. (default 0)
        count - указывает, какое максимальное число записей следует возвращать (max 1000).
        latitude - широта точки, в радиусе от которой необходимо производить поиск (от -90 до 90).
        longitud - долгота точки, в радиусе от которой необходимо производить поиск (от -180 до 180).
        start_time - время в формате unixtime, начиная с которого следует получить новости для текущего пользователя.
                    Если параметр не задан, то он считается равным значению времени, которое было сутки назад.
        end_time - время в формате unixtime, до которого следует получить новости для текущего пользователя.
                    Если параметр не задан, то он считается равным текущему времени.
        fields - https://vk.com/dev/objects/user / https://vk.com/dev/objects/group
        """
        parameters = self.edit_parameters(parameters)
        post  = requests.post(f'https://api.vk.com/method/newsfeed.search?', params = parameters)

        return post

VkApi = VkApiRequestClass(access_token)

def download_file(url):
    global path_for_photos

    file_name = f"{path_for_photos}/{url.split('.jpg')[0].split('/')[-1] + datetime.now().strftime(f'%d-%m-%H-%M-%S_{randint(0, 1000)}')}.jpg"
    urllib.request.urlretrieve(url, file_name)
    sleep(2)
    return detect_qr(file_name)

found_posts = 0
photos_count = 0
def get_posts_photos(response):
    global file_name
    global qrcodes_count
    global photos_count
    global found_posts

    output_file = open(file_name, 'a')
    print(f'[*] Статус запроса: {response.status_code}')
    if response.status_code == requests.codes.ok:
        if "error" in response.json():
            print(f'[!!!] Error: {response.json()["error"]["error_msg"]}')
            return False
        found_posts += response.json()["response"]["count"]
        if found_posts == response.json()["response"]["total_count"]:
            output_file.write("[!] Ничего не найдено\n")
            print("[!] Ничего не найдено\n")
            return False
        print(f'[*] Найдено постов: {found_posts} из {response.json()["response"]["total_count"]}')

        count = 0
        for post in response.json()["response"]["items"]:
            if post["from_id"] < 0:
                continue
            id = post["id"]
            owner_id = post["owner_id"]
            photo_urls = []

            if "attachments" in post:
                print(f"Ссылка на пост: \thttps://vk.com/id{owner_id}?w=wall{owner_id}_{id}")
                output_file.write("\t————————————————————————————————————————————————————————\n")
                output_file.write(f"[-] Ссылка на пост: \thttps://vk.com/id{owner_id}?w=wall{owner_id}_{id}\n")
                for attachment in post["attachments"]:
                    if attachment["type"] == "photo":
                        count += 1
                        photos_count += 1

                        index = len(attachment["photo"]["sizes"]) - 1
                        photo = attachment["photo"]["sizes"][index]
                        photo_urls.append(photo["url"])
                        output_file.write(f'Фотография из поста: {photo["url"]}\n')
                        print(f"Фотография из поста: \t{photo['url']}")
                        qr_data = download_file(photo['url'])
                        if qr_data != False:
                            output_file.write(f'[...] Ссылка QR: {qr_data}\n')
                            print(f'Ссылка QR: {qr_data}\n')

                print(f"————————————————————————————————————————————————————————")


        output_file.write("\n********************************************************\n")
        output_file.write(f"[*] Постов с фото: \t{count}\n")
        output_file.write(f"[*] Всего фотографий: \t{photos_count}\n")
        output_file.write(f"[*] QR кодов: \t{qrcodes_count}\n")
        if 'next_from' in response.json()['response']:
            output_file.write(f"[*] Значение start_from = \t{response.json()['response']['next_from']}\n")
        else:
            output_file.write(f"[!] Конец\n")
            output_file.write("********************************************************\n")
            return False
        output_file.write("********************************************************\n")

        print("\n********************************************************\n")
        print(f"[*] Постов с фото: \t{count}\n")
        print(f"[*] Всего фотографий: \t{photos_count}\n")
        print(f"[*] QR кодов: \t{qrcodes_count}\n")
        if 'next_from' in response.json()['response']:
            print(f"[*] Значение start_from = \t{response.json()['response']['next_from']}\n")
        else:
            print(f"[!] Конец\n")
            print("********************************************************\n")
            return False
        print("********************************************************\n")

        output_file.close()
        return response.json()['response']['next_from']

qrDetect = cv2.QRCodeDetector()
qrcodes_count = 0
def detect_qr(inputImage):
    global qrcodes_count
    img = cv2.imread(inputImage)
    data, bbox, rectifieldImage = qrDetect.detectAndDecode(img)
    if len(data) > 0:
        qrcodes_count += 1
        replace(inputImage, f'photos/qr/{inputImage.split("fails/")[1]}')
        return data
    else:
        return False

date_filename = datetime.now().strftime(f'%d-%m-%H-%M-%S')
path_for_photos = f'photos/fails/{date_filename}'
mkdir(path_for_photos)
mkdir(f'photos/qr/{date_filename}')
file_name = f'links/post_links{date_filename}.txt'

file = open(file_name, 'w')
file.close()

parameters = {'q' : 'футбол', 'latitude': 59.972728, 'longitude': 30.2192158}
response_return = True
while qrcodes_count < 50 and response_return:
    response_return = get_posts_photos(VkApi.newsfeed_search(parameters))
    parameters['start_from'] = response_return
    sleep(2)
