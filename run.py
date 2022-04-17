import pandas as pd
from fuzzywuzzy import process


def load_file(filename):
    """Открывает файл и преобразует в pandas DataFrame с индексом
    по первой колонке городов. Каждый лист экселя идет в отдельный
    DataFrame.

    Принимает:
    filename -- путь к эксель файлу
    """

    print('Loading file...')
    dfs = dict()
    dfs['Miles'] = pd.read_excel(filename, sheet_name='Miles', engine='openpyxl',  index_col=' ')
    dfs['Miles'].index.name = 'City'
    dfs['Population'] = pd.read_excel(filename, sheet_name='Population', engine='openpyxl',  index_col='City')
    print("File opened")
    return dfs


def search_paths(start, df):
    """Ищет пути удовлетворяющие условию задачи используя обход дерева.

    Принимает:
    start -- начальный город
    df -- DataFrame с матрицей расстояний
    """

    def traverse(visited, df, current_city, day, today_distance, initial_city, path):
        """Реализация рекурсивного обхода дерева.

        Принимает:
        visited -- посещенные города
        df -- DataFrame с матрицей расстояний
        current_city -- текущий город
        day -- текущий день путешествия
        today_distance -- пройденый путь за текущий день
        initial_city -- начальный город
        path -- путь к текущему городу
        """

        cpath = path.copy()  # что бы не влиять на другие ветки
        if day == 7 and current_city == initial_city:  # если наступил седьмой день и мы вернулись то возвращаем путь
            cpath.append(current_city)
            return [cpath]
        elif day < 7 and current_city not in visited:  # если еще путеществуем и город не посещен
            visited.add(current_city)
            cpath.append(current_city)
            result = list()  # аккумулятор результатов
            # проверяем города не дальше предельного расстояния от текущего
            for index, distance in df.loc[(df[current_city] <= 400), current_city].items():
                if distance + today_distance >= 400:  # если сегодня уже не доехать в следующий город
                    # то едем завтра и завтра мы проедем до него distance
                    res = traverse(visited, df, index, day + 1, distance, initial_city, cpath)
                else:  # иначе едем сегодня и увеличиваем дистанцию за сегодня
                    res = traverse(visited, df, index, day, distance + today_distance, initial_city, cpath)
                if res:
                    result.extend(res)  # добавляем полученные пути в аккумулятор если они есть
            return result

    return traverse(set(), df, start, 0, 0, start, [])


def range_paths(df, paths):
    """Ранжировка результатов.

    Принимает:
    df -- DataFrame с населением городов
    paths -- список путей
    """

    result = list()
    for path in paths:
        result.append((calc_path_score(df, path), path))
    result.sort(key=lambda tup: tup[0], reverse=True)
    return result


def calc_path_score(df, path):
    """Скоринг пути.

    Принимает:
    df -- DataFrame с населением городов
    path -- путь
    """
    score = 0
    visited = set()
    for city in path:
        if city not in visited:
            visited.add(city)
            score += df.at[city, 'Population']
    return score


def city_input_loop(df):
    """Ввод города, с предложением варианта ближайшего по
    расстоянию Левенштейна. Что бы можно было не писать страну,
    или исправлять опечатки

    Принимает:
    df -- DataFrame с индексом по городам
    """

    while True:
        user_city = input('Введите название города: ')
        city, rate = process.extractOne(user_city, df.index.values)
        confirm = input(f'Вы имели в виду {city}? (yes\\no): ')
        if confirm == 'yes':
            return city


def test_path(df, path):
    """Вывод информации о путешествии. Такой как количество дней,
    итоговое расстояние и список расстояний переходов между городами.

    Принимает:
    df -- DataFrame с матрицей расстояний
    path -- путь
    """

    result = list()
    total = 0
    today = 0
    days = 0
    prev_city = None
    for city in path:
        if prev_city:
            distance = df.at[city, prev_city]
            result.append(distance)
            total += distance
            if today + distance >= 400:  # сегодня не доедем
                days += 1  # поедем завтро
                today = distance  # проедем завтро до следующего города
            else:  # доедем сегодня
                today += distance  # проедем в итоге за сегодня
        prev_city = city
    return dict(total_miles=total, days_in_a_road=days, distances_list=result)


if __name__ == '__main__':
    dfs = load_file("Funventurer_test task_data.xlsx")
    while True:
        city = city_input_loop(dfs['Population'])
        paths = search_paths(city, dfs['Miles'])
        result = range_paths(dfs['Population'], paths)
        for path in result:
            print(path)
        # расскоментить для дополнительной информации о маршрутах
        # for path in paths:
        #     print('-------------------------')
        #     print(path)
        #     print(test_path(dfs['Miles'], path))
        confirm = input('Еще один запрос? (yes\\no): ')
        if confirm == 'no':
            break
