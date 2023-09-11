import faker
import random

from faker.providers import BaseProvider

import connection
import models

class PhoneUAProvider(BaseProvider):
    def phone(self) -> str:
        code = random.choice(models.PhoneFieldUA.phone_codes)
        count = (8 - len(code))
        phone = "80" + code + f"{random.randrange(1, 10**count - 1):0{count}}"
        return phone

    def mobile_phone(self) -> str:
        code = random.choice(models.PhoneFieldUA.mobile_codes)
        count = (8 - len(code))
        phone = "80" + code + f"{random.randrange(1, 10**count - 1):0{count}}"
        return phone


MAX_SEEDS = 10

def seed(max_contacts = MAX_SEEDS):
    # connection.connect()
    _faker = faker.Faker()
    _faker.add_provider(PhoneUAProvider)
    for i in range(max_contacts):
        name = _faker.first_name() + " " + _faker.last_name()
        methods = []
        priority = random.randint(0, 1)
        if priority:
            method = models.SMS(value = _faker.mobile_phone())
            methods.append(method)
            method = models.Email(value = _faker.email())
            methods.append(method)
        else:
            method = models.Email(value = _faker.email())
            methods.append(method)
            method = models.SMS(value = _faker.mobile_phone())
            methods.append(method)
        method = models.Voice(value = _faker.phone())
        methods.append(method)

        contact = models.Contact(name = name, methods = methods, processed = None)
        contact.save()


if __name__ == "__main__":
    seed(MAX_SEEDS)