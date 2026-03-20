from faststream.nats import NatsRoute, NatsRouter

from .service import apply_service

router = NatsRouter(
    handlers=[
        NatsRoute(
            apply_service,
            subject="match_apply_service",
            queue="match_queue",
            max_workers=1,
        ),
    ],
)
