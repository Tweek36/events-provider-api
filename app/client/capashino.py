from urllib.parse import urljoin

import httpx
import structlog

logger = structlog.get_logger()


class CapashinoClient:
    """Клиент для взаимодействия с Capashino Notification Service."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def send_notification(self, message: str, reference_id: str, idempotency_key: str) -> dict:
        """
        Отправить уведомление через Capashino API.

        Args:
            message: Текст уведомления
            reference_id: Идентификатор связанной сущности (например, ticket_id)
            idempotency_key: Ключ идемпотентности для предотвращения дубликатов

        Returns:
            dict: Ответ от Capashino API

        Raises:
            httpx.HTTPStatusError: При ошибках HTTP
        """
        url = urljoin(self.base_url, "/api/notifications")
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        payload = {
            "message": message,
            "reference_id": reference_id,
            "idempotency_key": idempotency_key,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)

                # 201 - успешное создание
                if response.status_code == 201:
                    logger.info(
                        "capashino_notification_sent",
                        reference_id=reference_id,
                        idempotency_key=idempotency_key,
                    )
                    return response.json()

                # 409 - уведомление с таким idempotency_key уже существует (это OK)
                if response.status_code == 409:
                    logger.info(
                        "capashino_notification_already_exists",
                        reference_id=reference_id,
                        idempotency_key=idempotency_key,
                    )
                    return response.json()

                # Другие ошибки
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as e:
            logger.error(
                "capashino_timeout",
                reference_id=reference_id,
                error_msg=str(e),
            )
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                "capashino_http_error",
                reference_id=reference_id,
                status_code=e.response.status_code,
                error_msg=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "capashino_unexpected_error",
                reference_id=reference_id,
                error_type=type(e).__name__,
                error_msg=str(e),
            )
            raise
