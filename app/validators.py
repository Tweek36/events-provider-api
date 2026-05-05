import re
from datetime import datetime


def validate_date_format(v: str) -> str:
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, v):
        raise ValueError(f"Неверный формат даты: '{v}'. Ожидается YYYY-MM-DD.")
    
    try:
        datetime.strptime(v, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Невалидная дата: '{v}'.")
    
    return v

def validate_seat_pattern(v: str) -> str:
    pattern = r'^[A-Z]\d+$'
    if not re.match(pattern, v):
        raise ValueError(f"Неверный формат паттерна мест: '{v}'. Ожидается буква и цифра.")
    return v

def validate_seats_pattern(v: str) -> str:
    pattern = r'^[A-Z]\d+-\d+(,[A-Z]\d+-\d+)*$'
    if not re.match(pattern, v):
        raise ValueError(f"Неверный формат схемы рассадки: '{v}'. Ожидается формат 'A1-10,B1-20' и т.д.")
    return v