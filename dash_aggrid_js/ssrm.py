"""Server-side row model helpers for AgGridJS.

This module translates AG Grid server-side datasource requests into SQL that
DuckDB (and most ANSI-compliant databases) can execute.  It also exposes helper
utilities that automatically register SSRM routes via Dash hooks so apps only
need to declare their DuckDB source in `configArgs`.
"""

from __future__ import annotations

import datetime as _dt
import re
import textwrap
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Iterable

import dash
from dash import hooks
from flask import jsonify, request

try:  # pragma: no cover - handled at runtime
    import duckdb  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - surfaced in register
    duckdb = None  # type: ignore
    _DUCKDB_IMPORT_ERROR = exc
else:
    _DUCKDB_IMPORT_ERROR = None

__all__ = ["sql_for", "distinct_sql", "quote_identifier", "register_duckdb_ssrm"]


_DEFAULT_BASE = "_aggrid/ssrm"
_NUMERIC_FUNCS = {
    "sum",
    "avg",
    "average",
    "mean",
    "min",
    "max",
    "stddev",
    "stddev_pop",
    "stddev_samp",
    "variance",
    "var_pop",
    "var_samp",
}
_IDENT_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_SSRM_REGISTRY: dict[str, dict[str, Any]] = {}
_REGISTERED_BASES: set[str] = set()
_APP_ROUTE_CACHE: dict[int, set[str]] = {}


def quote_identifier(raw: str) -> str:
    """
    Quote a SQL identifier for use in generated statements.

    Only simple identifiers (letters, digits, underscore) are permitted.
    """
    if not _IDENT_RX.match(raw or ""):
        raise ValueError(f"Unsupported identifier: {raw!r}")
    return f'"{raw}"'


def _sql_literal(val: Any) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, str):
        return "'" + val.replace("'", "''") + "'"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (_dt.date, _dt.datetime)):
        # DuckDB accepts ISO-formatted literal strings
        return "'" + val.isoformat() + "'"
    return str(val)


def _date_literal(val: Any) -> str:
    if isinstance(val, (_dt.date, _dt.datetime)):
        return (
            f"DATE '{val.date().isoformat()}'"
            if isinstance(val, _dt.datetime)
            else f"DATE '{val.isoformat()}'"
        )

    if isinstance(val, str):
        try:
            parsed = _dt.datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = _dt.datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                return _sql_literal(val)
        return f"DATE '{parsed.date().isoformat()}'"

    return _sql_literal(val)


def _number_pred(col: str, node: Mapping[str, Any]) -> str:
    """
    Convert a single number/date filter leaf into a SQL predicate.
    """
    op = node.get("type", "equals")
    val = node.get("filter")
    val2 = node.get("filterTo")

    if node.get("filterType") == "date":
        # AG Grid uses dateFrom/dateTo for date filters; fall back to filter/filterTo
        val = node.get("dateFrom", val)
        val2 = node.get("dateTo", val2)
        literal = _date_literal
    else:
        literal = _sql_literal

    lit = literal(val)
    lit2 = literal(val2)

    if op == "equals":
        return f"{col} = {lit}"
    if op == "notEqual":
        return f"{col} <> {lit}"
    if op == "lessThan":
        return f"{col} < {lit}"
    if op == "lessThanOrEqual":
        return f"{col} <= {lit}"
    if op == "greaterThan":
        return f"{col} > {lit}"
    if op == "greaterThanOrEqual":
        return f"{col} >= {lit}"
    if op == "inRange":
        return f"{col} BETWEEN {lit} AND {lit2}"
    if op == "blank":
        return f"{col} IS NULL"
    if op == "notBlank":
        return f"{col} IS NOT NULL"

    raise ValueError(f"Unsupported number-filter op: {op}")


def _text_pred(col: str, node: Mapping[str, Any]) -> str:
    op = node.get("type", "contains")
    lit = _sql_literal(node.get("filter", ""))

    if op == "contains":
        return f"{col} ILIKE '%' || {lit} || '%'"
    if op in ("notContains", "doesNotContain"):
        return f"{col} NOT ILIKE '%' || {lit} || '%'"
    if op == "equals":
        return f"{col} = {lit}"
    if op == "notEqual":
        return f"{col} <> {lit}"
    if op in ("startsWith", "beginsWith"):
        return f"{col} ILIKE {lit} || '%'"
    if op == "endsWith":
        return f"{col} ILIKE '%' || {lit}"
    if op == "blank":
        return f"({col} IS NULL OR {col} = '')"
    if op == "notBlank":
        return f"({col} IS NOT NULL AND {col} <> '')"

    raise ValueError(f"Unsupported text-filter op: {op}")


def _child_to_sql(col: str | None, node: Mapping[str, Any]) -> str:
    """
    Recursively translate a filter tree (advanced filter or per-column node).
    """
    if not node:
        return "1=1"

    col_id = col or node.get("colId")
    if not col_id:
        raise ValueError("Filter node missing colId")
    col_expr = quote_identifier(str(col_id))

    filter_type = node.get("filterType")
    if filter_type == "join":
        op = node.get("type", "AND").upper()
        parts = [
            _child_to_sql(None, child)
            for child in node.get("conditions", [])
            if child
        ]
        return "(" + f" {op} ".join(parts) + ")" if parts else "1=1"

    if filter_type == "multi":
        op = node.get("operator", "OR").upper()
        parts = [
            _child_to_sql(col_id, child)
            for child in node.get("conditions", [])
            if child
        ]
        return "(" + f" {op} ".join(parts) + ")" if parts else "1=1"

    if node.get("operator") and node.get("filterType") in {"number", "text"}:
        op = node.get("operator", "AND").upper()
        conditions = node.get("conditions") or [
            node.get("condition1"),
            node.get("condition2"),
        ]
        parts = [_child_to_sql(col_id, child) for child in conditions if child]
        return "(" + f" {op} ".join(parts) + ")" if parts else "1=1"

    if filter_type in {"number", "date"}:
        return _number_pred(col_expr, node)

    if filter_type == "text":
        return _text_pred(col_expr, node)

    if filter_type == "set":
        values = node.get("values") or []
        if not isinstance(values, Iterable):
            raise ValueError("Set filter values must be iterable")
        literals = ", ".join(_sql_literal(v) for v in values)
        if not literals:
            return "1=0"
        return f"{col_expr} IN ({literals})"

    raise ValueError(f"Unsupported filterType: {filter_type}")


def _agg_expr(col: str, func: str) -> str:
    func_norm = (func or "").lower()
    if func_norm in _NUMERIC_FUNCS:
        return f"{func_norm.upper()}(try_cast({col} AS DOUBLE)) AS {col}"
    if func_norm == "count":
        return f"COUNT({col}) AS {col}"
    return f"{func_norm.upper()}({col}) AS {col}"


def sql_for(request: Mapping[str, Any] | None, table: str | Any) -> str:
    """
    Build an SQL query that reflects the passed AG Grid SSRM request.

    Parameters
    ----------
    request:
        The ``params.request`` payload emitted by AG Grid's datasource.
    table:
        Table name, schema-qualified table, sub-query, or any object exposing
        ``sql()`` (e.g. DuckDB relations).
    """
    req = dict(request or {})

    if isinstance(table, str):
        if not table.lstrip(" (").startswith(("SELECT", "(")):
            table_sql = table
        else:
            table_sql = table
    else:
        if not hasattr(table, "sql"):
            raise TypeError("table must be a string or expose a .sql() method")
        table_sql = f"({table.sql()}) AS t"

    column_state = req.get("columnState") or []
    column_state_lookup = {
        col["colId"]: quote_identifier(str(col["colId"]))
        for col in column_state
        if col.get("colId")
    }

    row_group_cols = req.get("rowGroupCols")
    if row_group_cols is None:
        row_group_cols = [
            {"field": col["colId"]}
            for col in column_state
            if col.get("rowGroup")
        ]

    value_cols = req.get("valueCols")
    if value_cols is None:
        value_cols = [
            {"field": col["colId"], "aggFunc": col.get("aggFunc", "sum")}
            for col in column_state
            if col.get("aggFunc")
        ]

    group_keys = req.get("groupKeys") or []

    filters = []
    filter_model = req.get("filterModel") or {}
    if filter_model:
        if isinstance(filter_model, Mapping) and "filterType" in filter_model:
            filters.append(_child_to_sql(None, filter_model))
        else:
            for col, node in filter_model.items():
                filters.append(_child_to_sql(col, node))

    group_cols = [
        {
            "field": entry["field"],
            "expr": column_state_lookup.get(
                entry["field"],
                quote_identifier(str(entry["field"])),
            ),
        }
        for entry in row_group_cols
        if entry.get("field")
    ]
    for group_meta, key_val in zip(group_cols, group_keys):
        filters.append(f"{group_meta['expr']} = {_sql_literal(key_val)}")

    where_clause = (
        "WHERE " + " AND ".join(filters) if filters else ""
    )

    depth = len(group_keys)
    at_leaf = depth >= len(group_cols)

    if at_leaf:
        select_cols = ["*"]
        group_by_clause = ""
    else:
        next_group = group_cols[depth]["expr"]
        select_cols = [next_group]
        select_cols.extend(
            _agg_expr(
                column_state_lookup.get(
                    v["field"],
                    quote_identifier(str(v["field"])),
                ),
                v.get("aggFunc", "sum"),
            )
            for v in value_cols
            if v.get("field")
        )
        group_by_clause = f"GROUP BY {next_group}"

    allowed_for_sort: set[str] = set()
    if at_leaf:
        allowed_for_sort.update(column_state_lookup.values())
    else:
        allowed_for_sort.add(group_cols[depth]["expr"])
        allowed_for_sort.update(
            column_state_lookup.get(
                v["field"], quote_identifier(str(v["field"]))
            )
            for v in value_cols
            if v.get("field")
        )

    sort_clauses: list[str] = []
    for entry in req.get("sortModel") or []:
        col_id = entry.get("colId")
        direction = entry.get("sort")
        if not col_id or not direction:
            continue
        col_expr = column_state_lookup.get(col_id)
        if not col_expr:
            col_expr = quote_identifier(str(col_id))
        if col_expr not in allowed_for_sort:
            continue
        sort_clauses.append(f"{col_expr} {direction.upper()}")
    order_clause = "ORDER BY " + ", ".join(sort_clauses) if sort_clauses else ""

    limit_clause = ""
    start_row = req.get("startRow")
    end_row = req.get("endRow")
    if start_row is not None and end_row is not None:
        try:
            limit = int(end_row) - int(start_row)
            offset = int(start_row)
        except (TypeError, ValueError):
            limit = None
            offset = None
        if limit is not None and limit >= 0:
            limit_clause = f"LIMIT {limit} OFFSET {offset or 0}"

    sql = f"""
        SELECT {', '.join(select_cols)}
        FROM {table_sql}
        {where_clause}
        {group_by_clause}
        {order_clause}
        {limit_clause}
    """

    return textwrap.dedent(sql).strip()


def distinct_sql(
    target: str | Callable[[Mapping[str, Any]], str],
    column: str,
    request: Mapping[str, Any] | None = None,
) -> str:
    """
    Build a ``SELECT DISTINCT`` statement for the given column.

    Parameters
    ----------
    target:
        Either a table name or a function that returns SQL when given a
        request payload.
    column:
        Column identifier requested by the grid's Set Filter.
    request:
        Optional request payload (should be empty when querying the full
        domain for filters).
    """
    col_sql = quote_identifier(column)

    if callable(target):
        base_sql = target(request or {})
        return f"SELECT DISTINCT {col_sql} FROM ({base_sql}) ORDER BY 1"

    return f"SELECT DISTINCT {col_sql} FROM {target} ORDER BY 1"


def register_duckdb_ssrm(grid_id: str, config: Mapping[str, Any]) -> str:
    """
    Register a grid ID for DuckDB-powered SSRM routes.

    Parameters
    ----------
    grid_id:
        The grid ID supplied to AgGridJS.
    config:
        Dict-like payload nested under ``configArgs['ssrm']`` that must include:

        - ``duckdb_path``: path to the DuckDB file.
        - ``table`` (str/subquery) **or** ``builder`` (callable returning SQL).
        - Optional ``base``/``endpoint`` to customise the route prefix.

    Returns
    -------
    str
        The normalised HTTP endpoint (with leading slash) registered for this
        grid ID. Front-end helpers reuse the value to wire datasource requests.
    """

    if not grid_id:
        raise ValueError("SSR grid requires a non-empty id")
    if not config:
        raise ValueError("SSR configuration cannot be empty")

    grid_key = str(grid_id)
    existing = _SSRM_REGISTRY.get(grid_key)
    if existing:
        return "/" + existing["base"]

    _ensure_duckdb_available()
    base = config.get("endpoint") or config.get("base") or config.get("base_route")
    canonical_base = _normalise_route_base(base)
    base_endpoint = "/" + canonical_base
    distinct_endpoint = f"{base_endpoint}/distinct"

    duckdb_path = config.get("duckdb_path") or config.get("path") or config.get("database")
    if not duckdb_path:
        raise ValueError("SSR config must include 'duckdb_path'")

    builder_fn, distinct_target = _resolve_builders(config)

    print(f'[AgGridJS] SSRM register {grid_key} -> {canonical_base}')
    entry = {
        "base": canonical_base,
        "duckdb_path": Path(duckdb_path),
        "builder": builder_fn,
        "distinct_target": distinct_target,
    }
    _SSRM_REGISTRY[grid_key] = entry
    _register_routes_for_base(canonical_base)

    return base_endpoint.rstrip("/")


def _ensure_duckdb_available() -> None:
    if duckdb is None:  # pragma: no cover - runtime guard
        raise RuntimeError(
            "DuckDB is required for AgGridJS SSRM helpers. "
            "Install the 'duckdb' package to enable this feature."
        ) from _DUCKDB_IMPORT_ERROR


def _normalise_route_base(base: str | None) -> str:
    if not base:
        return _DEFAULT_BASE
    candidate = base.strip("/")
    return candidate or _DEFAULT_BASE


def _resolve_builders(config: Mapping[str, Any]) -> tuple[Callable[[Mapping[str, Any]], str], Any]:
    builder = config.get("builder")
    table = config.get("table")
    relation = config.get("relation")

    if builder and not callable(builder):
        raise TypeError("ssrm.builder must be callable")

    if builder and (table or relation):
        raise ValueError("Provide either 'table'/'relation' or 'builder', not both.")

    if builder:
        return builder, builder

    target = relation or table
    if not target:
        raise ValueError("SSR config requires 'table' (str/relation) when no builder is supplied.")

    def _default_builder(req: Mapping[str, Any], source=target):
        return sql_for(req, source)

    return _default_builder, target


def _register_routes_for_base(base: str) -> None:
    if base in _REGISTERED_BASES:
        return

    def serve_ssrm(grid_id: str, _base=base):
        return _serve_ssrm_request(_base, grid_id)

    serve_ssrm.__name__ = f"aggrid_ssrm_{base.replace('/', '_')}"
    hooks.route(
        name=f"{base}/<grid_id>",
        methods=("POST", "OPTIONS"),
        priority=90,
    )(serve_ssrm)

    def serve_distinct(grid_id: str, column: str, _base=base):
        return _serve_distinct_request(_base, grid_id, column)

    serve_distinct.__name__ = f"aggrid_ssrm_distinct_{base.replace('/', '_')}"
    hooks.route(
        name=f"{base}/distinct/<grid_id>/<column>",
        methods=("GET",),
        priority=90,
    )(serve_distinct)

    @hooks.setup(priority=90)
    def _attach_on_setup(app: "dash.Dash", _base=base):
        _attach_routes_to_app(app, _base, serve_ssrm, serve_distinct)

    _maybe_attach_to_current_app(base, serve_ssrm, serve_distinct)
    _REGISTERED_BASES.add(base)


def _maybe_attach_to_current_app(base: str, serve_ssrm, serve_distinct) -> None:
    try:
        app = dash.get_app()
    except Exception:  # pragma: no cover
        app = None
    if app is None:
        return
    _attach_routes_to_app(app, base, serve_ssrm, serve_distinct)


def _attach_routes_to_app(app: "dash.Dash", base: str, serve_ssrm, serve_distinct) -> None:
    cache = _APP_ROUTE_CACHE.setdefault(id(app), set())
    if base in cache:
        return

    flask_app = app.server
    base_clean = base.strip("/") or _DEFAULT_BASE
    rule_base = f"/{base_clean}/<grid_id>"
    rule_distinct = f"/{base_clean}/distinct/<grid_id>/<column>"

    endpoint_suffix = base_clean.replace("/", "_")
    endpoint_base = f"aggrid_ssrm_{endpoint_suffix}_{id(app)}"
    endpoint_distinct = f"aggrid_ssrm_distinct_{endpoint_suffix}_{id(app)}"

    existing = {rule.rule for rule in flask_app.url_map.iter_rules()}
    if rule_base not in existing:
        flask_app.add_url_rule(
            rule_base,
            endpoint=endpoint_base,
            view_func=serve_ssrm,
            methods=["POST", "OPTIONS"],
        )

    if rule_distinct not in existing:
        flask_app.add_url_rule(
            rule_distinct,
            endpoint=endpoint_distinct,
            view_func=serve_distinct,
            methods=["GET"],
        )

    cache.add(base)


def _serve_ssrm_request(base: str, grid_id: str):
    entry = _SSRM_REGISTRY.get(grid_id)
    if not entry or entry["base"] != base:
        return jsonify({"error": f"No SSRM configuration registered for grid {grid_id!r}"}), 404

    try:
        payload = request.get_json(force=True) or {}
    except Exception as err:  # pragma: no cover - Flask handles JSON errors
        return jsonify({"error": f"Invalid JSON payload: {err}"}), 400

    builder = entry["builder"]

    try:
        query_sql = _ensure_sql(builder(payload))
        count_payload = {
            key: value
            for key, value in payload.items()
            if key not in {"startRow", "endRow"}
        }
        count_sql = _ensure_sql(builder(count_payload))
    except Exception as err:
        return jsonify({"error": f"Failed to build SSRM SQL: {err}"}), 500

    try:
        with duckdb.connect(str(entry["duckdb_path"]), read_only=True) as con:
            rows = _fetch_rows(con, query_sql)
            total = _execute_count(con, count_sql)
    except Exception as err:
        return jsonify({"error": f"DuckDB execution failed: {err}"}), 500

    return jsonify({"rows": rows, "rowCount": total})


def _serve_distinct_request(base: str, grid_id: str, column: str):
    entry = _SSRM_REGISTRY.get(grid_id)
    if not entry or entry["base"] != base:
        return jsonify({"error": f"No SSRM configuration registered for grid {grid_id!r}"}), 404

    try:
        sql = distinct_sql(entry["distinct_target"], column)
    except Exception as err:
        return jsonify({"error": f"Failed to build distinct SQL: {err}"}), 500

    try:
        with duckdb.connect(str(entry["duckdb_path"]), read_only=True) as con:
            values = [row[0] for row in con.sql(sql).fetchall()]
    except Exception as err:
        return jsonify({"error": f"DuckDB execution failed: {err}"}), 500

    return jsonify([str(value) for value in values if value is not None])


def _ensure_sql(candidate: Any) -> str:
    if isinstance(candidate, str):
        return candidate
    if hasattr(candidate, "sql"):
        return candidate.sql()
    raise TypeError("SSR builder must return a SQL string or DuckDB relation.")


def _fetch_rows(connection: "duckdb.DuckDBPyConnection", sql: str) -> list[dict[str, Any]]:
    relation = connection.sql(sql)
    columns = relation.columns
    return [dict(zip(columns, row)) for row in relation.fetchall()]


def _execute_count(connection: "duckdb.DuckDBPyConnection", sql: str) -> int:
    return connection.sql(f"SELECT COUNT(*) FROM ({sql})").fetchone()[0]


# Ensure the default SSRM route is registered as soon as the module loads so
# Dash apps with callable layouts have the endpoints mounted before the first
# request is processed.
_register_routes_for_base(_DEFAULT_BASE)
