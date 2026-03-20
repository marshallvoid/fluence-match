from dishka import Provider, Scope, provide

from match.application.common.task_queue.run_service import EnqueueRunService
from match.infrastructure.persistence.nats.task_queue.run_service import EnqueueRunServiceWithNats


class TaskQueueAdaptersProvider(Provider):
    scope = Scope.APP

    run_service = provide(
        EnqueueRunServiceWithNats,
        provides=EnqueueRunService,
    )
