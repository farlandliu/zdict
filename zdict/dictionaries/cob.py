import itertools
import json
import re

from bs4 import BeautifulSoup

from zdict.dictionary import DictBase
from zdict.exceptions import NotFoundError
from zdict.models import Record


class CobDict(DictBase):

    API = 'https://www.collinsdictionary.com/dictionary/english/{word}'

    @property
    def provider(self):
        return 'cob1'

    @property
    def title(self):
        return 'Collins Cobuild Ads Dictionary - simple version'

    def _get_url(self, word) -> str:
        return self.API.format(word=word)

    def show(self, record: Record):
        content = json.loads(record.content)

        # print word
        self.color.print(content['word'], 'yellow')

        # print pronounce
        for k in content.get('pronounce', []):
            self.color.print(k, end='')
        print() # = blank line

        # print explain
        main_explanations = content.get('explain', [])
        if self.args.verbose:
            main_explanations.extend(content.get('verbose', []))

        for speech in main_explanations:
            self.color.print(speech)
            
        print()

    def query(self, word: str):
        webpage = self._get_raw(word)
        data_root = BeautifulSoup(webpage, "html.parser")
        data_root = data_root.find('div', class_='dictionary Cob_Adv_Brit')
        # sometimes there are two dict sections, if there are two,
        # we use the 2nd one
        dicts = data_root.find_all('div', 'dictentry')
        if len(dicts) >1 :
            data = dicts[1]
        else:
            data = dicts[0]

        content = {}

        # handle record.word
        try:
            content['word'] = data.find('span', class_='orth').text
        except AttributeError:
            raise NotFoundError(word)

        # handle pronounce
        pronu_value = data.find('span', class_='mini_h2')
        if pronu_value:
            content['pronounce'] = []
            content['pronounce'].append(pronu_value.text.replace('\n', ''))

        # handle sound
        # skip
        # Handle explain
        main_explanations = data.find(
            class_='content definitions cobuild br'
        )

        content['explain'] = []
        content['explain'].append(main_explanations.text.replace('\n\n', '\n'))
        
        record = Record(
            word=word,
            content=json.dumps(content),
            source=self.provider,
        )
        return record
