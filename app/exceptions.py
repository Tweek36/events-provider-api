class EventNotFound(Exception):
    """Событие не найдено или не опубликовано"""
    pass


class SeatUnavailable(Exception):
    """Место недоступно для бронирования"""
    pass


class SeatAlreadyTaken(Exception):
    """Место уже занято"""
    pass


class RegistrationClosed(Exception):
    """Регистрация закрыта (прошел дедлайн)"""
    pass


class EventAlreadyOccurred(Exception):
    """Событие уже произошло"""
    pass


class TicketNotFound(Exception):
    """Билет не найден"""
    pass


class EventsProviderError(Exception):
    """Ошибка при обращении к внешнему API событий"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Events provider error {status_code}: {detail}")