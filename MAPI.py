import requests
import pygame
import sys
import os
from text_input import PygameTextBox, Button

pygame.init()
screen = pygame.display.set_mode((812, 384))
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')


def make_map_file(ll, z, l, points):
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    map_params = {
        "ll": ll,
        "l": l,
        "z": z,
        "size": "512,384"
    }
    if points:
        map_params['pt'] = points
    try:
        response = requests.get(map_api_server, params=map_params)
    except Exception:
        print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")
        pygame.quit()
        os.remove("map.png")
        sys.exit(1)
    if not response:
        print("Ошибка выполнения запроса")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        pygame.quit()
        os.remove("map.png")
        sys.exit(1)
    try:
        with open("map.png", "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        pygame.quit()
        os.remove("map.png")
        sys.exit(2)


def make_z(toponym):
    delta_x = float(toponym['boundedBy']['Envelope']['upperCorner'].split()[0]) - float(toponym['boundedBy']['Envelope']['lowerCorner'].split()[0])
    delta_y = float(toponym['boundedBy']['Envelope']['upperCorner'].split()[1]) - float(toponym['boundedBy']['Envelope']['lowerCorner'].split()[1])
    z = 0
    for i in range(17):
        if delta_x < 360 / 2 ** (i) or delta_y < 170 / 2 ** (i):
            z = i + 1
    return z


def search_place(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {"geocode": toponym_to_find, "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        print("Ошибка выполнения запроса")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    address_ll = list(map(float, toponym["Point"]["pos"].split(" ")))
    z = make_z(toponym)
    info = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"]
    if 'postal_code' in toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]:
        post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
    else:
        post_code = None
    return (address_ll, z, info, post_code)

def click_search(pos, st_point, z):
    x, y = pos[0] - 300, pos[1]
    print(pos[1])
    if x >= 0:
        st_point_x = st_point[0] - 360 / 2 ** z
        st_point_y = st_point[1] + 127.5 / 2 ** z
        point_x = st_point_x + 720 / 2 ** z / 512 * x
        point_y = st_point_y - 255 / 2 ** z / 384 * y
        print(st_point_x, st_point_y)
        address_ll = '{},{}'.format(point_x, point_y)
        # address_ll = '{},{}'.format(st_point_x, st_point_y)
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {"geocode": address_ll, "format": "json"}
        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            print("Ошибка выполнения запроса")
            print("Http статус:", response.status_code, "(", response.reason, ")")
            sys.exit(1)
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        info = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["formatted"]
        if 'postal_code' in toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]:
            post_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]
        else:
            post_code = None
        return (address_ll, info, post_code)

input_box = PygameTextBox(0, 0, 300, 28)
# btn = Button(429, 0, 83, 28, input_box)

starting_point = [0, 0]
zoom = 1
map_type = ["map"]
points = None

clock = pygame.time.Clock()
FPS = 30
running = True
event_check = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        input_box.update(events)
        # btn.update(events)
        if input_box.is_not_active():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    result, info, post_code = click_search(pygame.mouse.get_pos(), starting_point, zoom)
                    if result:
                        print(result)
                        point = result
                        points = point + ',flag'
                        input_box.add_info(info)
                        input_box.add_post_code(post_code)
                        event_check = True
            elif event.type == pygame.KEYDOWN:
                event_check = True
                if event.key == pygame.K_m:
                    if map_type[0] == "map":
                        map_type[0] = "sat"
                    else:
                        map_type[0] = "map"
                elif event.key == pygame.K_s:
                    if "skl" in map_type:
                        map_type.remove("skl")
                    else:
                        map_type.append("skl")
                elif event.key == pygame.K_t:
                    if "trf" in map_type:
                        map_type.remove("trf")
                    else:
                        map_type.append("trf")
                elif event.key == pygame.K_KP9:
                    if zoom < 17:
                        zoom += 1
                elif event.key == pygame.K_KP3:
                    if zoom > 1:
                        zoom -= 1
                elif event.key == pygame.K_UP:
                    starting_point[1] += 255 / 2 ** zoom
                    if starting_point[1] > 85:
                        starting_point[1] = 85
                    print(starting_point[1])
                elif event.key == pygame.K_DOWN:
                    starting_point[1] -= 255 / 2 ** zoom
                    if starting_point[1] < -85:
                        starting_point[1] = -85
                    print(starting_point[1])
                elif event.key == pygame.K_LEFT:
                    starting_point[0] -= 720 / 2 ** zoom
                    if starting_point[0] < -180:
                        starting_point[0] += 360
                elif event.key == pygame.K_RIGHT:
                    starting_point[0] += 720 / 2 ** zoom
                    if starting_point[0] > 180:
                        starting_point[0] -= 360
    name = input_box.get_name()
    if name:
        starting_point, zoom, info, post_code = search_place(name)
        input_box.add_info(info)
        input_box.add_post_code(post_code)
        points = ','.join(list(map(str, starting_point))) + ',flag'
    if input_box.drop_check():
        event_check = True
        points = None
    if name or event_check:
        make_map_file(
            "{},{}".format(starting_point[0], starting_point[1]),
            str(zoom),
            ','.join(map_type),
            points)
    screen.fill((255, 255, 255))
    input_box.draw(screen)
    # btn.draw(screen)
    screen.blit(pygame.image.load("map.png"), (300, 0))
    pygame.display.flip()
    clock.tick(FPS)
    event_check = False
pygame.quit()
os.remove("map.png")
