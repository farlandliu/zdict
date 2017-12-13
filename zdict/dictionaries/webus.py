import itertools
import json
import re

from bs4 import BeautifulSoup

from zdict.dictionary import DictBase
from zdict.exceptions import NotFoundError
from zdict.models import Record


class WebUSDict(DictBase):

    API = 'https://www.collinsdictionary.com/dictionary/english/{word}'

    @property
    def provider(self):
        return 'webus'

    @property
    def title(self):
        return 'Webster US Dictionary'

    def _get_url(self, word) -> str:
        return self.API.format(word=word)

    def show(self, record: Record):
        content = json.loads(record.content)

        # print word ,pronounce
        # import pdb;pdb.set_trace()
        self.color.print(content['word']+ content['pronounce'], 'red')

        # print explain
        main_explanations = content.get('explain', [])
        if self.args.verbose:
            main_explanations.extend(content.get('verbose', []))

        # explain = ['word forms',[sense1, sense2]]
        # sense = [grammar, example1,examle2]
        print(main_explanations[0])

        for speech in main_explanations[1:]:
            # print word forms
            self.color.print(speech[0],'blue')
            # print sense items
            for meaning in speech[1:]:

                for sentence in meaning[1:]:
                    if sentence:
                        print(' ' * 2, end='')
                        for i, s in enumerate(sentence.split('*')):
                            self.color.print(
                                s,

                                end=''
                            )
                    print()
            print()



    def query(self, word: str):
        webpage = self._get_raw(word)
        data_root = BeautifulSoup(webpage, "html.parser")
        data = data_root.find('div', class_='dictionary Large_US_Webster')
        content = {}

        # handle record.word
        try:
            content['word'] = data.find('span', class_='orth').text
        except AttributeError:
            raise NotFoundError(word)

        # handle pronounce
        pronu_value = data.find('span', class_='mini_h2')
        if pronu_value:
            content['pronounce'] = pronu_value.text.replace('\n','')

        # handle sound
        # skip
        # Handle explain
        definations = data.find(
            class_='content definitions american'
        )
        # explain = ['word forms',[sense1, sense2]]
        # sense = [grammar, example1,examle2]
        content['explain'] = []

        # handle word forms = content['explain'][0]
        forms = definations.find('span', class_='form inflected_forms type-infl')
        forms_text = forms.text if forms else ' '
        content['explain'].append(forms_text.replace('\n',''))

        #handle defination items
        def_items = definations.find_all('div', 'hom')
        for item in def_items:
            """
            structure:
            [num+ grammar + defs],[ex1],[ex2]

            """
            sense_item = []
            # sen_num = ''
            extra = item.find('span',class_='xr')
            if not extra:
                sen_num = item.find('span', class_='span sensenum')
                sen_num = sen_num.text if sen_num else ''
                sen_grm = item.find('span', class_='gramGrp')
                sen_grm = sen_grm.text if sen_grm else ' '
                sen_def_list = item.find_all('div', class_='def')
                sen_defs = ''   # store the definitaion
                for sen_def in sen_def_list:
                    sen_defs += sen_def.text.replace('\n\n', '\n')
                sense_item.append(sen_num + sen_grm + '\n' + sen_defs)
                sen_examples = []
                examples = item.find_all('div', class_='cit type-example')
                if examples:
                    for ex in examples:
                        sen_examples.append(ex.text)
                    sense_item.append(sen_examples)
            else:
                sen_num = item.find('span', class_='span sensenum')
                sen_num = sen_num.text if sen_num else ''
                sense_item.append(sen_num + extra.text)
            content['explain'].append(sense_item)

        # todo: copyright for dictionary

        record = Record(
            word=word,
            content=json.dumps(content),
            source=self.provider,
        )
        return record
