import os
import sys
import pygame
import random

pygame.init()

# добавление мелодии
pygame.mixer.init()
pygame.mixer.music.load('data/melody.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)
# переменная для проверки запуска мелодии для корректной работы паузы и отключения мелодии
sound_playing = True
# переменная, отвечающая за скорость притяжения чёрной дыры
attraction_speed = 2
# глобально отслеживаю количество тиков в игре, чтобы функция паузы работала корректно
time_units = 0

SIZE = WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode(SIZE)
pygame.display.set_caption('Quantum Drift')
FPS = 60
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


cursor = load_image('pointer.png') # добавляю свой курсор
cursor = pygame.transform.scale(cursor, (32, 32))
background = pygame.transform.scale(load_image('space.jpg'), (WIDTH, HEIGHT))
# задаю 3 основных размера шрифта, используемых в игре
font1 = pygame.font.Font(None, 50)
font2 = pygame.font.Font(None, 40)
font3 = pygame.font.Font(None, 20)


# функция, позволяющая отрисовать кнопки (прямоугольники), а также выделять их при наведении мыши
def draw_buttons(buttons, mouse):
    for button, rect in buttons.items():
        if len(buttons) == 2:
            screen.fill(pygame.Color((0, 0, 0)), rect) # кнопки для экрана с таблицей рекордов
        else:
            screen.fill(pygame.Color((0, 0, 64)), rect) # кнопки для главного меню
        if rect.collidepoint(mouse):
            screen.fill(pygame.Color((64, 0, 64)), rect) # выделение кнопки при наведении


# функция, позволяющая выводить текст из файлов по заданным параметрам
def show_text(text, font, x, y, step):
    for line in text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        line_rect = string_rendered.get_rect()
        y += step
        line_rect.top = y
        line_rect.x = x
        y += line_rect.height
        screen.blit(string_rendered, line_rect)


# функция, которая при наведении на игры с разными уровнями сложности выводит информацию об этих уровнях
def show_info(x, y, mode):
    height = 20 if mode == 'easy' else 95 # для лёгкого уровня описание короткое, для других - больше
    points = [(x, y), (x + 30, y - 30), (x + 30, y - 40), (x + 330, y - 40),
              (x + 330, y + height), (x + 30, y + height), (x + 30, y - 10)]
    pygame.draw.polygon(screen, pygame.Color((64, 0, 64)), points)
    with open(f'data/{mode}.txt', encoding='utf-8') as f:
        info_text = f.read().split('\n')
    show_text(info_text, font3, x + 35, y - 40, 5)


# создаю класс для вывода спрайтов для включения / отключения звука в игре
class Sound(pygame.sprite.Sprite):
    sound_on = load_image('switch-on.png')
    sound_off = load_image('switch-off.png')

    def __init__(self, group):
        super().__init__(group)
        if sound_playing: # при помощи глобальной переменной проверяю, в каком положении должен быть ползунок
            self.image = Sound.sound_on
        else:
            self.image = Sound.sound_off
        self.rect = self.image.get_rect()
        self.rect.x = 130
        self.rect.y = 532

    def update(self, *args):
        global sound_playing
        if args and args[0].type == pygame.MOUSEBUTTONDOWN and \
                self.rect.collidepoint(args[0].pos):
            if sound_playing:
                self.image = self.sound_off
                pygame.mixer.music.pause()
            else:
                self.image = self.sound_on
                pygame.mixer.music.unpause()
            sound_playing = not sound_playing


# класс, реализующий главный объект - корабль НЛО
class Ufo(pygame.sprite.Sprite):
    ufo = load_image('ufo.png')

    def __init__(self, group):
        super().__init__(group)
        self.image = Ufo.ufo
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.y = HEIGHT - self.rect.height
        self.speed = 7

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if self.rect.left - self.speed < 0:
                self.rect.left = 0
            else:
                self.rect.left -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if self.rect.right + self.speed > WIDTH:
                self.rect.right = WIDTH
            else:
                self.rect.right += self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            if self.rect.bottom + self.speed > HEIGHT:
                self.rect.bottom = HEIGHT
            else:
                self.rect.bottom += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if self.rect.top - self.speed < 0:
                self.rect.top = 0
            else:
                self.rect.top -= self.speed


# класс, реализующий квант, который надо собирать
class Quant(pygame.sprite.Sprite):
    quant = load_image('quant.png')

    def __init__(self, group, score, ufo):
        super().__init__(group)
        self.image = Quant.quant
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.ufo = ufo
        self.set_random_pos() # задаю кванту случайную позицию при появлении
        self.score = score


    def update(self, *args):
        if pygame.sprite.collide_mask(self, self.ufo):
            # при касании корабля кванта увеличиваю счёт и задаю новую позицию для кванта
            self.score[0] += 1
            self.set_random_pos()

    def set_random_pos(self):
        while True:
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.rect.y = random.randint(0, HEIGHT - self.rect.height)
            # проверяю, чтобы квант не появился в корабле
            if not pygame.sprite.collide_rect(self, self.ufo):
                break


# класс, реализующий появление ядерных бомб
class Bomb(pygame.sprite.Sprite):
    boom = load_image('boom.png')

    def __init__(self, group, hp, ufo):
        super().__init__(group)
        # для разнообразия генерирую случайное изображение из 7
        self.image = load_image(f'bomb{random.randint(1, 7)}.png')
        self.rect = self.image.get_rect()
        # задаю случайную позицию по горизонтали (оси х)
        self.rect.x = random.randint(0, WIDTH - self.rect.width)
        # задаю вертикальное положение (ось у) так, чтобы бомбу не было видно и она постепенно "падала"
        self.rect.y = -self.rect.height
        self.mask = pygame.mask.from_surface(self.image)
        self.hp = hp
        # этот атрибут отслеживает время, которое прошло с момента пересечения бомбы и корабля
        self.boom_timer = None
        self.ufo = ufo
        self.speed = 5

    def update(self):
        # проверяю, что с момента взрыва прошло 400 мс, чтобы пользователь успел заметить взрыв и потом он пропал
        if self.boom_timer is not None:
            if pygame.time.get_ticks() - self.boom_timer > 400:
                self.kill()
            return
        self.rect.y += self.speed
        if pygame.sprite.collide_mask(self, self.ufo):
            self.hp[0] -= 1
            # при контакте бомбы с кораблём, меняю изображение бомбы на изображение взрыва
            self.image = self.boom
            # засекаю время с момента взрыва
            self.boom_timer = pygame.time.get_ticks()
        if self.rect.y > HEIGHT: # если бомба ушла за пределы экрана - убираю её, чтобы не загружать программу
            self.kill()


# класс, реализующий чёрную дыру
class BlackHole(pygame.sprite.Sprite):
    black_hole = load_image('black-hole.png')

    def __init__(self, group, hp, spawn_time, ufo):
        super().__init__(group)
        self.image = BlackHole.black_hole
        self.rect = self.image.get_rect()
        self.ufo = ufo
        # задаю случайное место появления черной дыры
        self.set_random_pos()
        self.mask = pygame.mask.from_surface(self.image)
        self.hp = hp
        # отмечаю время, когда черная дыра появилась
        self.spawn_time = spawn_time

    def update(self):
        # при помощи глобально переменной time_units отслеживаю, чтобы черная дыра не пропала во время паузы
        if time_units - self.spawn_time > 240:
            self.kill()
            return
        # далее реализую код, который реализует механику притяжения центра корабля к центру черной дыры
        black_hole_center = self.rect.center
        target_center = self.ufo.rect.center
        dx = black_hole_center[0] - target_center[0]
        dy = black_hole_center[1] - target_center[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if 0 < distance <= 200: # притяжение начнётся только в том случае, если между центрам расстояние меньше 200 пкс
            dx /= distance
            dy /= distance
            self.ufo.rect.x += int(dx * attraction_speed)
            self.ufo.rect.y += int(dy * attraction_speed)
        if pygame.sprite.collide_mask(self, self.ufo): # если корабль касается черной дыры - мгновенная смерть
            self.hp[0] = 0

    def set_random_pos(self):
        target_center = self.ufo.rect.center
        while True:
            self.rect.x = random.randint(0, WIDTH - self.rect.width)
            self.rect.y = random.randint(0, HEIGHT - self.rect.height)
            black_hole_center = self.rect.center
            dx = black_hole_center[0] - target_center[0]
            dy = black_hole_center[1] - target_center[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance >= 200: # проверяю, чтобы черная дыра не появилась слишком близко к кораблю и пользователь
                break # успел бы отреагировать, а не угодить в неё случайно, по инерции


# функция, реализующая главное меню
def start_screen():
    with open('data/menu.txt', encoding='utf-8') as f:
        menu_text = f.read().split('\n')
    # чтобы проверять, на какую кнопку наведён курсор, реализую словарь
    buttons = {
        'description': pygame.Rect(15, 50, 400, 50),
        'control': pygame.Rect(15, 114, 400, 50),
        'easy': pygame.Rect(15, 178, 400, 54),
        'medium': pygame.Rect(15, 246, 400, 54),
        'hard': pygame.Rect(15, 314, 400, 54),
        'table': pygame.Rect(15, 382, 400, 50),
        'exit': pygame.Rect(15, 446, 400, 50)
    }
    sound = font1.render('ЗВУК', 1, pygame.Color('white'))
    sound_rect = sound.get_rect()
    sound_rect.x, sound_rect.y = 20, 548
    sounds = pygame.sprite.Group()
    Sound(sounds)
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        draw_buttons(buttons, mouse_pos)
        show_text(menu_text, font1, 20, 30, 30)
        screen.fill(pygame.Color((0, 0, 0)), pygame.Rect(15, 540, 180, 50))
        screen.blit(sound, sound_rect)
        for button, rect in buttons.items():
            if rect.collidepoint(mouse_pos):
                if button == 'easy':
                    show_info(415, 205, button)
                elif button == 'medium':
                    show_info(415, 273, button)
                elif button == 'hard':
                    show_info(415, 341, button)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button, rect in buttons.items():
                    if rect.collidepoint(mouse_pos): # проверяю, какую кнопку нажал пользователь и в какое окно перейти
                        if button == 'exit':
                            terminate()
                        elif button == 'table':
                            table_screen()
                        elif button == 'description':
                            description_screen()
                        elif button == 'control':
                            control_screen()
                        elif button == 'easy': # игровой процесс для разных уровней реализован в одной функции
                            # с разными параметрами
                            # делаю количество жизней списком, чтобы иметь к ним доступ из класса
                            game_screen([3], 5, False)
                        elif button == 'medium':
                            game_screen([3], 3, True)
                        elif button == 'hard':
                            game_screen([1], 1, True)
            sounds.update(event)
        sounds.draw(screen)
        screen.blit(cursor, mouse_pos) # отображаю курсор поверх всех спрайтов
        pygame.display.flip()
        clock.tick(FPS)


# функция, реализующая окно с таблицей рекордов
def table_screen():
    table_name = font1.render('ТАБЛИЦА РЕКОРДОВ', 1, pygame.Color('white'))
    header_rect = table_name.get_rect()
    header_rect.x, header_rect.y = 20, 70
    reset_button = font1.render('СБРОС', 1, pygame.Color('white'))
    reset_rect = reset_button.get_rect()
    reset_rect.x, reset_rect.y = 34, 328
    back_button = font1.render('НАЗАД', 1, pygame.Color('white'))
    back_rect = back_button.get_rect()
    back_rect.x, back_rect.y = 257, 328
    screen.blit(table_name, header_rect)
    buttons = {
        'reset': pygame.Rect(10, 320, 180, 50),
        'back': pygame.Rect(232, 320, 180, 50)
    }
    with open('data/table.txt', 'r', encoding='utf-8') as f:
        records = f.read().split('\n')
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(pygame.Color((0, 0, 0)), pygame.Rect(10, 60, 402, 250))
        screen.blit(table_name, header_rect)
        draw_buttons(buttons, mouse_pos)
        screen.blit(reset_button, reset_rect)
        screen.blit(back_button, back_rect)
        # так как в этом окне текст выводится в два столбика, решено не использовать функцию show_text()
        text_coord = [110, 110]
        for i, record in enumerate(records):
            col = 0 if i < 5 else 1
            string_rendered = font2.render(f'Номер {i + 1}: {record}', 1, pygame.Color('white'))
            record_rect = string_rendered.get_rect()
            text_coord[col] += 10
            record_rect.top = text_coord[col]
            record_rect.x = 20 if col == 0 else 220
            text_coord[col] += record_rect.height
            screen.blit(string_rendered, record_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button, rect in buttons.items():
                    if rect.collidepoint(mouse_pos):
                        if button == 'back':
                            start_screen()
                        elif button == 'reset': # при сбросе рекордов просто делаю список из десяти нулей
                            records = ['0' for _ in range(10)]
                            with open('data/table.txt', 'w', encoding='utf-8') as f:
                                f.write('\n'.join(records)) # и записываю этот список в файл
        screen.blit(cursor, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)


# функция, реализующая окно с предысторией игры
def description_screen():
    with open('data/description.txt', encoding='utf-8') as f:
        description = f.read().split('\n')
    back = pygame.Rect(380, 530, 180, 50)
    back_button = font1.render('НАЗАД', 1, pygame.Color('white'))
    back_rect = back_button.get_rect()
    back_rect.x, back_rect.y = 405, 538
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(pygame.Color((0, 0, 0)), pygame.Rect(10, 10, 550, 570))
        screen.fill(pygame.Color((0, 0, 0)), back)
        if back.collidepoint(mouse_pos):
            screen.fill(pygame.Color((64, 0, 64)), back)
        screen.blit(back_button, back_rect)
        show_text(description, font3, 20, 20, 5)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back.collidepoint(mouse_pos):
                        start_screen()
        screen.blit(cursor, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)


# функция, реализующая окно с описанием игрового процесса
def control_screen():
    with open('data/control.txt', encoding='utf-8') as f:
        control_text = f.read().split('\n')
    example_sprites = pygame.sprite.Group()
    # так как мне не надо проверять пересечение спрайтов и как-то их обрабатывать, создаю и добавляю их без классов
    info_ufo = pygame.sprite.Sprite(example_sprites)
    info_ufo.image = pygame.image.load('data/ufo.png')
    info_ufo.rect = info_ufo.image.get_rect()
    info_ufo.rect.x, info_ufo.rect.y = 195, 270
    info_quant = pygame.sprite.Sprite(example_sprites)
    info_quant.image = pygame.image.load('data/quant.png')
    info_quant.rect = info_quant.image.get_rect()
    info_quant.rect.x, info_quant.rect.y = 182, 353
    for i in range(1, 8):
        info_bomb = pygame.sprite.Sprite(example_sprites)
        info_bomb.image = pygame.image.load(f'data/bomb{i}.png')
        info_bomb.rect = info_bomb.image.get_rect()
        info_bomb.rect.x, info_bomb.rect.y = 162 + 50 * (i - 1), 440
    info_bh = pygame.sprite.Sprite(example_sprites)
    info_bh.image = pygame.image.load('data/mini-bh.png')
    info_bh.rect = info_bh.image.get_rect()
    info_bh.rect.x, info_bh.rect.y = 512, 440
    back = pygame.Rect(10, 530, 180, 50)
    back_button = font1.render('НАЗАД', 1, pygame.Color('white'))
    back_rect = back_button.get_rect()
    back_rect.x, back_rect.y = 35, 538
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(pygame.Color((0, 0, 0)), back)
        if back.collidepoint(mouse_pos):
            screen.fill(pygame.Color((64, 0, 64)), back)
        screen.blit(back_button, back_rect)
        show_text(control_text, font2, 20, 20, 10)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back.collidepoint(mouse_pos):
                    start_screen()
        example_sprites.draw(screen)
        screen.blit(cursor, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)


# функция, реализующая игровое окно
def game_screen(hp, max_hp, black_hole):
    # использую глобальные переменные
    global attraction_speed
    global time_units
    all_sprites = pygame.sprite.Group()
    bombs = []
    score = [0] # делаю счёт списком, чтобы иметь к нему доступ из класса
    ufo = Ufo(all_sprites)
    Quant(all_sprites, score, ufo)
    health = pygame.sprite.Group()
    # переменная для проверки состояния паузы
    game_paused = False
    time_units = 0
    # переменная для отсчёта тиков в игре
    time_delta = 1
    pause = font1.render('ПАУЗА', 1, pygame.Color('white'))
    pause_rect = pause.get_rect()
    pause_rect.x, pause_rect.y = 340, 458
    # если включен режим с чёрной дырой, первая должна появиться через 7 секунд, то есть через 420 тиков
    if black_hole:
        black_hole_spawn = 420
    else:
        black_hole_spawn = None
    while True:
        screen.fill((0, 0, 64))
        score_text = font2.render(f'Счёт: {score[0]}', 1, pygame.Color('white'))
        time_units += time_delta
        # если прошла секунда, или 60 тиков, появляется бомба
        if time_units % 60 == 0:
            bombs.append(Bomb(all_sprites, hp, ufo))
        if black_hole:
            if time_units == black_hole_spawn:
                BlackHole(all_sprites, hp, time_units, ufo)
                black_hole_spawn += 660 # следующая черная дыра появляется через 7 секунд, после "гибели" предыдущей
                # то есть 4 + 7 = 11 секунд или 660 тиков
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over_screen(score[0])
                elif event.key == pygame.K_SPACE:
                    # останавливаю игру
                    game_paused = not game_paused
                    if not game_paused: # если игра не на паузе, возвращаю прежние значения переменных, отвечающих
                        # за передвижение объектов и отслеживание времени
                        ufo.speed = 7
                        time_delta = 1
                        for bomb in bombs:
                            bomb.speed = 5
                        attraction_speed = 2
                        if sound_playing:
                            pygame.mixer.music.unpause()
                    else: # если игра на паузе, обнуляю все переменные, отвечающие за движение объектов и времени
                        ufo.speed = 0
                        time_delta = 0
                        for bomb in bombs:
                            bomb.speed = 0
                        attraction_speed = 0
                        if sound_playing:
                            pygame.mixer.music.pause()
                elif event.key == pygame.K_h:
                    # проверяю наличие очков для восстановления жизней, а также ограничения режима на максимальное хп
                    if score[0] >= 20 and hp != max_hp:
                        score[0] -= 20
                        hp[0] += 1
        all_sprites.update()
        if hp[0] == 0:
            game_over_screen(score[0])
        screen.blit(score_text, (10, 10))
        # заполняю группу спрайтов со здоровьем изображениями сердец в количестве текущего здоровья
        for i in range(hp[0]):
            heart = pygame.sprite.Sprite(health)
            heart.image = pygame.image.load('data/heart.png')
            heart.rect = heart.image.get_rect()
            heart.rect.y = 563
            heart.rect.x = 763 - i * 37
        if game_paused: # если игра поставлена на паузу, вывожу соответсвующее сообщение
            screen.fill(pygame.Color((0, 0, 0)), pygame.Rect(310, 450, 180, 50))
            screen.blit(pause, pause_rect)
        health.draw(screen)
        all_sprites.draw(screen)
        health.empty() # после отрисовки всех жизней, очищаю группу, ведь при следующем тике они могут измениться
        pygame.display.flip()
        clock.tick(FPS)


# функция, реализующая окно окончания игры
def game_over_screen(score):
    final_score = score
    with open('data/table.txt', encoding='utf-8') as f:
        records = list(map(int, f.read().split('\n')))
    game_over = font1.render('ИГРА ОКОНЧЕНА', 1, pygame.Color('white'))
    go_rect = game_over.get_rect()
    go_rect.x, go_rect.y = 15, 65
    new_record = font2.render('Новый рекорд!', 1, pygame.Color('white'))
    new_rect = new_record.get_rect()
    new_rect.x, new_rect.y = 15, 145
    score = font2.render(f'Финальный счёт: {final_score}', 1, pygame.Color('white'))
    score_rect = new_record.get_rect()
    score_rect.x, score_rect.y = 15, 110
    back_button = font1.render('МЕНЮ', 1, pygame.Color('white'))
    back_rect = back_button.get_rect()
    back_rect.x, back_rect.y = 265, 200
    back = pygame.Rect(230, 190, 180, 50)
    # при помощи этой переменной проверяю факт установления нового рекорда и необходимость вывода соответствующей надписи
    show_new = False
    if final_score > records[0]:
        show_new = True
    # добавляю счёт игрока в список рекордов, сортирую по убыванию и оставляю 10 лучших
    records.append(final_score)
    records.sort(reverse=True)
    records = list(map(str, records[:10]))
    with open('data/table.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(records))
    while True:
        screen.blit(background, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(pygame.Color((0, 0, 0)), pygame.Rect(10, 60, 400, 120))
        screen.fill(pygame.Color((0, 0, 0)), back)
        if back.collidepoint(mouse_pos):
            screen.fill(pygame.Color((64, 0, 64)), back)
        screen.blit(back_button, back_rect)
        screen.blit(game_over, go_rect)
        screen.blit(score, score_rect)
        if show_new:
            screen.blit(new_record, new_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mouse_pos):
                    start_screen()
        screen.blit(cursor, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)

# запускаю игровой процесс
if __name__ == '__main__':
    start_screen()
    # pygame.quit()