"""Template vs View context simple audit.

Scans templates for `{{ var }}` occurrences and Python files for render(..., { ... }) context dictionaries.
Produces a report of template variables that may not be provided by views (best-effort).

Run: python scripts/template_audit.py
"""
import re
import ast
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PROJECT_ROOT / 'templates'

VAR_RE = re.compile(r"{{\s*([a-zA-Z0-9_\.]+)\s*\|?")
RENDER_RE = re.compile(r"render\(request,\s*['\"]([^'\"]+)['\"],\s*\{")


def collect_template_vars():
    result = {}
    for tpl in TEMPLATE_DIR.rglob('*.html'):
        text = tpl.read_text(encoding='utf-8')
        vars_found = set()
        for m in VAR_RE.finditer(text):
            v = m.group(1).split('.')[0]
            vars_found.add(v)
        result[str(tpl.relative_to(PROJECT_ROOT))] = sorted(vars_found)
    return result


def collect_view_contexts():
    result = {}
    for py in PROJECT_ROOT.rglob('apps/**/*.py'):
        try:
            src = py.read_text(encoding='utf-8')
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            # look for calls to render (either render(...) or shortcuts.render(...))
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_render = False
            if isinstance(func, ast.Name) and func.id == 'render':
                is_render = True
            elif isinstance(func, ast.Attribute) and func.attr == 'render':
                is_render = True

            if not is_render:
                continue

            # simple heuristic: find string template arg and dict literal
            args = node.args
            tpl = None
            ctx = []
            if len(args) >= 2 and isinstance(args[1], ast.Constant) and isinstance(args[1].value, str):
                tpl = args[1].value

            # find dict literal either as third positional arg or as keyword arg
            if len(args) >= 3 and isinstance(args[2], ast.Dict):
                for k in args[2].keys:
                    if isinstance(k, ast.Constant):
                        ctx.append(k.value)
            for kw in node.keywords:
                if kw.arg and isinstance(kw.value, ast.Dict):
                    for k in kw.value.keys:
                        if isinstance(k, ast.Constant):
                            ctx.append(k.value)

            if tpl:
                result.setdefault(tpl, set()).update(ctx)
    # normalize keys
    return {k: sorted(v) for k, v in result.items()}


def main():
    print('Scanning templates...')
    tvars = collect_template_vars()
    print(f'Found {len(tvars)} templates')

    print('Scanning views for render contexts...')
    vctx = collect_view_contexts()
    print(f'Found {len(vctx)} render contexts')

    # report per template: which variables not provided by any view (best-effort)
    report = []
    for tpl, vars_ in tvars.items():
        tpl_key = tpl.replace('templates/', '')
        # try direct match in vctx keys
        provided = set()
        # find any view that renders this template (exact match or name)
        # best-effort: check vctx for keys that endwith tpl or equal
        for render_tpl, ctx_keys in vctx.items():
            if tpl_key.endswith(render_tpl) or render_tpl.endswith(tpl_key) or render_tpl == tpl_key:
                provided.update(ctx_keys)
        missing = [v for v in vars_ if v not in provided]
        report.append((tpl, provided, missing))

    # print summary
    print('\nTemplate audit report (template, provided_keys, missing_vars)')
    for tpl, provided, missing in sorted(report):
        if missing:
            print(f'\n- {tpl}')
            print(f'  Provided keys (from views): {sorted(provided)}')
            print(f'  Missing template vars: {sorted(missing)}')

    # write to file
    out = PROJECT_ROOT / 'reports' / 'template_audit.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as fh:
        fh.write('Template audit report\n')
        for tpl, provided, missing in sorted(report):
            fh.write(f'\nTemplate: {tpl}\n')
            fh.write(f'Provided keys: {sorted(provided)}\n')
            fh.write(f'Missing vars: {sorted(missing)}\n')
    print('\nReport written to:', out)


if __name__ == '__main__':
    main()
