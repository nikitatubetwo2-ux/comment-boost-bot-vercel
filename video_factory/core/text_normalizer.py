"""
Нормализация текста для TTS (Text-to-Speech)
Замена дат, чисел, аббревиатур на слова для корректной озвучки
Поддержка: русский, английский
"""

import re
from typing import Dict, List, Tuple


class TextNormalizer:
    """Нормализация текста для озвучки без ошибок"""
    
    # Русские числительные
    RU_ONES = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    RU_ONES_F = ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    RU_TEENS = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 
                'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
    RU_TENS = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 
               'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
    RU_HUNDREDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
                   'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
    
    RU_MONTHS = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    
    # Английские числительные
    EN_ONES = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    EN_TEENS = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
                'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']
    EN_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty',
               'sixty', 'seventy', 'eighty', 'ninety']
    
    EN_MONTHS = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    # Аббревиатуры и сокращения
    RU_ABBREVIATIONS = {
        'г.': 'года',
        'гг.': 'годов',
        'в.': 'века',
        'вв.': 'веков',
        'т.е.': 'то есть',
        'т.к.': 'так как',
        'т.д.': 'так далее',
        'т.п.': 'тому подобное',
        'др.': 'другие',
        'см.': 'смотри',
        'ок.': 'около',
        'прим.': 'примерно',
        'млн': 'миллионов',
        'млрд': 'миллиардов',
        'тыс.': 'тысяч',
        'км': 'километров',
        'м': 'метров',
        'кг': 'килограммов',
        'СССР': 'Эс Эс Эс Эр',
        'США': 'Соединённые Штаты Америки',
        'ФРГ': 'Эф Эр Гэ',
        'ГДР': 'Гэ Дэ Эр',
        'НКВД': 'Эн Ка Вэ Дэ',
        'КГБ': 'Ка Гэ Бэ',
        'ЦРУ': 'Цэ Эр У',
        'ООН': 'О О Эн',
        'НАТО': 'НАТО',
        'SS': 'Эс Эс',
        'SA': 'Эс А',
        'RAF': 'Эр Эй Эф',
        'РККА': 'Эр Ка Ка А',
    }
    
    EN_ABBREVIATIONS = {
        'e.g.': 'for example',
        'i.e.': 'that is',
        'etc.': 'et cetera',
        'vs.': 'versus',
        'approx.': 'approximately',
        'ca.': 'circa',
        'USSR': 'U S S R',
        'USA': 'U S A',
        'UK': 'U K',
        'NATO': 'NATO',
        'SS': 'S S',
        'RAF': 'R A F',
        'USAF': 'U S A F',
        'CIA': 'C I A',
        'FBI': 'F B I',
        'KGB': 'K G B',
        'NKVD': 'N K V D',
    }
    
    # Римские цифры
    ROMAN_NUMERALS = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
        'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
        'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
        'XXI': 21
    }

    
    @classmethod
    def number_to_words_ru(cls, n: int, feminine: bool = False) -> str:
        """Число в слова (русский)"""
        if n == 0:
            return 'ноль'
        
        if n < 0:
            return 'минус ' + cls.number_to_words_ru(-n, feminine)
        
        words = []
        ones = cls.RU_ONES_F if feminine else cls.RU_ONES
        
        # Миллиарды
        if n >= 1_000_000_000:
            billions = n // 1_000_000_000
            words.append(cls._ru_with_suffix(billions, 'миллиард', 'миллиарда', 'миллиардов'))
            n %= 1_000_000_000
        
        # Миллионы
        if n >= 1_000_000:
            millions = n // 1_000_000
            words.append(cls._ru_with_suffix(millions, 'миллион', 'миллиона', 'миллионов'))
            n %= 1_000_000
        
        # Тысячи (женский род)
        if n >= 1000:
            thousands = n // 1000
            words.append(cls._ru_with_suffix(thousands, 'тысяча', 'тысячи', 'тысяч', feminine=True))
            n %= 1000
        
        # Сотни
        if n >= 100:
            words.append(cls.RU_HUNDREDS[n // 100])
            n %= 100
        
        # Десятки и единицы
        if n >= 20:
            words.append(cls.RU_TENS[n // 10])
            n %= 10
        elif n >= 10:
            words.append(cls.RU_TEENS[n - 10])
            n = 0
        
        if n > 0:
            words.append(ones[n])
        
        return ' '.join(w for w in words if w)
    
    @classmethod
    def _ru_with_suffix(cls, n: int, one: str, two_four: str, many: str, feminine: bool = False) -> str:
        """Число с правильным окончанием"""
        num_words = cls.number_to_words_ru(n % 1000, feminine)
        last_two = n % 100
        last_one = n % 10
        
        if 11 <= last_two <= 19:
            suffix = many
        elif last_one == 1:
            suffix = one
        elif 2 <= last_one <= 4:
            suffix = two_four
        else:
            suffix = many
        
        return f"{num_words} {suffix}"
    
    @classmethod
    def number_to_words_en(cls, n: int) -> str:
        """Число в слова (английский)"""
        if n == 0:
            return 'zero'
        
        if n < 0:
            return 'minus ' + cls.number_to_words_en(-n)
        
        words = []
        
        # Billions
        if n >= 1_000_000_000:
            words.append(cls.number_to_words_en(n // 1_000_000_000) + ' billion')
            n %= 1_000_000_000
        
        # Millions
        if n >= 1_000_000:
            words.append(cls.number_to_words_en(n // 1_000_000) + ' million')
            n %= 1_000_000
        
        # Thousands
        if n >= 1000:
            words.append(cls.number_to_words_en(n // 1000) + ' thousand')
            n %= 1000
        
        # Hundreds
        if n >= 100:
            words.append(cls.EN_ONES[n // 100] + ' hundred')
            n %= 100
        
        # Tens and ones
        if n >= 20:
            tens_word = cls.EN_TENS[n // 10]
            ones_word = cls.EN_ONES[n % 10]
            if ones_word:
                words.append(f"{tens_word}-{ones_word}")
            else:
                words.append(tens_word)
        elif n >= 10:
            words.append(cls.EN_TEENS[n - 10])
        elif n > 0:
            words.append(cls.EN_ONES[n])
        
        return ' '.join(words)
    
    @classmethod
    def year_to_words_ru(cls, year: int) -> str:
        """Год в слова (русский): 1942 -> тысяча девятьсот сорок второго"""
        if 1000 <= year <= 2100:
            # Для годов используем родительный падеж
            base = cls.number_to_words_ru(year)
            # Заменяем окончание на родительный падеж
            replacements = [
                ('один', 'первого'), ('два', 'второго'), ('три', 'третьего'),
                ('четыре', 'четвёртого'), ('пять', 'пятого'), ('шесть', 'шестого'),
                ('семь', 'седьмого'), ('восемь', 'восьмого'), ('девять', 'девятого'),
                ('десять', 'десятого'), ('одиннадцать', 'одиннадцатого'),
                ('двенадцать', 'двенадцатого'), ('тринадцать', 'тринадцатого'),
                ('двадцать', 'двадцатого'), ('тридцать', 'тридцатого'),
                ('сорок', 'сорокового'), ('пятьдесят', 'пятидесятого'),
            ]
            for old, new in replacements:
                if base.endswith(old):
                    return base[:-len(old)] + new
            return base + 'го'
        return cls.number_to_words_ru(year)
    
    @classmethod
    def year_to_words_en(cls, year: int) -> str:
        """Год в слова (английский): 1942 -> nineteen forty-two"""
        if 1000 <= year <= 1999:
            first = year // 100
            second = year % 100
            if second == 0:
                return cls.number_to_words_en(first) + ' hundred'
            return cls.number_to_words_en(first) + ' ' + cls.number_to_words_en(second)
        elif 2000 <= year <= 2009:
            return 'two thousand' + (' ' + cls.number_to_words_en(year % 100) if year % 100 else '')
        elif 2010 <= year <= 2099:
            return 'twenty ' + cls.number_to_words_en(year % 100)
        return cls.number_to_words_en(year)

    
    @classmethod
    def normalize_for_tts(cls, text: str, language: str = 'ru') -> str:
        """
        Полная нормализация текста для TTS
        
        Args:
            text: Исходный текст
            language: 'ru' или 'en'
        
        Returns:
            Нормализованный текст готовый для озвучки
        """
        if language == 'ru':
            return cls._normalize_russian(text)
        else:
            return cls._normalize_english(text)
    
    @classmethod
    def _normalize_russian(cls, text: str) -> str:
        """Нормализация русского текста"""
        result = text
        
        # 1. Замена аббревиатур
        for abbr, full in cls.RU_ABBREVIATIONS.items():
            result = re.sub(r'\b' + re.escape(abbr) + r'\b', full, result, flags=re.IGNORECASE)
        
        # 2. Даты в формате DD.MM.YYYY или DD/MM/YYYY
        def replace_date(m):
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            day_word = cls.number_to_words_ru(day)
            month_word = cls.RU_MONTHS.get(month, '')
            year_word = cls.year_to_words_ru(year) + ' года'
            return f"{day_word} {month_word} {year_word}"
        
        result = re.sub(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', replace_date, result)
        
        # 3. Годы (1939, 1945 и т.д.)
        def replace_year(m):
            year = int(m.group(1))
            suffix = m.group(2) or ''
            if 1800 <= year <= 2100:
                year_word = cls.year_to_words_ru(year)
                if suffix in ['г.', 'г', 'году', 'года']:
                    return year_word + ' года'
                elif suffix in ['гг.', 'гг']:
                    return year_word
                return year_word + ' года'
            return m.group(0)
        
        result = re.sub(r'\b(\d{4})\s*(г\.|г|году|года|гг\.|гг)?\b', replace_year, result)
        
        # 4. Века (XIX век, XX век)
        def replace_century(m):
            roman = m.group(1).upper()
            if roman in cls.ROMAN_NUMERALS:
                num = cls.ROMAN_NUMERALS[roman]
                ordinal = cls._ordinal_ru(num)
                return f"{ordinal} век"
            return m.group(0)
        
        result = re.sub(r'\b([IVXLC]+)\s*век[а]?\b', replace_century, result, flags=re.IGNORECASE)
        
        # 5. Числа с единицами измерения
        def replace_number_with_unit(m):
            num = int(m.group(1))
            unit = m.group(2).lower()
            num_word = cls.number_to_words_ru(num)
            
            unit_map = {
                'км': ('километр', 'километра', 'километров'),
                'м': ('метр', 'метра', 'метров'),
                'кг': ('килограмм', 'килограмма', 'килограммов'),
                'тыс': ('тысяча', 'тысячи', 'тысяч'),
                'млн': ('миллион', 'миллиона', 'миллионов'),
                'млрд': ('миллиард', 'миллиарда', 'миллиардов'),
            }
            
            if unit in unit_map:
                one, two_four, many = unit_map[unit]
                last_two = num % 100
                last_one = num % 10
                if 11 <= last_two <= 19:
                    suffix = many
                elif last_one == 1:
                    suffix = one
                elif 2 <= last_one <= 4:
                    suffix = two_four
                else:
                    suffix = many
                return f"{num_word} {suffix}"
            
            return f"{num_word} {unit}"
        
        result = re.sub(r'(\d+)\s*(км|м|кг|тыс|млн|млрд)\.?\b', replace_number_with_unit, result)
        
        # 6. Простые числа (оставшиеся)
        def replace_number(m):
            num = int(m.group(0))
            if num > 10000000:  # Слишком большие числа оставляем
                return m.group(0)
            return cls.number_to_words_ru(num)
        
        result = re.sub(r'\b\d{1,7}\b', replace_number, result)
        
        # 7. Проценты
        result = re.sub(r'(\d+)%', lambda m: cls.number_to_words_ru(int(m.group(1))) + ' процентов', result)
        
        # 8. Специальные символы
        result = result.replace('&', ' и ')
        result = result.replace('№', 'номер ')
        result = result.replace('$', ' долларов ')
        result = result.replace('€', ' евро ')
        result = result.replace('£', ' фунтов ')
        
        # 9. Убираем лишние пробелы
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()
        
        return result
    
    @classmethod
    def _ordinal_ru(cls, n: int) -> str:
        """Порядковое числительное (русский)"""
        ordinals = {
            1: 'первый', 2: 'второй', 3: 'третий', 4: 'четвёртый', 5: 'пятый',
            6: 'шестой', 7: 'седьмой', 8: 'восьмой', 9: 'девятый', 10: 'десятый',
            11: 'одиннадцатый', 12: 'двенадцатый', 13: 'тринадцатый', 14: 'четырнадцатый',
            15: 'пятнадцатый', 16: 'шестнадцатый', 17: 'семнадцатый', 18: 'восемнадцатый',
            19: 'девятнадцатый', 20: 'двадцатый', 21: 'двадцать первый'
        }
        return ordinals.get(n, cls.number_to_words_ru(n))

    
    @classmethod
    def _normalize_english(cls, text: str) -> str:
        """Нормализация английского текста"""
        result = text
        
        # 1. Замена аббревиатур
        for abbr, full in cls.EN_ABBREVIATIONS.items():
            result = re.sub(r'\b' + re.escape(abbr) + r'\b', full, result, flags=re.IGNORECASE)
        
        # 2. Даты в формате MM/DD/YYYY или DD/MM/YYYY
        def replace_date(m):
            parts = [int(m.group(1)), int(m.group(2)), int(m.group(3))]
            # Предполагаем MM/DD/YYYY для английского
            if parts[0] <= 12:
                month, day, year = parts
            else:
                day, month, year = parts
            
            month_word = cls.EN_MONTHS.get(month, '')
            day_ordinal = cls._ordinal_en(day)
            year_word = cls.year_to_words_en(year)
            return f"{month_word} {day_ordinal}, {year_word}"
        
        result = re.sub(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', replace_date, result)
        
        # 3. Годы
        def replace_year(m):
            year = int(m.group(1))
            if 1800 <= year <= 2100:
                return cls.year_to_words_en(year)
            return m.group(0)
        
        result = re.sub(r'\b(\d{4})\b', replace_year, result)
        
        # 4. Века
        def replace_century(m):
            roman = m.group(1).upper()
            if roman in cls.ROMAN_NUMERALS:
                num = cls.ROMAN_NUMERALS[roman]
                ordinal = cls._ordinal_en(num)
                return f"the {ordinal} century"
            return m.group(0)
        
        result = re.sub(r'\b([IVXLC]+)\s*century\b', replace_century, result, flags=re.IGNORECASE)
        
        # 5. Числа
        def replace_number(m):
            num = int(m.group(0))
            if num > 10000000:
                return m.group(0)
            return cls.number_to_words_en(num)
        
        result = re.sub(r'\b\d{1,7}\b', replace_number, result)
        
        # 6. Проценты
        result = re.sub(r'(\d+)%', lambda m: cls.number_to_words_en(int(m.group(1))) + ' percent', result)
        
        # 7. Специальные символы
        result = result.replace('&', ' and ')
        result = result.replace('#', 'number ')
        result = result.replace('$', ' dollars ')
        result = result.replace('€', ' euros ')
        result = result.replace('£', ' pounds ')
        
        # 8. Убираем лишние пробелы
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()
        
        return result
    
    @classmethod
    def _ordinal_en(cls, n: int) -> str:
        """Порядковое числительное (английский)"""
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
            19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first'
        }
        if n in ordinals:
            return ordinals[n]
        
        # Для больших чисел
        word = cls.number_to_words_en(n)
        if word.endswith('y'):
            return word[:-1] + 'ieth'
        elif word.endswith('one'):
            return word[:-3] + 'first'
        elif word.endswith('two'):
            return word[:-3] + 'second'
        elif word.endswith('three'):
            return word[:-5] + 'third'
        else:
            return word + 'th'


# Быстрый доступ
def normalize_text(text: str, language: str = 'ru') -> str:
    """Нормализация текста для TTS"""
    return TextNormalizer.normalize_for_tts(text, language)


# Тест
if __name__ == "__main__":
    # Русский
    test_ru = """
    В 1942 году Германия начала наступление. 
    31.01.1943 немецкая армия капитулировала.
    Погибло около 2 млн человек.
    СССР потерял 27 млн граждан.
    Битва длилась 200 дней.
    XIX век был временем перемен.
    """
    
    print("=== РУССКИЙ ===")
    print(normalize_text(test_ru, 'ru'))
    
    # Английский
    test_en = """
    In 1942, Germany launched an offensive.
    On 01/31/1943, the German army surrendered.
    About 2 million people died.
    The USSR lost 27 million citizens.
    The battle lasted 200 days.
    The XIX century was a time of change.
    """
    
    print("\n=== ENGLISH ===")
    print(normalize_text(test_en, 'en'))
