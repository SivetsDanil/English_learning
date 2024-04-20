from translate import Translator

rus_letters = 'ёйцукенгшщзхъфывапролджэячсмитьбю'
eng_letters = 'qwertyuiopasdfghjklzxcvbnm'

def translate(x, word):
    if x == 0:
        translator = Translator(from_lang='English', to_lang='Russian')
    else:
        translator = Translator(from_lang='Russian', to_lang='English')
    return translator.translate(word)
