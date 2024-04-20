import json
import logging
import random
import time

from flask import Flask, request

from modes import *
from levels_items import *
from texts import *
from translator import *

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

users = dict()
words = json.load(open("words.json", encoding="utf-8"))
latet = json.load(open("latet.json", encoding="utf-8"))
sounds = json.load(open("sounds.json", encoding="utf-8"))
images = json.load(open("images.json", encoding="utf-8"))
statistic_items = json.load(open("statistic_items.json", encoding="utf-8"))


@app.route("/", methods=["POST"])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        "session": request.json["session"],
        "version": request.json["version"],
        "response": {
            "end_session": False
        },
        "application_state": None
    }
    response = handler(request.json, response)
    logging.info(f"Response: {response!r}")
    return json.dumps(response)


def make_response(text=None, card=None, tts=None, buttons=[]):
    response = {
        "response": {
            "text": text,
            "tts": tts,
            "buttons": buttons + [],
            "card": card
        },
        "version": "1.0",
        "application_state": {
            "value": ["", ""]
        },
    }
    return response


def zaglushka():
    return make_response(text="Дальше пока что не написал :))",
                         card={"type": "BigImage", "image_id": "1652229/cb64aba93edc5c78c8d4"})


def handler(event, context):
    global users
    flag = True
    flag_for_buttons = True
    res = make_response()
    OS = "Yandex" if 'Yandex' in event['meta']['client_id'] else "Display"
    user_request = event["request"]["command"]
    user_request = user_request.replace("ё", "е")
    user_request = user_request.replace("-", " ")
    user = event["session"]["user_id"]


    if event["session"]["new"] or users[user]["action"] == "special_case":
        answ_hi = hi_answer[random.randint(0, len(hi_answer) - 1)]
        if user in users:
            if users[user]["action"] == "name" or users[user]["action"] == "level":
                text = "Привет! В прошлый раз я не успела запомнить твоё имя &#128546, так как навык завершил свою " \
                       "работу. Как тебя зовут?&#128150"
                users[user]["action"] = "name"
                users[user]["game_mode"] = "N"
                res = make_response(text=text)
            else:
                text = greeting(user)
                card = {
                    "type": "ItemsList",
                    "header": {
                        "text": f'{answ_hi}{users[user]["name"]}!'
                    },
                    "items": modes1,
                }
                users[user]["action"] = "mode_selection"
                if OS == "Display":
                    tts = f'{answ_hi}, {users[user]["name"]}! Напоминаю, если будут какие-то вопросы - скажи "помощь"\n' \
                          f'В какой режим хочешь сыграть?sil <[100]> Карточки,sil <[70]> Слова,sil <[70]> Игра на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина.'
                else:
                    tts = f'{answ_hi}, {users[user]["name"]}! Напоминаю, если будут какие-то вопросы - скажи "помощь"\n' \
                          f'В какой режим хочешь сыграть?sil <[100]> Карточки,sil <[70]> Игра на время,sil <[70]> Детский режим.'
                buttons = [{"title": "Ещё режимы", "hide": False}]
                res = make_response(card=card, text=text, tts=tts, buttons=buttons)

        else:
            add_user(user)
            users[user]["action"] = "name"
            res["response"]["text"] = greeting(user)

    # Вспомогательные функции навыка
    elif user_request in change_level_txt:
        res = make_response(text='Скажи "поменять уровень на <уровень>', tts='Скажи "поменяй уровень на sil <[100]> и сам уровень')

    elif "переведи" in user_request:
        flag = False
        arg = 0 if user_request.split()[-1][0] in eng_letters else 1
        try:
            answer = translate(arg, ' '.join(user_request.split()[1:]))
            text = f"{' '.join(user_request.split()[1:])} - это {answer}"
        except:
            text = "Такого слова не сущестсвует."
        res = make_response(text=text)

    elif user_request == "уровни":
        flag = False
        res = levels()

    elif user_request in commands_list:
        flag = False
        res = commands()

    elif user_request in repeate_list:
        flag = False
        res = repeate(event)

    elif user_request in help_list:
        flag = False
        res = help_response()

    elif user_request == "правила":
        flag = False
        res = rules_response(user)

    elif user_request in continue_list and not users[user]["words_game"]["end"]:
        flag = False
        res = event["state"]["application"]["value"][1]

    elif user_request in statistic_list:
        flag = False
        card = {
            "type": "BigImage",
            "title": "Твой прогресс по уровню:",
            "description": statistic(user, users[user]["level"]),
            "image_id":  statistic_items[users[user]["level"]]
        }
        text = "Твой прогресс по уровню:"
        res = make_response(text=text, tts=text+"sil <[70]>"+statistic(user, users[user]['level']), card=card)

    elif any([x in user_request for x in change_level_txt]):
        if users[user]["name"] != "N":
            flag = False
            change_status = change_level(user_request, user)
            if change_status == "OK":
                text = "Изменила уровень&#128150. Теперь буду тебе называть слова этого уровня. Можешь продолжать играть!"
                res = make_response(text=text)
            elif change_status == "WRONG_TYPE":
                text = "Мне не удалось понять на какой уровень ты хочешь перейти &#128546. Скажи, пожалуйста, ещё раз&#128150"
                res = make_response(text=text)
        else:
            res = make_response(text="Сначала скажи имя")
    elif any([x in user_request for x in change_name_txt]):
        if users[user]["name"] != "N":
            flag = False
            if change_name(user_request, user):
                text = f"Изменила имя&#128150. Теперь буду называть тебя {users[user]['name']}. Можешь продолжать играть!"
            else:
                text = f"Мне кажется, ты забыл назвать новое имя, необходимо сказать его после самой команды;)"
            res = make_response(text=text)
        else:
            res = make_response(text="Чтобы менять имя, стоит его сперва придумать;)")
    elif user_request in change_mode:
        if users[user]["name"] != "N":
            flag = False
            users[user]["action"] = "mode_selection"
            card = {
                "type": "ItemsList",
                "header": {
                    "text": "В какой режим будем играть теперь?"
                },
                "items": modes1,
            }
            text = "В какой режим будем играть теперь?"
            if OS == "Display":
                tts = "В какой режим будем играть теперь?sil <[200]> Карточки,sil <[70]> Слова,sil <[70]> Игра на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина."
            else:
                tts = "В какой режим будем играть теперь?sil <[200]> Карточки,sil <[70]> Игра на время,sil <[70]> Детский режим."
            buttons = [{"title": "Ещё режимы", "hide": False}]
            res = make_response(text=text, tts=tts, card=card, buttons=buttons)
        else:
            res = make_response(text="Сначала скажи имя")

    elif user_request in change_topic:
        if users[user]["game_mode"] != "N":
            flag_for_buttons = False
            flag = False
            users[user]["action"] = "topic_selection"
            text = f'Слова на какую тему мне загадывать теперь? Можешь выбрать конкретую или все слова. Есть темы:\n\n' \
                   f'{", ".join(words[users[user]["level"]].keys()).capitalize()}'
            tts = f'Слова на какую тему мне загадывать теперь? Можешь выбрать конкретую или все слова. Есть темы:sil <[100]>\n\n' \
                  f'{",sil <[70]> ".join(words[users[user]["level"]].keys()).capitalize()}'
            buttons = []
            for topic in words[users[user]['level']].keys():
                buttons.append({"title": topic, "hide": True})
            res = make_response(text=text, buttons=buttons, tts=tts)
        else:
            if users[user]["name"] == "N":
                res = make_response(text="Сначала скажи имя.")
            elif users[user]["game_mode"] == "N":
                res = make_response(text="Сначала выбери режим игры.")

    elif user_request == "еще режимы" and OS == "Display":
        flag = False
        card = {
            "type": "ItemsList",
            "header": {
                "text": "В какой режим ты хочешь поиграть сегодня?"
            },
            "items": modes2,
        }
        text = "Режимы:"
        tts = "Режимы:sil <[100]>    Карточки,sil <[70]> Слова,sil <[70]> Игра на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина."
        buttons = [{"title": "Назад", "hide": False}]
        res = make_response(text=text, tts=tts, card=card, buttons=buttons)

    elif user_request == "назад" and OS == "Display":
        flag = False
        card = {
            "type": "ItemsList",
            "header": {
                "text": "В какой режим ты хочешь поиграть сегодня?"
            },
            "items": modes1,
        }
        text = "Режимы:"
        tts = "Режимы:sil <[100]>    Карточки,sil <[70]> Слова,sil <[70]> Игры на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина."
        buttons = [{"title": "Ещё режимы", "hide": False}]
        res = make_response(text=text, tts=tts, card=card, buttons=buttons)

    elif users[user]["action"] == "name":
        users[user]["name"] = get_name(user_request)
        users[user]["action"] = "level"
        text = "Приятно познакомиться, " + users[user]["name"] + '! Какой у тебя уровень владения английским?' \
                                                                 ' Ты в любой момент сможешь изменить уровень и тебе станут доступны новые слова!'
        card = {
            "type": "ItemsList",
            "header": {
                "text": "Какой у тебя уровень владения английским?"
            },
            "items": levels_items(),
        }
        tts = text
        if OS == "Yandex":
            tts += 'Чтобы узнать уровни, скажи: "Уровни"'
        else:
            tts += "sil <[100]>А1 sil <[70]> А2 sil <[70]> Б1 sil <[70]> Б2 sil <[70]> Ц1"
        res = make_response(text=text, card=card, tts=tts)


    elif users[user]["action"] == "level":
        users[user]["is_registered"] = True
        level = user_request
        level = correct(level)
        if level == 'C2':
            res = make_response(text="Я считаю, что носитель языка в действительности не оценит данный навык, "
                                     "так что я не преподаю уровень C2. Однако, если ты хочешь углубиться - выбирай"
                                     " C1, он тоже очень интересный!",
                                tts="Я считаю,sil <[50]> что носитель языка в действительности не оценит данный навык,sil <[50]> так"
                                    " что я не преподаю уровень Ц2. Однако,sil <[50]> если ты хочешь углубитьсяsil <[50]> - выбирай Ц1,sil <[50]>"
                                    " он тоже очень интересный!")
        elif level != "wrong_answer":
            users[user]["level"] = level
            card = {
                "type": "ItemsList",
                "header": {
                    "text": "В какой режим ты хочешь поиграть сегодня?"
                },
                "items": modes1,
            }
            text = "Отлично, теперь мы готовы начинать!"
            if OS == "Display":
                tts = 'Отлично,sil <[50]> мы готовы начинать! Теперь я буду вести статистику.sil <[50]> Чтобы узнать её, скажи: "Статистика". ' \
                      'В какой режим ты хочешь поиграть сегодня?sil <[100]>   Карточки,sil <[70]> Слова,sil <[70]> Игра на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина.'
            else:
                tts = 'Отлично,sil <[50]> мы готовы начинать! Теперь я буду вести статистику.sil <[50]> Чтобы узнать её, скажи: "Статистика". ' \
                      'В какой режим ты хочешь поиграть сегодня?sil <[100]>   Карточки,sil <[70]> Игра на время,sil <[70]> Детский режим.'
            buttons = [{"title": "Ещё режимы", "hide": False}]
            res = make_response(card=card, text=text, tts=tts, buttons=buttons)
            users[user]["action"] = "mode_selection"

        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                res = make_response(text="Если ты не знаешь какой у тебя уровень, можешь выбрать для начала А1.")
            else:
                res = make_response(text="Мне не удалось понять какой у тебя уровень знания языка &#128546. Скажи,"
                                         " пожалуйста, ещё раз&#128150")


    elif users[user]["action"] == "mode_selection":
        users[user]["enter_mode"] = True
        users[user]["time_game"]["strike"], users[user]["time_game"]["start_time"] = 0, -1
        users[user]["cards"]["last_word"] = ()
        users[user]["words_game"]["last_word"], users[user]["words_game"]["tell_words"] = '', []
        if user_request in modes_list:
            users[user]["game_mode"] = user_request.capitalize()
            if OS == "Yandex" and (
                    user_request == "карточки наоборот" or user_request == "буквы" or user_request == "слова" or user_request == "викторина"):
                res = make_response(
                    text="Прости, этот режим доступен только при игре с экраном. Но без экрана ты всё равно можешь поиграть в большинство режимов этого навыка! Выбери ещё раз.")
            elif user_request != "детский режим" and user_request != "слова":
                users[user]["action"] = "topic_selection"
                text = f"Отлично! Ты хочешь учить слова из конкретной темы или мне выбирать слова случайным образом? " \
                       f"Есть темы:\n\n{', '.join(words[users[user]['level']].keys()).capitalize()}"
                tts = f"Отлично! Ты хочешь учить слова из конкретной темы или мне выбирать слова случайным образом? " \
                      f"Есть темы:sil <[100]>\n\n{',sil <[70]> '.join(words[users[user]['level']].keys()).capitalize()}"
                buttons = []
                flag_for_buttons = False
                for topic in words[users[user]['level']].keys():
                    buttons.append({"title": topic, "hide": True})
                res = make_response(text=text, buttons=buttons, tts=tts)
            else:
                if users[user]["game_mode"] == "Слова":
                    kusok = "Слов+а"
                else:
                    kusok = users[user]["game_mode"]
                text = f'Прекрасно! Сейчас мы будем играть в "{users[user]["game_mode"]}". Правильно?'
                tts = f'Прекрасно! Сейчас мы будем играть в "{kusok}". Правильно?'
                res = make_response(text=text, tts=tts)
                users[user]["action"] = "in_game"

        else:
            text = "Я не поняла режим &#128546. Выбери ещё раз&#128150:"
            card = {
                "type": "ItemsList",
                "header": {
                    "text": text
                },
                "items": modes1,
            }
            if OS == "Display":
                tts = "Я не поняла режим &#128546. Выбери ещё раз&#128150:sil <[200]> Карточки,sil <[70]> Слова,sil <[70]> Игры на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина"
            else:
                tts = "Я не поняла режим &#128546. Выбери ещё раз&#128150:sil <[200]> Карточки,sil <[70]> Игра на время,sil <[70]> Детский режим."
            buttons = [{"title": "Ещё режимы", "hide": False}]
            res = make_response(text=text, tts=tts, card=card, buttons=buttons)


    elif users[user]["action"] == "topic_selection":
        topic = event["request"]["command"]
        users[user]["enter_mode"] = True
        users[user]["time_game"]["strike"], users[user]["time_game"]["start_time"] = 0, -1
        users[user]["cards"]["last_word"] = ()
        users[user]["words_game"]["last_word"], users[user]["words_game"]["tell_words"] = '', []

        if topic not in words[users[user]["level"]].keys():
            text = f"Я не поняла тему &#128546. Выбери ещё раз&#128150:\n\n{', '.join(words[users[user]['level']].keys()).capitalize()}"
            buttons = []
            flag_for_buttons = False
            for topic in words[users[user]['level']].keys():
                buttons.append({"title": topic, "hide": True})
            res = make_response(text=text, buttons=buttons)

        else:
            users[user]["topic"] = topic
            users[user]["action"] = "in_game"
            res = handler(event, context)

    elif users[user]["game_mode"] != "Детский режим" and users[user]["game_mode"] != "Слова" and users[user][
        "action"] == "in_game" and users[user]["topic"] != "все слова" and len(
            list(set(words[users[user]["level"]][users[user]["topic"]].keys()) - set(
                    users[user]["learned_words"][users[user]["level"]]))) == 2:
        res = make_response(
            text=f'Ты полностью знаешь тему "{users[user]["topic"]}" на уровне {users[user]["level"]}, так что рекоменую перейти к изучению следующей! Можешь продолжать играть.')
        users[user]["learned_words"][users[user]["level"]] = list(
            set(users[user]["learned_words"][users[user]["level"]]) - set(
                words[users[user]["level"]][users[user]["topic"]].keys()))

    elif users[user]["action"] == "in_game":
        mode = users[user]["game_mode"]
        topic = users[user]["topic"]
        if yes_or_no(event) is False and users[user]["enter_mode"] is True or users[user]["words_game"]["end"] is True:
            users[user]["action"] = "mode_selection"
            text = "В какой режим ты хочешь поиграть сегодня?"
            card = {
                "type": "ItemsList",
                "header": {
                    "text": "В какой режим ты хочешь поиграть сегодня?"
                },
                "items": modes1,
            }
            if OS == "Display":
                tts = "В какой режим ты хочешь поиграть сегодня?sil <[100]>    Карточки,sil <[70]> Слова,sil <[70]> Игры на время,sil <[70]> Детский режим,sil <[70]> Карточки наоборот,sil <[70]> Буквы,sil <[70]> Викторина."
            else:
                tts = "В какой режим ты хочешь поиграть сегодня?sil <[100]>    Карточки,sil <[70]> Игра на время,sil <[70]> Детский режим."
            buttons = [{"title": "Ещё режимы", "hide": False}]
            res = make_response(text=text, tts=tts, card=card, buttons=buttons)

        elif users[user]["modes_rules"][mode] is False:
            res = make_response(text=rules[mode] + "На этом всё, начинаем?")
            users[user]["modes_rules"][mode] = True
        else:
            if mode == "Карточки":
                res = cards_1(user_request, user, topic, users[user]["level"], first_request=users[user]["enter_mode"])
            elif mode == "Викторина":
                res = test(user_request, user, topic, users[user]["level"], first_request=users[user]["enter_mode"])
            elif mode == "Детский режим":
                res = kids(user_request, user, first_request=users[user]["enter_mode"])
            elif mode == "Карточки наоборот":
                res = cards_2(user_request, user, topic, users[user]["level"], first_request=users[user]["enter_mode"])
            elif mode == "Игра на время":
                res = time_game(user_request, user, topic, users[user]["level"],
                                first_request=users[user]["enter_mode"])
            elif mode == "Буквы":
                res = letters(user_request, user, topic, users[user]["level"], first_request=users[user]["enter_mode"])
            elif mode == "Слова":
                res = words_game(user_request, user, topic, users[user]["level"],
                                 first_request=users[user]["enter_mode"])

            if users[user]["enter_mode"] is True:
                users[user]["enter_mode"] = False
                res["response"]["text"] = "Отлично, Тогда начинаем! Первое слово:\n" + res["response"]["text"]

    if flag_for_buttons is True:
        res["response"]["buttons"] = [butt for butt in res["response"]["buttons"] if butt["hide"] is False] + [
            {
                "title": "Помощь",
                "hide": True
            },
            {
                "title": "Продолжить",
                "hide": True
            },
            {
                "title": "Статистика",
                "hide": True
            },
            {
                "title": "Поменять режим",
                "hide": True
            },
            {
                "title": "Поменять тему",
                "hide": True
            }
        ]
    if 'Приятно познакомиться' in res["response"]["text"]:
        res["response"]["text"] = "Приятно познакомиться, " + users[user][
            "name"] + '! Какой у тебя уровень владения английским? Чтобы узнать уровни, скажи: "Уровни".\nТы в любой момент сможешь ' \
                      'изменить уровень и тебе станут доступны новые слова!'
    text = res["response"]["text"]
    tts = res["response"]["tts"]
    buttons = res["response"]["buttons"]
    card = res["response"]["card"]
    res["application_state"]["value"][0] = make_response(text=text, tts=tts, buttons=buttons, card=card)
    if flag is True:
        res["application_state"]["value"][1] = make_response(text=text, tts=tts, buttons=buttons, card=card)
        try:
            if res["response"]["buttons"][1]["title"] == "Продолжить":
                res["response"]["buttons"].pop(1)
        except:
            pass
    else:
        event_request = event["state"]["application"]["value"][1]
        text = event_request["response"]["text"]
        tts = event_request["response"]["tts"]
        buttons = event_request["response"]["buttons"]
        card = event_request["response"]["card"]
        res["application_state"]["value"][1] = make_response(text=text, tts=tts, buttons=buttons, card=card)

    percent = len(users[user]["learned_words"][users[user]["level"]]) / len(words[users[user]["level"]]["все слова"])
    if percent >= 0.88 and users[user]["action"] != "in_game":
        users[user]["statistic"][users[user]["level"]] = str(percent * 100)[:4] + "%"
        if percent == 1:
            users[user]["statistic"][users[user]["level"]] = "100%"
        if res["response"]["tts"]:
            res["response"][
                "tts"] += f"\nКстати,sil <[70]> ты уже достаточно хорошо знаешь {users[user]['level']},sil <[70]> можно переходить на следующий!"
        else:
            res["response"][
                "tts"] = f"\nКстати,sil <[70]> ты уже достаточно хорошо знаешь {users[user]['level']},sil <[70]> можно переходить на следующий!"
    if percent >= 0.94:
        users[user]["statistic"][users[user]["level"]] = str(percent * 100)[:4] + "%"
        if percent == 1:
            users[user]["statistic"][users[user]["level"]] = "100%"
        users[user]["learned_words"][users[user]["level"]] = list(
            set(users[user]["learned_words"][users[user]["level"]]) - set(
                words[users[user]["level"]]["все слова"].keys()))
    return res


def repeate(request):
    return request["state"]["application"]["value"][0]


def help_response():
    return make_response(text=help_txt, tts=help_tts)


def change_level(user_command, user):
    answer_correct_func = correct(user_command)
    if answer_correct_func != "wrong_answer":
        users[user]["level"] = answer_correct_func
        return "OK"
    else:
        return "WRONG_TYPE"


def change_name(user_command, user):
    if user_command.split()[-1] not in ['имя', "на"] and len(user_command.split()[-1]) != 1:
        users[user]["name"] = user_command.split()[-1].capitalize()
        return True
    return False


def statistic(user, level):
    return 'ㅤㅤㅤ'.join([f'{topic}: {str(int(len(users[user]["learned_words"][level][topic]) / len(words[level][topic]) * 100)) + "%"}' for topic in words[level]]).replace("все слова", "Общий прогресс")


def rules_response(user):
    return make_response(text=rules[users[user]["game_mode"]])


def add_user(user_id):
    global users
    user = {
        "is_registered": False,
        "name": "N",
        "level": "A1",
        "learned_words": {
            "A1": {
                "все слова": [],
                "глаголы": [],
                "окружающий мир": [],
                "семья": [],
                "коммуникация": [],
                "туризм": [],
                "прилагательные": [],
                "наречия": []
            },
            "A2": {
                "все слова": [],
                "глаголы": [],
                "работа": [],
                "досуг": [],
                "природа": []
            },
            "B1": {
                "все слова": [],
                "глаголы": [],
                "существительные": [],
                "социум": [],
                "прилагательные": [],
                "наречия": []
            },
            "B2": {
                "все слова": [],
                "глаголы": [],
                "образование": [],
                "социальные тренды": [],
                "литература": []
            },
            "C1": {
                "все слова": [],
                "глаголы": [],
                "наука": [],
                "социум": [],
                "климат": []
            },
            "kids": []
        },
        "action": "special_case",
        "game_mode": "N",
        "topic": "N",
        "enter_mode": True,
        "last_eng_word": "",
        "modes_rules": {
            "Карточки": False,
            "Викторина": False,
            "Детский режим": False,
            "Карточки наоборот": False,
            "Слова": False,
            "Буквы": False,
            "Игра на время": False,
        },
        "time_game": {
            "start_time": -1,
            "word": '',
            "true_answer": '',
            "strike": 0,
            "load": -1
        },
        "test_word": "",
        "last_word": ("", ""),
        "cards": {"last_word": ()},
        "kids": {"last_word": ("", "")},
        "letters": {
            "word": ''
        },
        "words_game": {"last_word": '',
                       "tell_words": [],
                       "end": False}
    }
    users[user_id] = user


def get_name(input_name):
    name = input_name
    name = name.replace("Меня зовут ", "")
    name = name.replace("Моё имя ", "")
    name = name.replace("Называй меня ", "")
    name = name.replace("Я ", "")
    name = name if len(name.split()) == 0 else name.split()[-1]
    return name.capitalize()


def greeting(user):
    global users
    if users[user]["is_registered"] is True:
        text = 'Рада слышать тебя снова, ' + users[user]["name"] + '! Напоминаю, если есть какие-то вопросы - скажи ' \
                                                                   '"помощь"\nВ какой режим хочешь сыграть?'
    else:
        text = 'Привет! Я - Мэй, и я люблю учить английский язык. А ты наверное хочешь позаниматься английским! ' \
               'Если у тебя будут какие-то вопросы, скажи "Помощь"\nКак тебя зовут?'
    return text


def correct(level):
    lev = "wrong_answer"
    if "а 1" in level or "a 1" in level:
        lev = "A1"
    elif "а 2" in level or "a 2" in level:
        lev = "A2"
    elif "б 1" in level or "b 1" in level or "в 1" in level:
        lev = "B1"
    elif "б 2" in level or "b 2" in level or "в 2" in level:
        lev = "B2"
    elif "ц 1" in level or "с 1" in level or "c 1" in level:
        lev = "C1"
    return lev


def yes_or_no(event):
    or_ut = event['request']['command'].lower().replace('ё', 'е')

    # Функция вернёт True, если ответ положительный и вернёт False, если ответ отрицательный
    if or_ut in No_list:
        return False
    elif or_ut in Yes_list:
        return True
    else:
        return "error"


def cards_1(user_request, user, topic, level, first_request=False):
    if len(list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level][topic]))) >= 4:
        choise_list = list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level][topic]))
    else:
        choise_list = words[level][topic].keys()

    if first_request is True:
        eng_word = random.choice(choise_list)
        rus_word = words[level][topic][eng_word]
        card_res = eng_word
        users[user]["cards"]["last_word"] = (eng_word, rus_word)
    else:
        if user_request.lower() in users[user]["cards"]["last_word"][1]:
            users[user]['learned_words'][level][topic].append(users[user]["cards"]["last_word"][0])
            if topic == "все слова":
                try:
                    users[user]['learned_words'][level][find_topic(level, users[user]["cards"]["last_word"][0])].append(users[user]["cards"]["last_word"][0])
                except:
                    pass
            part1 = str(f'{random.choice(yes)}! {users[user]["cards"]["last_word"][0]} - это {user_request.lower()}.')
            eng_word = random.choice(choise_list)
            rus_word = words[level][topic][eng_word]
            users[user]["cards"]["last_word"] = (eng_word, rus_word)
            card_res = part1 + f"\nСледующее слово: {eng_word}"
        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                part1 = str(f'{random.choice(ok)}, {users[user]["cards"]["last_word"][0]} переводится как {users[user]["cards"]["last_word"][1][0]}.')
            else:
                part1 = str(f'{random.choice(no)}, {users[user]["cards"]["last_word"][0]} переводится как {users[user]["cards"]["last_word"][1][0]}.')
            eng_word = random.choice(choise_list)
            rus_word = words[level][topic][eng_word]
            users[user]["cards"]["last_word"] = (eng_word, rus_word)
            card_res = part1 + f"\nВот новое слово: {eng_word}"
    return make_response(text=card_res)


def button(level, topic, answer):
    butt = random.sample(
        [{"title": word, "hide": False} for word in words[level][topic] if word != answer], 3) + [{"title": answer, "hide": False}]
    random.shuffle(butt)
    return butt


def ru_word(level, topic, x):
    return words[level][topic][x][0]


def test(user_request, user, topic, level, first_request=False):
    if len(list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level][topic]))) >= 4:
        choise_list = list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level][topic]))
    else:
        choise_list = words[level][topic].keys()

    if first_request is True:
        users[user]["test_word"] = random.choice(choise_list)
        buttons = button(level, topic, users[user]["test_word"])
        tts = 'sil <[70]>'.join([butt["title"] for butt in buttons])
        return make_response(text=ru_word(level, topic, users[user]["test_word"]), buttons=buttons, tts=tts)

    elif users[user]["test_word"].lower() == user_request:
        ruword = ru_word(level, topic, users[user]["test_word"])
        users[user]["learned_words"][level][topic].append(ruword)
        if topic == "все слова":
            try:
                users[user]["learned_words"][level][find_topic(level, ruword)].append(ruword)
            except:
                pass
        users[user]["test_word"] = random.choice(choise_list)
        buttons = button(level, topic, users[user]["test_word"])
        answ = good_answer[random.randint(0, len(good_answer) - 1)]
        text = f"{answ} Следующее слово: {ruword}"
        tts = 'sil <[70]>'.join([butt["title"] for butt in buttons])
        return make_response(text=text, buttons=buttons, tts=tts)
    else:
        later_word = users[user]["test_word"]
        users[user]["test_word"] = random.choice(choise_list)
        buttons = button(level, topic, users[user]["test_word"])
        answ_bed = bad_answer[random.randint(0, len(bad_answer) - 1)]
        he_dont_know = False
        for phrase in i_dont_know:
            if phrase in user_request.lower():
                he_dont_know = True
        if he_dont_know:
            answ_bed = random.choice(ok)
        text = f"{answ_bed} &#128546. Правильный ответ был: {later_word}. Следующее слово для тебя: {ru_word(level, topic, users[user]['test_word'])}"
        tts = 'sil <[70]>'.join([butt["title"] for butt in buttons])
        return make_response(text=text, buttons=buttons, tts=tts)


def kids(user_request, user, first_request=False):
    if len(list(set(words["kids"].keys()) - set(users[user]["learned_words"]["kids"]))) >= 4:
        choise_list = list(set(words["kids"].keys()) - set(users[user]["learned_words"]["kids"]))
    else:
        choise_list = words["kids"].keys()

    if first_request is True:
        eng_word = random.choice(choise_list)
        rus_word = words["kids"][eng_word]
        text = eng_word
        users[user]["kids"]["last_word"] = (eng_word, rus_word)
    else:
        if user_request.lower() in users[user]["kids"]["last_word"][1]:
            users[user]["learned_words"]["kids"].append(users[user]["kids"]["last_word"][0])
            part1 = str(f'{random.choice(yes)}! {users[user]["kids"]["last_word"][0]} - это {user_request.lower()}.')
            eng_word = random.choice(choise_list)
            rus_word = words["kids"][eng_word]
            users[user]["kids"]["last_word"] = (eng_word, rus_word)
            text = part1 + f"\nСледующее слово: {eng_word}"
        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                part1 = f'{random.choice(ok)}, {users[user]["kids"]["last_word"][0]} переводится как {users[user]["kids"]["last_word"][1][0]}.'
            else:
                part1 = f'{random.choice(no)}, {users[user]["kids"]["last_word"][0]} переводится как {users[user]["kids"]["last_word"][1][0]}.'
            eng_word = random.choice(choise_list)
            rus_word = words["kids"][eng_word]
            users[user]["kids"]["last_word"] = (eng_word, rus_word)
            text = part1 + f"\nВот новое слово: {eng_word}"
    card = {
        "type": "BigImage",
        "title": text,
        "image_id": images[eng_word]
    }
    try:
        tts = text + sounds[eng_word]
    except:
        tts = text
    return make_response(text=text, tts=tts, card=card)


def letters(user_request, user, topic, level, first_request=False):
    if len(list(set(filter(lambda x: len(x.split()[-1]) < 7, words[level][topic].keys())) - set(users[user]["learned_words"][level]))) >= 4:
        choise_list = list(set(filter(lambda x: len(x.split()[-1]) < 7, words[level][topic].keys())) - set(users[user]["learned_words"][level]))
    else:
        choise_list = list(set(filter(lambda x: len(x.split()[-1]) < 7, words[level][topic].keys())))

    if first_request is True:
        users[user]["letters"]["word"] = random.choice(choise_list)
        lis = list(users[user]["letters"]["word"].split()[-1].lower())
        random.shuffle(lis)
        quest = ' '.join(lis)
        if len(users[user]["letters"]["word"].split()) != 1:
            quest = 'to ' + quest
        return make_response(text=quest)
    else:
        if user_request.lower() == users[user]["letters"]["word"].lower():
            resp = f'{random.choice(yes)}! Я загадывала именно {user_request}.'
            users[user]["learned_words"][level][topic].append(user_request)
            if topic == "все слова":
                try:
                    users[user]["learned_words"][level][find_topic(level, user_request)].append(user_request)
                except:
                    pass
        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                resp = f'{random.choice(ok)}, верно было {users[user]["letters"]["word"]}.'
            else:
                resp = f'{random.choice(no)}, верно было {users[user]["letters"]["word"]}.'
        users[user]["letters"]["word"] = random.choice(choise_list)
        lis = list(users[user]["letters"]["word"].split()[-1].lower())
        random.shuffle(lis)
        quest = ' '.join(lis)
        tts_quest = 'sil <[50]> '.join(lis)
        if len(users[user]["letters"]["word"].split()) != 1:
            quest = 'to ' + quest
        tts = resp + "Новый набор букв:sil <[70]> " + tts_quest
        resp += f' Новый набор букв:\n {quest}'
        return make_response(text=resp, tts=tts)


def cards_2(user_request, user, topic, level, first_request=False):
    if len(list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level]))) >= 4:
        choise_list = list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level]))
    else:
        choise_list = words[level][topic].keys()

    if first_request is True:
        eng_word = random.choice(choise_list)
        rus_word = words[level][topic][eng_word]
        card2_res = rus_word[0]
        users[user]["cards"]["last_word"] = (eng_word, rus_word[0])
    else:
        if user_request.lower() in users[user]["cards"]["last_word"][0]:
            users[user]['learned_words'][level][topic].append(users[user]["cards"]["last_word"][0])
            if topic == "все слова":
                try:
                    users[user]['learned_words'][level][find_topic(level, users[user]["cards"]["last_word"][0])].append(users[user]["cards"]["last_word"][0])
                except:
                    pass
            part1 = str(f'{random.choice(yes)}! {users[user]["cards"]["last_word"][1]} - это {user_request.lower()}.')
            eng_word = random.choice(choise_list)
            rus_word = words[level][topic][eng_word][0]
            users[user]["cards"]["last_word"] = (eng_word, rus_word)
            card2_res = part1 + f"\nСледующее слово: {rus_word}"
        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                part1 = str(f'{random.choice(ok)}, {users[user]["cards"]["last_word"][0]} переводится как {users[user]["cards"]["last_word"][1][0]}.')
            else:
                part1 = str(f'{random.choice(no)}, {users[user]["cards"]["last_word"][0]} переводится как {users[user]["cards"]["last_word"][1][0]}.')
            eng_word = random.choice(choise_list)
            rus_word = words[level][topic][eng_word][0]
            users[user]["cards"]["last_word"] = (eng_word, rus_word)
            card2_res = part1 + f"\nВот новое слово: {rus_word}"
    return make_response(text=card2_res)


def words_game(user_request, user, topic, level, first_request=False):
    flag = True
    users[user]["words_game"]["end"] = False
    if "сда" in user_request.lower():
        users[user]["words_game"]["end"] = True
        t_word = len(users[user]["words_game"]["tell_words"])
        users[user]["words_game"]["last_word"], users[user]["words_game"]["tell_words"] = '', []
        if t_word >= 30:
            return make_response(text="Ты хорошо держался, ничего страшного")
        else:
            return make_response(text="Ты слишком слаб для меня&#128546\n Стоит еще поучиться на других режимах;)")
    if first_request is False:
        arg = 0 if user_request.split()[-1][0] in eng_letters else 1
        try:
            if len(user_request.split()[-1]) > 2 and translate(arg, user_request.split()[-1]).lower() not in user_request.split()[-1] and '(' not in translate(arg, user_request.split()[-1]):
                answer = translate(arg, user_request.split()[-1])
                words_game_res = f"{user_request.split()[-1]} - это {answer}"
                flag = True
            else:
                words_game_res = f"Такого слова не существует. Назови слово на букву {users[user]['words_game']['last_word'][-1]}"
                flag = False
        except RuntimeError:
            words_game_res = f"Такого слова не существует. Назови слово на букву {users[user]['words_game']['last_word'][-1]}"
            flag = False
    if flag is False:
        return make_response(text=words_game_res)
    if users[user]["words_game"]["last_word"] == "":
        words_game_res = random.choice(list(set(latet[random.choice("qwertyuiopasdfghjklzxcvbnm")])))
        users[user]["words_game"]["last_word"] = words_game_res.strip()
        users[user]["words_game"]["tell_words"].append(words_game_res.strip())
    else:
        if user_request[0] == users[user]["words_game"]["last_word"][-1] and user_request not in \
                users[user]["words_game"]["tell_words"]:
            users[user]["words_game"]["tell_words"].append(user_request.strip())
            users[user]["words_game"]["last_word"] = user_request.strip()
            if len(list(set(latet[random.choice(user_request[0])]) - set(users[user]["words_game"]["tell_words"]))) != 0:
                words_game_res = random.choice(list(set(latet[random.choice(user_request[-1])]) - set(users[user]["words_game"]["tell_words"])))
                users[user]["words_game"]["last_word"] = words_game_res.strip()
                users[user]["words_game"]["tell_words"].append(words_game_res.strip())
            else:
                words_game_res = "Я сдаюсь, ты победил"
        else:
            if user_request[0] != users[user]["words_game"]["last_word"][-1]:
                words_game_res = f"Упс... {random.choice(no)}. Назови слово на букву {users[user]['words_game']['last_word'][-1]}"
            if user_request in users[user]["words_game"]["tell_words"]:
                words_game_res = f"Упс... Это слово уже было названо. Назови слово на букву {users[user]['words_game']['last_word'][-1]}, которого еще не было в нашей игре ранее"

    return make_response(text=words_game_res)


def time_game(user_request, user, topic, level, first_request=False):
    if len(list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level]))) >= 4:
        choise_list = list(set(words[level][topic].keys()) - set(users[user]["learned_words"][level]))
    else:
        choise_list = words[level][topic].keys()

    if users[user]["time_game"]["start_time"] == -1:
        users[user]["time_game"]["start_time"] = time.time()
        quest = random.choice(choise_list)
        users[user]["time_game"]["word"] = quest
        users[user]["time_game"]["true_answer"] = words[level][topic][quest]
        res = make_response(text=users[user]['time_game']['word'])
    elif time.time() - users[user]["time_game"]["start_time"] <= 100:
        quest = random.choice(choise_list)
        users[user]["time_game"]["word"] = quest
        if user_request.lower() in users[user]["time_game"]["true_answer"]:
            users[user]["time_game"]["strike"] += 1
            users[user]["learned_words"][level][topic].append(quest)
            if topic == "все слова":
                try:
                    users[user]["learned_words"][level][find_topic(level, quest)].append(quest)
                except:
                    pass
            ans = f"{random.choice(yes)}, следующее слово {quest}."
        else:
            he_dont_know = False
            for phrase in i_dont_know:
                if phrase in user_request.lower():
                    he_dont_know = True
            if he_dont_know:
                ans = f"{random.choice(ok)}, следующее слово {quest}."
            else:
                ans = f"{random.choice(no)}, следующее слово {quest}."
        users[user]["time_game"]["true_answer"] = words[level][topic][quest]
        res = make_response(text=ans)

    else:
        ans = f'Время вышло! Вы успели набрать {users[user]["time_game"]["strike"]} очков. Скажи "Поменять режим" если хочешь сыграть во что-то новое или скажи: "Дальше".'
        users[user]["time_game"]["strike"], users[user]["time_game"]["start_time"] = 0, -1
        res = make_response(text=ans)
    return res


def levels():
    text = levels_txt
    tts = levels_tts
    return make_response(text=text, tts=tts)


def commands():
    return make_response(text=commands_txt)


def find_topic(level, word):
    for topic in words[level]:
        if topic != "все слова":
            if word in words[level][topic]:
                return topic


if __name__ == '__main__':
    app.run()
