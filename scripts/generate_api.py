#!/usr/bin/env python3
"""RC ID: RC-062. Generate the frontend API contract from FastAPI OpenAPI."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from prompt_optimizer.api.app import app


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "docs" / "api" / "openapi-v1.json"
GENERATED_DIR = ROOT / "frontend" / "src" / "generated"
GENERATED_PATHS = {
    "schema.ts": GENERATED_DIR / "schema.ts",
    "client.ts": GENERATED_DIR / "client.ts",
}
GENERATED_HEADER = "// AUTO-GENERATED FILE. DO NOT EDIT.\n// RC IDs: RC-062, RC-154, RC-181, RC-184.\n// Source: docs/api/openapi-v1.json\n// Generator: scripts/generate_api.py\n\n"

JsonObject = dict[str, Any]


def canonical_json(value: JsonObject) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def live_openapi() -> JsonObject:
    return app.openapi()


def load_baseline() -> JsonObject:
    return json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))


def ref_name(schema: JsonObject) -> str | None:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return None
    return reference.rsplit("/", 1)[-1]


def ts_string(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def ts_type(schema: JsonObject) -> str:
    reference = ref_name(schema)
    if reference:
        return reference

    if "anyOf" in schema:
        members = [ts_type(item) for item in schema["anyOf"]]
        return " | ".join(dict.fromkeys(members))

    if "oneOf" in schema:
        members = [ts_type(item) for item in schema["oneOf"]]
        return " | ".join(dict.fromkeys(members))

    if "enum" in schema:
        return " | ".join(ts_string(item) for item in schema["enum"])

    schema_type = schema.get("type")
    if schema_type == "string":
        return "string"
    if schema_type == "null":
        return "null"
    if schema_type in {"integer", "number"}:
        return "number"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "array":
        return f"Array<{ts_type(schema.get('items', {}))}>"
    if schema_type == "object":
        properties = schema.get("properties")
        if isinstance(properties, dict) and properties:
            fields = []
            required = set(schema.get("required", []))
            for name, field_schema in properties.items():
                optional = "" if name in required else "?"
                fields.append(f"{property_name(name)}{optional}: {ts_type(field_schema)};")
            return "{ " + " ".join(fields) + " }"
        return "Record<string, unknown>"
    return "unknown"


def property_name(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name) and name not in {
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "enum",
        "export",
        "extends",
        "false",
        "finally",
        "for",
        "function",
        "if",
        "import",
        "in",
        "instanceof",
        "new",
        "null",
        "return",
        "super",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "typeof",
        "var",
        "void",
        "while",
        "with",
        "yield",
    }:
        return name
    return ts_string(name)


def generate_schema(spec: JsonObject) -> str:
    lines = [GENERATED_HEADER.rstrip(), ""]
    schemas = spec["components"]["schemas"]
    for name, schema in schemas.items():
        lines.append(f"export interface {name} {{")
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not properties:
            lines.append("  [key: string]: unknown;")
        else:
            for field_name, field_schema in properties.items():
                optional = "" if field_name in required else "?"
                lines.append(
                    f"  {property_name(field_name)}{optional}: {ts_type(field_schema)};"
                )
        lines.extend(["}", ""])
    return "\n".join(lines)


def camel_case(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:] if part)


def operation_name(operation_id: str) -> str:
    return camel_case(operation_id.split("_api_v1_", 1)[0])


def response_type(operation: JsonObject) -> str:
    response = operation.get("responses", {}).get("200", {})
    content = response.get("content", {})
    if not content:
        return "Response"
    schema = next(iter(content.values())).get("schema", {})
    return ts_type(schema)


def qualify_type(type_expression: str, schema_names: set[str]) -> str:
    for name in sorted(schema_names, key=len, reverse=True):
        type_expression = re.sub(rf"\b{re.escape(name)}\b", f"Schema.{name}", type_expression)
    return type_expression


def request_body_type(operation: JsonObject) -> str | None:
    request_body = operation.get("requestBody")
    if not request_body:
        return None
    content = request_body.get("content", {})
    if not content:
        return None
    return ts_type(next(iter(content.values())).get("schema", {}))


def path_expression(path: str, path_parameters: list[str]) -> str:
    chunks = re.split(r"(\{[^}]+\})", path)
    expression = []
    for chunk in chunks:
        match = re.fullmatch(r"\{([^}]+)\}", chunk)
        if match:
            parameter = match.group(1)
            if parameter not in path_parameters:
                raise ValueError(f"Path parameter {parameter!r} is not declared in {path!r}")
            expression.append(
                f"${{encodeURIComponent(String({camel_case(parameter)}))}}"
            )
        else:
            expression.append(chunk)
    return "`" + "".join(expression) + "`"


def generate_operation(
    path: str,
    method: str,
    operation: JsonObject,
    schema_names: set[str],
) -> list[str]:
    name = operation_name(operation["operationId"])
    parameters = operation.get("parameters", [])
    path_parameters = [item["name"] for item in parameters if item.get("in") == "path"]
    query_parameters = [item for item in parameters if item.get("in") == "query"]
    body_type = request_body_type(operation)
    args: list[str] = []
    for parameter in parameters:
        if parameter.get("in") not in {"path", "query"}:
            continue
        parameter_name = camel_case(parameter["name"])
        optional = "" if parameter.get("required") else "?"
        args.append(f"{parameter_name}{optional}: {ts_type(parameter.get('schema', {}))}")
    if body_type:
        args.append(f"body: Schema.{body_type}")
    if name in {"optimize", "optimizeStream"}:
        args.append("signal?: AbortSignal")
    if name == "optimize":
        args.append("requestId?: string")
    if name == "optimizeStream":
        args.extend(["requestId?: string", "afterSeq?: number"])

    path_value = path_expression(path, path_parameters)
    query_lines = []
    for parameter in query_parameters:
        parameter_name = camel_case(parameter["name"])
        query_lines.append(
            f"      if ({parameter_name} !== undefined && {parameter_name} !== null) "
            "{ query.set("
            f"{ts_string(parameter['name'])}, String({parameter_name})); }}"
        )
    if query_lines:
        path_value = (
            "withQuery(" + path_value + ", (query) => {\n"
            + "\n".join(query_lines)
            + "\n    })"
        )

    response = response_type(operation)
    qualified_response = qualify_type(response, schema_names)
    call_lines = [f"    {name}({', '.join(args)}) {{"]
    call_lines.append(
        f"      return request<{qualified_response}>({path_value}, {{"
    )
    call_lines.append(f'        method: "{method.upper()}",')
    if body_type:
        call_lines.append("        body: JSON.stringify(body),")
    if name in {"optimize", "optimizeStream"}:
        call_lines.append("        ...(signal ? { signal } : {}),")
    if name == "optimize":
        call_lines.extend(
            [
                "        ...(requestId ? {",
                "          headers: { \"X-Request-ID\": requestId },",
                "        } : {}),",
            ]
        )
    if name == "optimizeStream":
        call_lines.extend(
            [
                "        ...(requestId || afterSeq !== undefined ? {",
                "          headers: {",
                '            ...(requestId ? { "X-Request-ID": requestId } : {}),',
                '            ...(afterSeq !== undefined ? { "Last-Event-ID": String(afterSeq) } : {}),',
                "          },",
                "        } : {}),",
            ]
        )
    call_lines.append("      }, true);" if response == "Response" else "      });")
    call_lines.append("    },")
    return call_lines


def generate_client(spec: JsonObject) -> str:
    schema_names = set(spec["components"]["schemas"])
    lines = [GENERATED_HEADER.rstrip(), "", 'import type * as Schema from "./schema";', ""]
    lines.extend(
        [
            "export interface ApiClientOptions {",
            "  baseUrl?: string;",
            "  fetch?: typeof fetch;",
            "  getToken?: () => string | null;",
            "}",
            "",
            "export class ApiRequestError extends Error {",
            "  readonly status: number;",
            "  readonly code?: string;",
            "  readonly category?: string;",
            "  readonly recoveryAction?: string;",
            "  readonly exitCode?: number;",
            "  readonly providerRequestId?: string;",
            "",
            "  constructor(status: number, payload: unknown, fallback: string) {",
            "    const envelope = payload && typeof payload === \"object\" ? payload as Record<string, unknown> : {};",
            "    const detail = envelope.detail && typeof envelope.detail === \"object\" ? envelope.detail as Record<string, unknown> : envelope;",
            "    const message = typeof envelope.detail === \"string\" ? envelope.detail : detail.message;",
            "    super(typeof message === \"string\" ? message : fallback);",
            "    this.name = \"ApiRequestError\";",
            "    this.status = status;",
            "    this.code = typeof detail.code === \"string\" ? detail.code : undefined;",
            "    this.category = typeof detail.category === \"string\" ? detail.category : undefined;",
            "    this.recoveryAction = typeof detail.recovery_action === \"string\" ? detail.recovery_action : undefined;",
            "    this.exitCode = typeof detail.exit_code === \"number\" ? detail.exit_code : undefined;",
            "    this.providerRequestId = typeof detail.provider_request_id === \"string\" ? detail.provider_request_id : undefined;",
            "  }",
            "}",
            "",
            "export function createApiClient(options: ApiClientOptions = {}) {",
            '  const baseUrl = options.baseUrl?.replace(/\\/$/, "") ?? "";',
            "  const fetcher = options.fetch ?? ((input: RequestInfo | URL, init?: RequestInit) => globalThis.fetch(input, init));",
            "",
            "  async function request<T>(",
            "    path: string,",
            "    init: RequestInit,",
            "    returnResponse = false,",
            "  ): Promise<T> {",
            "    const token = options.getToken?.();",
            "    const headers: HeadersInit = {",
            '      ...(init.body ? { "Content-Type": "application/json" } : {}),',
            '      ...(token ? { Authorization: `Bearer ${token}` } : {}),',
            "      ...(init.headers ?? {}),",
            "    };",
            "    const response = await fetcher(`${baseUrl}${path}`, { ...init, headers });",
            "    if (!response.ok) {",
            '      const payload = await response.json().catch(() => ({ detail: response.statusText }));',
            '      const detail = payload && typeof payload === "object" && "detail" in payload',
            "        ? (payload as { detail?: unknown }).detail",
            "        : response.statusText;",
            "      throw new ApiRequestError(response.status, payload, typeof detail === \"string\" ? detail : response.statusText);",
            "    }",
            "    if (returnResponse) {",
            "      return response as T;",
            "    }",
            "    return (await response.json()) as T;",
            "  }",
            "",
            "  function withQuery(path: string, populate: (query: URLSearchParams) => void) {",
            "    const query = new URLSearchParams();",
            "    populate(query);",
            "    const encoded = query.toString();",
            '    return encoded ? `${path}?${encoded}` : path;',
            "  }",
            "",
            "  return {",
        ]
    )

    for path, path_item in spec["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if operation:
                lines.extend(generate_operation(path, method, operation, schema_names))
    lines.extend(["  };", "}", ""])
    return "\n".join(lines)


def generated_artifacts(spec: JsonObject) -> dict[Path, str]:
    return {
        GENERATED_PATHS["schema.ts"]: generate_schema(spec),
        GENERATED_PATHS["client.ts"]: generate_client(spec),
    }


def check_generated() -> None:
    actual = live_openapi()
    baseline = load_baseline()
    if canonical_json(actual) != canonical_json(baseline):
        raise SystemExit(
            "OpenAPI baseline is stale; run python scripts/generate_api.py before checking generated files"
        )
    mismatches = []
    for path, expected in generated_artifacts(actual).items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path.relative_to(ROOT)))
    if mismatches:
        raise SystemExit("Generated API artifacts are stale: " + ", ".join(mismatches))
    print("Generated API artifacts are up to date.")


def write_generated() -> None:
    actual = live_openapi()
    OPENAPI_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAPI_PATH.write_text(canonical_json(actual), encoding="utf-8")
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in generated_artifacts(actual).items():
        path.write_text(content, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the frontend API client from FastAPI OpenAPI.")
    parser.add_argument("--check", action="store_true", help="fail when the baseline or generated files drift")
    args = parser.parse_args(argv)
    if args.check:
        check_generated()
    else:
        write_generated()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
