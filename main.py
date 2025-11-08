#!/usr/bin/env python3
"""
Инструмент визуализации графа зависимостей пакетов
Этап 1: Минимальный прототип с конфигурацией через командную строку
"""

import argparse
import sys


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


def main():
    """Главная функция"""
    try:
        # Парсим аргументы
        args = parse_arguments()

        # Проверяем корректность
        errors = validate_arguments(args)
        if errors:
            print(" Ошибки в параметрах:")
            for error in errors:
                print(f"   - {error}")
            print("\nИспользуйте python main.py --help для справки")
            sys.exit(1)

        # Выводим конфигурацию (требование этапа 1)
        print_configuration(args)

        print("\n" + "=" * 40)
        print(" Этап 1 завершен! Минимальный прототип готов.")
        print("Следующий шаг: реализация сбора данных о зависимостях.")

    except KeyboardInterrupt:
        print("\n\n Программа прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()