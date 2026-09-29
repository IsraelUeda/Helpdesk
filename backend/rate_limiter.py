import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """
    Rate limiter baseado em janela deslizante (sliding window) em memória.
    Thread-safe e eficiente para limitar requisições por minuto por cliente/IP.
    """

    def __init__(self, max_requests: int = 25, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def check_rate_limit(self, client_key: str):
        current_time = time.time()
        window_start = current_time - self.window_seconds

        with self.lock:
            # Filtra requisições que caíram fora da janela de 60 segundos
            timestamps = [ts for ts in self.requests[client_key] if ts > window_start]
            self.requests[client_key] = timestamps

            if len(timestamps) >= self.max_requests:
                earliest_ts = timestamps[0]
                retry_after = int(self.window_seconds - (current_time - earliest_ts)) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Limite de criação de tickets excedido: máximo de {self.max_requests} tickets por minuto. Tente novamente em {retry_after} segundos.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            # Registra a nova requisição
            self.requests[client_key].append(current_time)


# Instância global configurada para no máximo 25 criações de tickets por minuto
ticket_creation_limiter = SlidingWindowRateLimiter(max_requests=25, window_seconds=60)


def limit_ticket_creation(request: Request):
    """
    Dependency do FastAPI para aplicar o limite de 25 tickets por minuto por cliente.
    """
    client_ip = request.client.host if request.client else "unknown_client"
    # Considera também cabeçalhos de proxy reverso caso existam (ex: X-Forwarded-For)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    ticket_creation_limiter.check_rate_limit(client_ip)
