from inspect import Parameter, Signature
from typing import Any, Dict, List


def augment_signature(signature: Signature, *extra: Parameter) -> Signature:
    if not extra:
        return signature

    parameters = list(signature.parameters.values())
    variadic_keyword_params: List[Parameter] = []
    while parameters and parameters[-1].kind is Parameter.VAR_KEYWORD:
        variadic_keyword_params.append(parameters.pop())

    return signature.replace(parameters=[*parameters, *extra, *variadic_keyword_params])


def augment_annotations(original_annotations: Dict[str, Any], *extra: Parameter) -> Dict[str, Any]:
    augmented_annotations = original_annotations.copy()

    for param in extra:
        if param.annotation is not Parameter.empty:
            augmented_annotations[param.name] = param.annotation

    return augmented_annotations


def locate_param(sig: Signature, dep: Parameter, to_inject: List[Parameter]) -> Parameter:
    """Locate an existing parameter in the decorated endpoint

    If not found, returns the injectable parameter, and adds it to the to_inject list.

    """
    param = next((p for p in sig.parameters.values() if p.annotation is dep.annotation), None)
    if param is None:
        to_inject.append(dep)
        param = dep
    return param
