"""Virtual address backend model built from Django settings."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..address_backends import build_backend_diagnostic
from virtualqueryset import InMemoryQuerySet

_slug_cleanup = re.compile(r"[^a-z0-9]+")


def _to_slug(value: str) -> str:
    slug_value = _slug_cleanup.sub("-", value.strip().lower()).strip("-")
    return slug_value or "backend"


class AddressBackendInfoQuerySet(InMemoryQuerySet):
    """In-memory queryset for address backend diagnostics."""

    pass


class AddressBackendInfoManager(models.Manager):
    """Manager returning diagnostics data as an in-memory queryset."""

    def get_queryset(self):
        backends_config = getattr(settings, "GEOADDRESS_BACKENDS", None)
        if not backends_config:
            return AddressBackendInfoQuerySet(model=self.model, data=[])

        diagnostics = []
        payload = {}
        
        # Try to load describe_address_backends function
        describe_fn = None
        try:
            from geoaddress.helpers import describe_address_backends
            describe_fn = describe_address_backends
        except ImportError:
            pass  # Not available, will use fallback
        
        # If we have the function, use it
        if describe_fn:
            try:
                payload = describe_fn(backends_config, skip_api_test=True)
                diagnostics = payload.get("items", [])
            except Exception:
                # Silent fail, use fallback construction below
                diagnostics = []
                payload = {"sample_result": {}, "selected_backend": None}
        else:
            # No helpers available, use fallback
            diagnostics = []
            payload = {"sample_result": {}, "selected_backend": None}

        items = []
        # Build items from diagnostics if available, otherwise from config
        if diagnostics:
            for idx, data in enumerate(diagnostics, start=1):
                # Ensure we have a valid backend_name
                backend_name = data.get("backend_name") or data.get("class_name")
                if not backend_name:
                    class_path = data.get("class", "")
                    class_name = (
                        class_path.split(".")[-1] if class_path else f"Backend {idx}"
                    )
                    backend_name = (
                        class_name.replace("AddressBackend", "")
                        .replace("Backend", "")
                        .lower()
                        or f"backend_{idx}"
                    )
                display_label = data.get("backend_display_name") or backend_name
                data["backend_display_name"] = display_label

                base_slug_source = backend_name or data.get("class") or str(idx)
                slug_value = _to_slug(str(base_slug_source))
                backend = AddressBackendInfo(
                    pk=backend_name,  # Use name as pk for URL generation
                    name=backend_name,
                    class_path=data.get("class") or "",
                    status=data.get("status", "unknown"),
                )
                backend._diagnostic = data
                backend._selected_backend = payload.get("selected_backend")
                backend._sample_result = payload.get("sample_result", {})
                backend._slug = slug_value
                items.append(backend)
        elif backends_config:
            # Fallback: build items directly from config if diagnostics failed
            # Try to load package and config info for each backend
            for idx, backend_config in enumerate(backends_config, start=1):
                class_path = backend_config.get("class", "")
                config = backend_config.get("config", {}) or {}
                class_name = (
                    class_path.split(".")[-1] if class_path else f"Backend {idx}"
                )
                backend_name = (
                    class_name.replace("AddressBackend", "")
                    .replace("Backend", "")
                    .lower()
                    or f"backend_{idx}"
                )
                base_slug_source = backend_name or class_path or str(idx)
                slug_value = _to_slug(str(base_slug_source))

                # Try to load backend class and get package/config info
                diagnostic = {
                    "class": class_path,
                    "class_name": class_name,
                    "status": "unknown",
                    "backend_name": backend_name,
                    "backend_display_name": backend_name,
                    "packages": {},
                    "config": {},
                    "required_packages": [],
                    "required_config_keys": [],
                    "documentation_url": None,
                    "site_url": None,
                }

                try:
                    # Import backend class dynamically
                    from importlib import import_module

                    module_path, class_name_attr = class_path.rsplit(".", 1)
                    module = import_module(module_path)
                    backend_class = getattr(module, class_name_attr)
                    
                    # Get documentation_url, site_url and display_name from class attributes (always available)
                    diagnostic["documentation_url"] = getattr(backend_class, "documentation_url", None)
                    diagnostic["site_url"] = getattr(backend_class, "site_url", None)
                    class_display_name = getattr(backend_class, "display_name", None)
                    if class_display_name:
                        diagnostic["backend_display_name"] = class_display_name
                    
                    backend_instance = backend_class(config=config)
                    diagnostic.update(
                        build_backend_diagnostic(
                            backend_instance,
                            config=config,
                            backend_name=backend_name,
                        )
                    )
                except Exception as exc:
                    # Even if instantiation fails, try to get class-level attributes and check packages
                    try:
                        from importlib import import_module
                        module_path, class_name_attr = class_path.rsplit(".", 1)
                        module = import_module(module_path)
                        backend_class = getattr(module, class_name_attr)
                        diagnostic["documentation_url"] = getattr(backend_class, "documentation_url", None)
                        diagnostic["site_url"] = getattr(backend_class, "site_url", None)
                        diagnostic["required_packages"] = getattr(backend_class, "required_packages", [])
                        diagnostic["required_config_keys"] = getattr(backend_class, "config_keys", [])
                        
                        # Get display_name from class attribute
                        class_display_name = getattr(backend_class, "display_name", None)
                        if class_display_name:
                            diagnostic["backend_display_name"] = class_display_name
                        
                        # Check packages even if instantiation failed
                        required_packages = getattr(backend_class, "required_packages", [])
                        packages_status = {}
                        for pkg in required_packages:
                            try:
                                __import__(pkg)
                                packages_status[pkg] = "installed"
                            except ImportError:
                                packages_status[pkg] = "missing"
                        diagnostic["packages"] = packages_status
                        
                        # Check config keys
                        config_keys = getattr(backend_class, "config_keys", [])
                        config_status = {}
                        for key in config_keys:
                            value = config.get(key)
                            config_status[key] = {
                                "present": "present" if value else "missing",
                                "value_preview": "***" if value else None,
                            }
                        diagnostic["config"] = config_status
                        
                    except Exception:
                        pass
                    
                    diagnostic["error"] = str(exc)
                    
                    # Determine status based on error message
                    error_msg = str(exc).lower()
                    if "is required" in error_msg or "missing" in error_msg or "not found" in error_msg:
                        # Config-related errors
                        diagnostic["status"] = "missing_config"
                    else:
                        diagnostic["status"] = "error"

                backend = AddressBackendInfo(
                    pk=backend_name,
                    name=backend_name,
                    class_path=class_path,
                    status=diagnostic.get("status", "unknown"),
                )
                backend._diagnostic = diagnostic
                backend._selected_backend = None
                backend._sample_result = {}
                backend._slug = slug_value
                items.append(backend)

        return AddressBackendInfoQuerySet(model=self.model, data=items)


class AddressBackendInfo(models.Model):
    """Virtual model describing configured address verification backends."""

    name = models.CharField(max_length=120, verbose_name=_("Backend name"))
    class_path = models.CharField(max_length=255, verbose_name=_("Import path"))
    status = models.CharField(max_length=32, verbose_name=_("Status"))

    objects = AddressBackendInfoManager()

    class Meta:
        managed = False
        verbose_name = _("Address backend")
        verbose_name_plural = _("Address backends")
        default_permissions = ()
        ordering = ["name"]

    def __str__(self):
        return self.display_name

    # Internal helpers -------------------------------------------------
    @property
    def diagnostic(self) -> Dict[str, Any]:
        diag = getattr(self, "_diagnostic", None)
        if isinstance(diag, dict):
            return diag
        return {}

    @property
    def packages(self) -> Dict[str, Any]:
        value = self.diagnostic.get("packages", {}) or {}
        return value if isinstance(value, dict) else {}

    @property
    def required_packages(self):
        return self.diagnostic.get("required_packages", [])

    @property
    def config_entries(self) -> List[Tuple[str, Dict[str, Any]]]:
        config = self.diagnostic.get("config", {}) or {}
        if not isinstance(config, dict):
            return []
        return [(key, details) for key, details in config.items()]

    @property
    def documentation_url(self):
        return self.diagnostic.get("documentation_url")

    @property
    def site_url(self):
        return self.diagnostic.get("site_url")

    @property
    def display_name(self) -> str:
        diag_name = self.diagnostic.get("backend_display_name")
        if isinstance(diag_name, str) and diag_name:
            return diag_name
        return self.name

    @property
    def error(self):
        return self.diagnostic.get("error")

    @property
    def class_name_token(self) -> str:
        if self.class_path:
            return self.class_path.split(".")[-1]
        value = self.diagnostic.get("class_name")
        if isinstance(value, str):
            return value
        return (self.name or "").replace(" ", "_")

    @property
    def slug(self) -> str:
        cached = getattr(self, "_slug", None)
        if cached:
            return str(cached)
        base = self.name or self.diagnostic.get("backend_name") or self.class_name_token
        slug_value = _to_slug(str(base))
        return slug_value

    # Status -----------------------------------------------------------
    @property
    def status_display(self):
        mapping = {
            "working": _("✅ Working"),
            "ready": _("✅ Ready"),
            "missing_packages": _("❌ Missing packages"),
            "missing_config": _("⚠️ Missing configuration"),
            "unavailable": _("⚠️ Unavailable"),
        }
        return mapping.get(self.status, _("❓ Unknown"))

    @property
    def is_selected(self):
        selected = getattr(self, "_selected_backend", None)
        return bool(selected and selected == self.diagnostic.get("backend_name"))

    # Display helpers --------------------------------------------------
    @property
    def packages_summary(self) -> List[Tuple[str, bool]]:
        summary: List[Tuple[str, bool]] = []
        packages = self.packages or {}
        if packages:
            for name, status in packages.items():
                summary.append((name, status == "installed"))
        elif self.required_packages:
            for name in self.required_packages:
                summary.append((name, False))
        return summary

    @property
    def config_summary(self) -> List[Tuple[str, bool, Optional[str]]]:
        entries: List[Tuple[str, bool, Optional[str]]] = []
        for key, details in self.config_entries:
            present = bool(details.get("present"))
            preview = details.get("value_preview")
            if preview is not None:
                preview = str(preview)
            entries.append((key, present, preview))
        return entries


__all__ = ["AddressBackendInfo"]
