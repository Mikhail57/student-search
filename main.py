import vk_api
from VkScholarSearch import VkScholarSearch


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """
    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


def main():
    login, password = 'mikhail@email.ru', 'passw0rd'
    vk_session = vk_api.VkApi(
        login, password,
        # функция для обработки двухфакторной аутентификации
        auth_handler=auth_handler
    )

    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    searcher = VkScholarSearch(vk_session.get_api())

    searcher.search_scholars(['иркутск'])
    searcher.save_to_csv('lol.csv')


if __name__ == '__main__':
    main()
