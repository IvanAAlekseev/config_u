# Инструмент визуализации графа зависимостей пакетов

## Этап 1: Минимальный прототип с конфигурацией

CLI-приложение для анализа зависимостей пакетов Ubuntu.

### Использование

```bash
# Базовая команда
python main.py --package python3 --repository http://archive.ubuntu.com/ubuntu/

# С дополнительными параметрами
python main.py --package firefox --repository test_repo.txt --test-mode --ascii-tree --filter debug

# Короткие версии флагов
python main.py -p python3 -r http://archive.ubuntu.com/ubuntu/ -t -a