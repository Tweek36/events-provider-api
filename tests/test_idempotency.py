import uuid

from app.repositories.idempotency import IdempotencyRepository


class TestIdempotencyRepository:
    """Тесты для IdempotencyRepository."""

    def test_compute_request_hash_with_uuid(self):
        """Тест вычисления хэша запроса с UUID объектами."""
        # Arrange
        event_id = uuid.UUID("1340d126-a670-44a4-b595-6f1daece9679")
        request_data = {
            "event_id": event_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "seat": "A1",
        }

        # Act
        hash_result = IdempotencyRepository.compute_request_hash(request_data)

        # Assert
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 хэш в hex формате

    def test_compute_request_hash_consistency(self):
        """Тест, что одинаковые данные дают одинаковый хэш."""
        # Arrange
        event_id = uuid.UUID("1340d126-a670-44a4-b595-6f1daece9679")
        request_data_1 = {
            "event_id": event_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "seat": "A1",
        }
        request_data_2 = {
            "event_id": event_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "seat": "A1",
        }

        # Act
        hash_1 = IdempotencyRepository.compute_request_hash(request_data_1)
        hash_2 = IdempotencyRepository.compute_request_hash(request_data_2)

        # Assert
        assert hash_1 == hash_2

    def test_compute_request_hash_different_data(self):
        """Тест, что разные данные дают разные хэши."""
        # Arrange
        event_id = uuid.UUID("1340d126-a670-44a4-b595-6f1daece9679")
        request_data_1 = {
            "event_id": event_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "seat": "A1",
        }
        request_data_2 = {
            "event_id": event_id,
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "seat": "A2",
        }

        # Act
        hash_1 = IdempotencyRepository.compute_request_hash(request_data_1)
        hash_2 = IdempotencyRepository.compute_request_hash(request_data_2)

        # Assert
        assert hash_1 != hash_2

    def test_compute_request_hash_key_order_independence(self):
        """Тест, что порядок ключей не влияет на хэш."""
        # Arrange
        event_id = uuid.UUID("1340d126-a670-44a4-b595-6f1daece9679")
        request_data_1 = {
            "event_id": event_id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "seat": "A1",
        }
        # Другой порядок ключей
        request_data_2 = {
            "seat": "A1",
            "email": "john.doe@example.com",
            "last_name": "Doe",
            "first_name": "John",
            "event_id": event_id,
        }

        # Act
        hash_1 = IdempotencyRepository.compute_request_hash(request_data_1)
        hash_2 = IdempotencyRepository.compute_request_hash(request_data_2)

        # Assert
        assert hash_1 == hash_2
