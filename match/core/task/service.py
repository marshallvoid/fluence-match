import asyncio
import inspect
from typing import Any, Callable

from fastapi.dependencies.utils import get_typed_signature
from loguru import logger
from pydantic import BaseModel, TypeAdapter

from match.utils.module_loading import import_string


def analyze_param(func: Callable[..., Any], param_name: str, annotation: Any) -> Any:
    if annotation is inspect.Signature.empty:
        logger.error(f"Parameter {param_name} needs to be annotated with type in {func.__name__}")

    if isinstance(annotation, TypeAdapter):
        adapter = annotation
    elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        adapter = annotation  # type: ignore
    else:
        try:
            adapter = TypeAdapter(annotation)
        except Exception as err:
            logger.error(f"Not supported for {annotation}")
            raise err

    return adapter


async def get_handler_params(ctx: dict, func: Callable[..., Any], **kwargs: dict) -> dict:
    func_signature = get_typed_signature(func)
    signature_params = func_signature.parameters
    validated_kwargs = {}
    for param_name, param in signature_params.items():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            err = Exception(f"Positional arguments are not supported in {func.__name__}")
            raise err

        adapter = analyze_param(
            func=func,
            param_name=param_name,
            annotation=param.annotation,
        )

        if param_name in kwargs:
            value = kwargs[param_name]
        elif param.default != inspect.Signature.empty:
            value = param.default
        else:
            err = Exception(f"No value provided for {param_name}")
            raise err

        if adapter:
            if hasattr(adapter, "model_validate"):
                validated_value = adapter.model_validate(value)
            elif hasattr(adapter, "validate_python"):
                validated_value = adapter.validate_python(value)
            else:
                err = Exception(f"Not supported for {adapter.__class__.__name__}")
                raise err
            validated_kwargs[param_name] = validated_value
        else:
            if param_name in kwargs:
                validated_kwargs[param_name] = value

    return validated_kwargs


async def run_service(ctx: dict, service_name: str, func_name: str, params: dict) -> Any:
    container = ctx.get("AsyncContainer")
    assert container, "Container is required to run service"

    assert service_name, "Service name is required to run service"
    assert func_name, "Function name is required to run service"

    async with container() as request_container:
        service_class = import_string(service_name)
        service_instance = await request_container.get(service_class)

        service_func = getattr(service_instance, func_name)
        validated_kwargs = await get_handler_params(ctx, service_func, **params)

        if asyncio.iscoroutinefunction(service_func):
            return await service_func(**validated_kwargs)
        else:
            return service_func(**validated_kwargs)
