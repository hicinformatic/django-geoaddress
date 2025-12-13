"""Utilities for inspecting address verification backends."""

from __future__ import annotations

import importlib
from typing import Any, Dict, Optional, Sequence

try:
    from geoaddress.helpers import (
        get_address_backends_from_config as ga_get_address_backends_from_config,
        search_addresses as ga_search_addresses,
    )
except ImportError:  # pragma: no cover
    ga_get_address_backends_from_config = None
    ga_search_addresses = None


DEFAULT_ADDRESS_KWARGS: Dict[str, Optional[str]] = {
    "address_line1": "123 Test St",
    "address_line2": None,
    "address_line3": None,
    "city": "Paris",
    "postal_code": "75001",
    "state": None,
    "country": "FR",
}

DEFAULT_EXTRA_KWARGS: Dict[str, Optional[float]] = {
    "latitude": 48.8566,
    "longitude": 2.3522,
}


def _load_backend_class(import_path: str):
    if not import_path:
        raise ValueError("Missing backend import path")

    module_path, class_name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _mask_value(value: Any) -> Optional[str]:
    if not value:
        return None
    value_str = str(value)
    if len(value_str) <= 6:
        return value_str
    return f"{value_str[:3]}…{value_str[-2:]}"


def build_backend_diagnostic(
    backend_instance: Any,
    config: Dict[str, Any],
    *,
    backend_name: str,
    selected_backend: Optional[str] = None,
    is_working: bool = False,
) -> Dict[str, Any]:
    """Compute diagnostic information for a backend instance."""
    check = backend_instance.check_package_and_config()
    packages = check.get("packages", {})
    config_status = check.get("config", {})
    missing_packages = [
        pkg for pkg, status in packages.items() if status != "installed"
    ]
    missing_config = [
        key
        for key in backend_instance.config_keys
        if config_status.get(key) != "present" or not config.get(key)
    ]

    if is_working:
        status = "working"
    elif missing_packages:
        status = "missing_packages"
    elif missing_config:
        status = "missing_config"
    else:
        # All packages and config are present but not tested yet
        status = "ready"

    backend_label = getattr(backend_instance, "name", backend_name)
    return {
        "status": status,
        "backend_name": backend_label,
        "backend_display_name": getattr(
            backend_instance, "label", backend_label
        ),
        "documentation_url": backend_instance.documentation_url,
        "site_url": backend_instance.site_url,
        "required_packages": backend_instance.required_packages,
        "required_config_keys": backend_instance.config_keys,
        "packages": packages,
        "config": {
            key: {
                "present": config_status.get(key) == "present",
                "value_preview": _mask_value(config.get(key)),
            }
            for key in (backend_instance.config_keys or config.keys())
        },
        "selected": selected_backend == getattr(backend_instance, "name", None),
    }


def _build_backend_payload(
    backend_config: Dict[str, Any],
    working_instances: Dict[str, Any],
    selected_backend: Optional[str],
) -> Dict[str, Any]:
    class_path = backend_config.get("class", "")
    config = backend_config.get("config", {}) or {}
    class_name = class_path.split(".")[-1] if class_path else "UnknownBackend"
    data: Dict[str, Any] = {
        "class": class_path,
        "class_name": class_name,
        "status": "error",
        "documentation_url": None,
        "site_url": None,
        "required_packages": [],
        "required_config_keys": [],
        "packages": {},
        "config": {},
        "selected": False,
        "error": None,
    }

    try:
        backend_class = _load_backend_class(class_path)
        backend_instance = working_instances.get(class_name) or backend_class(
            config=config
        )
        diagnostic = build_backend_diagnostic(
            backend_instance,
            config,
            backend_name=class_name,
            selected_backend=selected_backend,
            is_working=class_name in working_instances,
        )
        data.update(diagnostic)
    except Exception as exc:  # pragma: no cover - defensive fallback
        data["error"] = str(exc)

    return data


def _resolve_address_kwargs(
    address_kwargs: Optional[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    resolved = DEFAULT_ADDRESS_KWARGS.copy()
    if not address_kwargs:
        return resolved

    for key, value in address_kwargs.items():
        if value not in (None, ""):
            resolved[key] = str(value)
    return resolved


def _resolve_extra_kwargs(
    operation: str, extra_kwargs: Optional[Dict[str, Any]]
) -> Dict[str, Optional[float]]:
    resolved = DEFAULT_EXTRA_KWARGS.copy()
    if not extra_kwargs:
        return resolved

    if operation != "reverse_geocode":
        return resolved

    try:
        if "latitude" in extra_kwargs and extra_kwargs["latitude"] is not None:
            resolved["latitude"] = float(extra_kwargs["latitude"])
        if "longitude" in extra_kwargs and extra_kwargs["longitude"] is not None:
            resolved["longitude"] = float(extra_kwargs["longitude"])
    except (TypeError, ValueError):
        pass

    return resolved


def build_address_backends_payload(
    *,
    backends_config: Optional[Sequence[Dict[str, Any]]],
    operation: str = "validate",
    address_kwargs: Optional[Dict[str, Any]] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute diagnostics payload for address verification backends."""
    if not backends_config:
        return {
            "configured": 0,
            "working": 0,
            "selected_backend": None,
            "sample_operation": "validate",
            "sample_result": {"error": "No address backends configured"},
            "items": [],
            "address_kwargs": DEFAULT_ADDRESS_KWARGS.copy(),
            "extra_kwargs": DEFAULT_EXTRA_KWARGS.copy(),
            "operations": ["validate", "geocode", "reverse_geocode"],
        }

    operation = (operation or "validate").lower()
    allowed_operations = {"validate", "geocode", "reverse_geocode"}
    if operation not in allowed_operations:
        operation = "validate"

    resolved_address_kwargs = _resolve_address_kwargs(address_kwargs)
    resolved_extra_kwargs = (
        _resolve_extra_kwargs(operation, extra_kwargs)
        if operation == "reverse_geocode"
        else {}
    )

    # Build query string for testing
    address_parts = [
        resolved_address_kwargs.get("address_line1"),
        resolved_address_kwargs.get("postal_code"),
        resolved_address_kwargs.get("city"),
    ]
    test_query = ", ".join(filter(None, address_parts)) or "test address"

    if operation == "reverse_geocode" or ga_search_addresses is None:
        # Reverse geocode not supported by search_addresses
        sample_result = {
            "error": "Reverse geocode test not available",
            "backend_used": None,
        }
    else:
        search_result = ga_search_addresses(
            backends_config=backends_config,
            query=test_query,
            country=resolved_address_kwargs.get("country"),
            limit=1,
        )
        results = search_result.get("results", [])
        if results:
            sample_result = results[0]
            sample_result["backend_used"] = search_result.get("backend_used")
        else:
            sample_result = search_result

    selected_backend = sample_result.get("backend_used")

    working_instances_list = []
    if ga_get_address_backends_from_config:
        working_instances_list = ga_get_address_backends_from_config(backends_config)
    working_instances = {
        instance.__class__.__name__: instance for instance in working_instances_list
    }

    items = [
        _build_backend_payload(config, working_instances, selected_backend)
        for config in backends_config
    ]

    return {
        "configured": len(backends_config),
        "working": len(working_instances),
        "selected_backend": selected_backend,
        "sample_operation": operation,
        "sample_result": sample_result,
        "items": items,
        "address_kwargs": resolved_address_kwargs,
        "extra_kwargs": resolved_extra_kwargs,
        "operations": ["validate", "geocode", "reverse_geocode"],
    }


__all__ = [
    "build_backend_diagnostic",
    "build_address_backends_payload",
]
