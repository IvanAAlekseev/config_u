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
        help='Режим работы с тестовым репозиторием'
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
    print("⚙️  Конфигурация приложения:")
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
            print("🔧 Тестовый режим - используем заглушку")
            dependencies = ["python3.10", "libpython3-stdlib", "python3-minimal"]
        else:
            # Получаем зависимости
            print(f" Получаем зависимости пакета {args.package}...")
            dependencies = get_package_dependencies_simple(args.package, args.repository)

        # Выводим результат
        print(f" Прямые зависимости пакета {args.package}:")
        for dep in dependencies:
            print(f"   - {dep}")

        print("\n Данные о зависимостях получены.")

    except KeyboardInterrupt:
        print("\n\n Программа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()