from babel.plural import PluralRule
import json
from string import Template
import glob
import os
from datetime import datetime
from babel.dates import format_datetime



class Translator():
    def __init__(self, translations_folder, lang):
        self.data = {}
        if lang is None:
            self.locale = 'en'
        else:
            self.locale = lang
        self.plural_rule = PluralRule({'one': 'n is 1'})

        files = glob.glob(os.path.join(translations_folder, f'{self.locale}.json'))
        for fil in files:
            # get the name of the file without extension, will be used as locale name
            loc = os.path.splitext(os.path.basename(fil))[0]
            with open(fil, 'r', encoding='utf8') as f:
                self.data[loc] = json.load(f)


    def set_locale(self, loc):
        if loc in self.data:
            self.locale = loc
        else:
            print('Invalid locale')

    def get_locale(self):
        return self.locale

    def set_plural_rule(self, rule):
        try:
            self.plural_rule = PluralRule(rule)
        except Exception:
            print('Invalid plural rule')

    def get_plural_rule(self):
        return self.plural_rule

    def translate(self, key, **kwargs):
        # return the key instead of translation text if locale is not supported
        if self.locale not in self.data:
            return key

        text = self.data[self.locale].get(key, key)
        # type dict represents key with plural form
        if type(text) == dict:
            count = kwargs.get('count', 1)
            # parse count to int
            try:
                count = int(count)
            except Exception:
                print('Invalid count')
                return key
            text = text.get(self.plural_rule(count), key)
        return Template(text).safe_substitute(**kwargs)


def parse_datetime(dt, input_format='%Y-%m-%d', output_format='MMMM dd, yyyy', output_locale='en'):
    dt = datetime.strptime(dt, input_format)
    return format_datetime(dt, format=output_format, locale=output_locale)