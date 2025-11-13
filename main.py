#!/usr/bin/env python3

import argparse
import sys
import requests
import gzip
import re


def parse_arguments():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description='Инструмент визуализации графа зависимостей пакетов Ubuntu',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Обязательные параметры
    parser.add_argument(
        '--package', '-p',
        required=True,
        help='Имя анализируемого пакета (например: python3, firefox)'
    )

    parser.add_argument(
        '--repository', '-r',
        required=True,
        help='URL репозитория Ubuntu или путь к файлу тестового репозитория'
    )

    # Опциональные параметры
    parser.add_argument(
        '--test-mode', '-t',
        action='store_true',
        help='Режим работы с тестового репозитория'
    )

    parser.add_argument(
        '--version',
        help='Версия пакета (например: 3.10.6)'
    )

    parser.add_argument(
        '--ascii-tree', '-a',
        action='store_true',
        help='Вывод зависимостей в формате ASCII-дерева'
    )

    parser.add_argument(
        '--filter', '-f',
        help='Подстрока для фильтрации пакетов (исключает пакеты, содержащие подстроку)'
    )

    # НОВЫЙ АРГУМЕНТ ДЛЯ ЭТАПА 3
    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        help='Максимальная глубина анализа зависимостей'
    )

    return parser.parse_args()

def validate_arguments(args):
    """Проверяет корректность аргументов"""
    errors = []

    # Проверка имени пакета
    if not args.package.strip():
        errors.append("Имя пакета не может быть пустым")

    # Проверка репозитория
    if not args.repository.strip():
        errors.append("URL репозитория не может быть пустым")

    # Проверка версии (если указана)
    if args.version and not args.version.strip():
        errors.append("Версия пакета не может быть пустой строкой")

    # Проверка фильтра (если указан)
    if args.filter and not args.filter.strip():
        errors.append("Фильтр не может быть пустой строкой")

    return errors


def print_configuration(args):
    """Выводит конфигурацию в формате ключ-значение (требование этапа 1)"""
    print(" Конфигурация приложения:")
    print("=" * 40)

    config_items = [
        ("Анализируемый пакет", args.package),
        ("Репозиторий", args.repository),
        ("Режим тестирования", "ВКЛ" if args.test_mode else "ВЫКЛ"),
        ("Версия пакета", args.version if args.version else "не указана"),
        ("Режим ASCII-дерева", "ВКЛ" if args.ascii_tree else "ВЫКЛ"),
        ("Фильтр пакетов", args.filter if args.filter else "не указан")
    ]

    for key, value in config_items:
        print(f"  {key:<25} : {value}")


def get_package_dependencies_simple(package_name, repository_url):
    """Простая функция для получения зависимостей (без классов)"""
    try:
        # Формируем URL к файлу пакетов
        packages_url = f"{repository_url}/dists/jammy/main/binary-amd64/Packages.gz"

        # Скачиваем файл
        response = requests.get(packages_url, timeout=30)
        response.raise_for_status()

        # Распаковываем
        packages_content = gzip.decompress(response.content).decode('utf-8')

        # Ищем нужный пакет в содержимом
        package_block = find_package_block(packages_content, package_name)
        if not package_block:
            return []

        # Извлекаем зависимости
        depends_line = extract_depends_line(package_block)
        if not depends_line:
            return []

        # Парсим зависимости
        return parse_dependencies_simple(depends_line)

    except Exception as e:
        print(f"Ошибка при получении зависимостей: {e}")
        return []


def find_package_block(content, package_name):
    """Ищет блок с описанием пакета в содержимом файла"""
    lines = content.split('\n')
    in_target_package = False
    package_block = []

    for line in lines:
        if line.startswith('Package: ') and package_name in line:
            in_target_package = True
            package_block.append(line)
        elif line.startswith('Package: ') and in_target_package:
            # Нашли следующий пакет - заканчиваем
            break
        elif in_target_package:
            package_block.append(line)

    return '\n'.join(package_block) if package_block else None


def extract_depends_line(package_block):
    """Извлекает строку с зависимостями из блока пакета"""
    for line in package_block.split('\n'):
        if line.startswith('Depends: '):
            return line.replace('Depends: ', '')
    return None


def parse_dependencies_simple(depends_string):
    """Парсит строку зависимостей"""
    if not depends_string:
        return []

    dependencies = []

    for dep in depends_string.split(','):
        dep = dep.strip()
        # Убираем версии: "libc6 (>= 2.34)" → "libc6"
        dep = re.sub(r'\([^)]*\)', '', dep).strip()
        # Убираем альтернативы: "a | b" → "a"
        dep = dep.split('|')[0].strip()

        if dep:
            dependencies.append(dep)

    return dependencies


def download_and_parse_all_packages(repository_url):
    """Скачивает и парсит ВЕСЬ файл пакетов один раз"""
    try:
        # Формируем URL к файлу пакетов
        packages_url = f"{repository_url}/dists/jammy/main/binary-amd64/Packages.gz"

        # Скачиваем файл
        response = requests.get(packages_url, timeout=30)
        response.raise_for_status()

        # Распаковываем
        packages_content = gzip.decompress(response.content).decode('utf-8')

        # Парсим ВСЕ пакеты
        all_packages = {}
        current_package = None
        current_deps = []

        for line in packages_content.split('\n'):
            if line.startswith('Package: '):
                # Сохраняем предыдущий пакет
                if current_package:
                    all_packages[current_package] = current_deps

                # Начинаем новый пакет
                current_package = line.replace('Package: ', '').strip()
                current_deps = []

            elif line.startswith('Depends: ') and current_package:
                # Парсим зависимости для текущего пакета
                depends_str = line.replace('Depends: ', '')
                current_deps = parse_dependencies_simple(depends_str)

        # Не забываем последний пакет
        if current_package:
            all_packages[current_package] = current_deps

        return all_packages

    except Exception as e:
        print(f"Ошибка при загрузке пакетов: {e}")
        return {}

def build_dependency_graph(start_package, get_deps_func, max_depth=None, package_filter=None):
    """Строит полный граф зависимостей с помощью DFS"""
    graph = {}
    visited = set()
    cycles_detected = []

    def should_include_package(package_name):
        """Проверяет, нужно ли включать пакет согласно фильтру"""
        if package_filter and package_filter in package_name.lower():
            return False
        return True

    def dfs(package_name, current_depth=0, path=None):
        """Рекурсивная функция DFS для обхода зависимостей"""
        if path is None:
            path = []

        # Проверяем максимальную глубину
        if max_depth and current_depth >= max_depth:
            return

        # Проверяем фильтр
        if not should_include_package(package_name):
            return

        # Обнаружение циклических зависимостей
        if package_name in path:
            cycle = path[path.index(package_name):] + [package_name]
            cycles_detected.append(cycle)
            return

        # Защита от повторного посещения (оптимизация)
        if package_name in visited:
            return

        visited.add(package_name)
        path.append(package_name)

        # Получаем зависимости пакета (используем переданную функцию)
        dependencies = get_deps_func(package_name)

        # Фильтруем зависимости
        filtered_deps = [dep for dep in dependencies if should_include_package(dep)]

        # Добавляем в граф
        graph[package_name] = filtered_deps

        # Рекурсивно обрабатываем зависимости
        for dep in filtered_deps:
            dfs(dep, current_depth + 1, path.copy())

        path.pop()

    # Запускаем DFS из стартового пакета
    dfs(start_package)

    return graph, cycles_detected


def print_dependency_graph(graph, cycles_detected):
    """Выводит граф в читаемом формате"""
    print("Граф зависимостей:")
    for package, deps in graph.items():
        if deps:
            print(f"  {package} -> {', '.join(deps)}")
        else:
            print(f"  {package} -> (нет зависимостей)")

    if cycles_detected:
        print("\nОбнаружены циклические зависимости:")
        for cycle in cycles_detected:
            print(f"  {' -> '.join(cycle)}")


def get_graph_statistics(graph):
    """Возвращает статистику графа"""
    total_packages = len(graph)
    total_dependencies = sum(len(deps) for deps in graph.values())

    return {
        'total_packages': total_packages,
        'total_dependencies': total_dependencies,
        'packages_without_deps': len([deps for deps in graph.values() if not deps])
    }

def main():
    try:
        args = parse_arguments()
        errors = validate_arguments(args)
        if errors:
            print(" Ошибки в параметрах:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
        print_configuration(args)

        print("\n" + "=" * 40)

        if args.test_mode:
            # Для тестового режима - заглушка
            print("Тестовый режим - используем заглушку")
            dependencies = ["python3.10", "libpython3-stdlib", "python3-minimal"]
        else:
            # Получаем зависимости
            print(f" Получаем зависимости пакета {args.package}...")
            dependencies = get_package_dependencies_simple(args.package, args.repository)

        # Выводим результат (ЭТАП 2)
        print(f" Прямые зависимости пакета {args.package}:")
        for dep in dependencies:
            print(f"   - {dep}")

        print("\n Данные о зависимостях получены.")

        # ========== НАЧАЛО ЭТАПА 3 ==========
        print("\n" + "=" * 40)
        print("Этап 3: Построение графа зависимостей")

        # Создаем функцию для получения зависимостей (совместимую с этапом 2)
        # Кеш для реального режима (глобальная переменная в main)
        packages_cache = {}

        def get_dependencies_func(package_name):
            if args.test_mode:
                # Тестовые данные для демонстрации
                test_data = {
                    'python3': ['python3.10', 'libpython3-stdlib', 'python3-minimal'],
                    'python3.10': ['libc6', 'libssl3', 'zlib1g'],
                    'libc6': ['libgcc1'],
                    'libssl3': ['libc6'],
                    'zlib1g': ['libc6'],
                    'libpython3-stdlib': ['python3.10'],
                    'python3-minimal': ['python3.10'],
                    'libgcc1': []
                }
                return test_data.get(package_name, [])
            else:
                # РЕАЛЬНЫЙ РЕЖИМ С КЕШИРОВАНИЕМ
                # Если пакет уже в кеше - возвращаем из кеша
                if package_name in packages_cache:
                    return packages_cache[package_name]

                # Если кеш пустой - скачиваем и парсим весь файл один раз
                if not packages_cache:
                    print("Скачиваем файл пакетов... (это займет время)")
                    all_packages = download_and_parse_all_packages(args.repository)
                    packages_cache.update(all_packages)
                    print(f"Загружено {len(packages_cache)} пакетов")

                # Возвращаем зависимости из кеша (или пустой список если пакет не найден)
                return packages_cache.get(package_name, [])

        # Строим граф
        print("Строим граф зависимостей (DFS)...")
        graph, cycles = build_dependency_graph(
            start_package=args.package,
            get_deps_func=get_dependencies_func,
            max_depth=args.max_depth,
            package_filter=args.filter
        )

        # Выводим результаты
        print_dependency_graph(graph, cycles)

        # Статистика
        stats = get_graph_statistics(graph)
        print(f"\nСтатистика графа:")
        print(f"  Всего пакетов: {stats['total_packages']}")
        print(f"  Всего зависимостей: {stats['total_dependencies']}")
        print(f"  Пакетов без зависимостей: {stats['packages_without_deps']}")
        print(f"  Обнаружено циклов: {len(cycles)}")

        print("\nЭтап 3 завершен. Граф зависимостей построен.")
        # ========== КОНЕЦ ЭТАПА 3 ==========

    except KeyboardInterrupt:
        print("\n\n Программа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()