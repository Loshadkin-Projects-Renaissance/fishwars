creator = 792414733

ban = []

sealist = ['crystal', 'black', 'moon']
fighthours = [12, 16, 20, 0]
letters=['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

allletters=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 
           'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']

sea_localization = {
    'crystal': '💎Кристальное',
    'black': '⚫️Чёрное',
    'moon': '🌙Лунное'
}

sea_emojies = {
    'crystal': '💎',
    'black': '⚫️',
    'moon':  '🌙'
}

emojies_sea = {}

for line in sea_localization.copy():
    sea_localization.update({sea_localization[line]: line})

for line in sea_emojies:
    emojies_sea.update({sea_emojies[line]: line})

def sea_ru(sea):
    return sea_localization.get(sea)

def seatoemoj(sea=None, emoj=None):
    return sea_emojies.get(sea) if sea else emojies_sea.get(emoj)