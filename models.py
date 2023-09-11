import csv

from mongoengine import EmbeddedDocument, Document, CASCADE
from mongoengine.fields import  DateTimeField,\
                                EmbeddedDocumentField,\
                                ListField,\
                                StringField,\
                                ReferenceField,\
                                BooleanField,\
                                EmailField,\
                                GenericEmbeddedDocumentField
from pydantic import BaseModel#, Field



class PhoneFieldUA(StringField):
    mobile_codes = ["50", "63", "66", "67", "68", "73", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"]
    phone_codes = []
    with open("data/phone_codes_ua.csv") as fd:
        reader = csv.reader(fd, delimiter=',')
        for row in reader:
            codes = row[2].split('"')
            code = codes[0]
            try:
                int(code)
            except ValueError:
                continue
            phone_codes.append(code)
    
    error_msg = "Invalid phone number: %s"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    "8044446804"
    def validate(self, value):
        super().validate(value)
        if len(value) != 10:
            self.error(self.error_msg % value)
        if      value[2:8] not in self.phone_codes  \
            and value[2:7] not in self.phone_codes  \
            and value[2:6] not in self.phone_codes  \
            and value[2:5] not in self.phone_codes  \
            and value[2:4] not in self.phone_codes  \
            and value[2:4] not in self.mobile_codes \
        :
            self.error(self.error_msg % value)
        return
    


class Message(BaseModel):
    contact_id: str
    message: str



class Email(EmbeddedDocument):
    value       = EmailField()
    processed   = DateTimeField(null = True, dedault = None)
    result      = BooleanField(null = False, dedault = False)



class Voice(EmbeddedDocument):
    value       = PhoneFieldUA()
    processed   = DateTimeField(null = True, dedault = None)
    result  = BooleanField(null = False, dedault = False)



class SMS(EmbeddedDocument):
    value       = PhoneFieldUA()
    processed   = DateTimeField(null = True, dedault = None)
    result      = BooleanField(null = False, dedault = False)



class Contact(Document):
    name        = StringField(unique=True, required=True)
    processed   = DateTimeField(null = True, dedault = None)
    result      = BooleanField(null = False, dedault = False)
    methods     = ListField(GenericEmbeddedDocumentField())

    meta = {"collection": "contacts"}



if __name__ == "__main__":
    field = PhoneFieldUA()
    field.validate("8044446804")