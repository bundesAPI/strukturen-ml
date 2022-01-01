import re

import spacy

from models import Organisation, Person


class OrgChartEntryParser:
    def __init__(self):
        self.model = spacy.load("model-last/")

    def parse(self, text):
        nlp = self.model(text)
        return nlp, nlp.to_json()


    def clean_str(self, str_):
        str_ = str_.replace("\n", " ")
        str_ = re.sub(' +', ' ', str_)
        return str_.strip()

    def parse_to_entities(self, nlp):
        entities = []
        current_org_entity = Organisation()
        person = None
        for entity in nlp.ents:
            if entity.label_ == "NAME":
                if not current_org_entity.name:
                    current_org_entity.name = self.clean_str(entity.text)
                else:
                    if person:
                        current_org_entity.people.append(person)
                        person = None
                    entities.append(current_org_entity)
                    current_org_entity = Organisation()
                    current_org_entity.name = self.clean_str(entity.text)

            if entity.label_ == "SHORT_NAME":
                if not current_org_entity.shortName:
                    current_org_entity.shortName = self.clean_str(entity.text)
                else:
                    if person:
                        current_org_entity.people.append(person)
                        person = None
                    entities.append(current_org_entity)
                    current_org_entity = Organisation()
                    current_org_entity.shortName = self.clean_str(entity.text)
            if entity.label_ == "DIAL_CODE":
                current_org_entity.dialCodes.append(self.clean_str(entity.text))

            if entity.label_ == "PERSON":
                if not person:
                    person = Person(name=self.clean_str(entity.text))
                else:
                    if person.name:
                        current_org_entity.people.append(person)
                        person = Person(name=self.clean_str(entity.text))
                    else:
                        person.name = self.clean_str(entity.text)

            if entity.label_ == "POSITION":
                if not person:
                    person = Person(position=self.clean_str(entity.text))
                else:
                    if person.position:
                        current_org_entity.people.append(person)
                        person = Person(position=self.clean_str(entity.text))
                    else:
                        person.position = self.clean_str(entity.text)


        if person is not None:
            current_org_entity.people.append(person)
        entities.append(current_org_entity)
        return entities

