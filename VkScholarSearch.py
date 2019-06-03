import vk_api
import pandas as pd
from pandas.io.json import json_normalize
import json

from vk_api.execute import VkFunction


def get_first_item_with_field(lst: list, field: str):
    for item in lst:
        if field in item:
            return item
    raise Exception


def reduce_fields(item: dict, fields: list) -> dict:
    result = {}
    for field in fields:
        result[field] = item[field]
    return result


class VkScholarSearch:

    def __init__(self, vk: vk_api.vk_api.VkApiMethod) -> None:
        super().__init__()
        self._vk = vk

        self._tools = vk_api.VkTools(vk)

        self._country_id = 1
        self.age_from = 1
        self.age_to = 1
        self._cities_id = []
        self._found_scholars = []

    def search_scholars(self, cities: list, age_from=10, age_to=18):
        self._fill_cities(cities)
        self._get_all_scholars(age_from, age_to)
        print(f'Всего найдено: {len(self._found_scholars)}')
        self._filter_closed_scholars()
        print(f'После фильтрации на закрытые профили и возможность писать сообщения: {len(self._found_scholars)}')
        self._get_scholars_groups()

    def save_to_csv(self, filename):
        df = json_normalize(self._found_scholars)
        df.set_index('id', inplace=True)
        df.to_csv(filename)

    def _fill_cities(self, cities: list):
        self._cities_id.clear()
        for city in cities:
            response = self._vk.database.getCities(
                country_id=self._country_id,
                q=city
            )
            if response['count'] < 1:
                raise Exception('Не найден город ' + city)
            self._cities_id.append(response['items'][0]['id'])

    def _get_all_scholars(self, age_from: int, age_to: int):
        for city in self._cities_id:
            params = {
                'city': city,
                'age_from': age_from,
                'age_to': age_to,
                'fields': 'sex,bdate,city,contacts,education,schools,last_seen,can_write_private_message'
            }
            response = self._tools.get_all('users.search', 1000, params)
            items = response['items']
            print('Получены все люди из города ' + get_first_item_with_field(items, 'city')['city']['title'])
            self._found_scholars.extend(items)

    def _filter_closed_scholars(self):
        self._found_scholars = list(filter(
            lambda p: not p['is_closed'] and p['can_write_private_message'] == 1,
            self._found_scholars
        ))

    def _get_scholars_groups(self, max_count=25):
        result = []
        print('Получение списка групп для каждого пользователя...')
        users = list(map(lambda p: p['id'], self._found_scholars))
        total_count = len(users)
        for i in range(0, total_count, max_count):
            user_ids = users[i:i + max_count]
            result.extend(vk_get_groups(self._vk, user_ids=user_ids, per_user_count=1000))
            print(f'Получено {min(i + max_count, total_count)}/{total_count}...')
        print('Список групп получен')
        with open('kek.json', 'w') as f:
            json.dump(result, f)

        def add_groups(z):
            user, groups = z
            assert user['id'] == groups['user_id']
            user = user.copy()
            items_ = groups['groups']['items']
            if isinstance(items_, list):
                user['groups'] = list(map(lambda g: reduce_fields(g, ['id', 'name']), items_))
            else:
                user['groups'] = []

            return user

        self._found_scholars = list(map(add_groups, zip(self._found_scholars, result)))
        return self._found_scholars


vk_get_groups = VkFunction('''
var users = %(user_ids)s;
var result = [];
var i = 0;
while(i < users.length) {
  var userId = users[i];
  var params = {'user_id': userId, 'extended': 1, 'count': %(per_user_count)s};
  var res = API.groups.get(params);
  var item = {'user_id': userId, 'groups': res};
  result.push(item);
  i = i + 1;
}
return result;
''', args=['user_ids', 'per_user_count'], clean_args=['per_user_count'])
