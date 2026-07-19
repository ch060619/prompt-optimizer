from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from prompt_optimizer.api.app import create_app, create_app_server
from prompt_optimizer.config import ConfigService
from prompt_optimizer.core.models import ExportFormat, ModelProviderName, PromptAnalysis
from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.identity import (
    CLI_NAME,
    LEGACY_CLI_NAME,
    LEGACY_COMPATIBILITY_CUTOFF,
    PRODUCT_NAME,
)
from prompt_optimizer.providers import ModelProviderError
from prompt_optimizer.public import provider_error_presentation
from prompt_optimizer.services import AppServices
from rabbit_code.cli import EXIT_OK
from rabbit_code.cli import main as agent_cli_main
from rabbit_code.maintenance import (
    CompletionShell,
    build_doctor_report,
    build_uninstall_plan,
    execute_uninstall,
    installation_paths,
    package_version,
    render_completion,
)

app = typer.Typer(
    name=CLI_NAME,
    help=f"{PRODUCT_NAME}：离线提示词分析、优化、模板管理和版本对比工具。",
)
prompt_app = typer.Typer(help="Rabbit Code 提示词工作流兼容命令组。")
templates_app = typer.Typer(help="模板库管理。")
history_app = typer.Typer(help="版本历史与对比。")
config_app = typer.Typer(help="分层配置查看。")
app.add_typer(templates_app, name="templates")
app.add_typer(history_app, name="history")
app.add_typer(config_app, name="config")
app.add_typer(prompt_app, name="prompt")
prompt_app.add_typer(templates_app, name="templates")
prompt_app.add_typer(history_app, name="history")

console = Console()
stderr_console = Console(stderr=True)
services = AppServices()

# RC ID: RC-054. Provide the rabbit CLI while warning on the prompt-opt alias.


@app.callback()
def compatibility_notice() -> None:
    if Path(sys.argv[0]).stem.lower().startswith(LEGACY_CLI_NAME):
        stderr_console.print(
            f"[yellow]提示：{LEGACY_CLI_NAME} 已弃用，请迁移到 {CLI_NAME}；"
            f"兼容截止 Rabbit Code {LEGACY_COMPATIBILITY_CUTOFF}。[/yellow]"
        )


@app.command()
@prompt_app.command()
def analyze(prompt: Annotated[str, typer.Argument(help="待分析的提示词")]) -> None:
    """分析提示词质量并输出评分与建议。"""
    try:
        analysis = services.analyzer.analyze(prompt)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _print_analysis(analysis)


@app.command()
@prompt_app.command()
def optimize(
    prompt: Annotated[str, typer.Argument(help="待优化的提示词")],
    template_id: Annotated[str | None, typer.Option("--template-id", "-t")] = None,
    provider: Annotated[ModelProviderName, typer.Option("--provider", "-p")] = "offline",
    model: Annotated[str | None, typer.Option("--model")] = None,
    max_tokens: Annotated[int | None, typer.Option("--max-tokens")] = None,
    max_cost: Annotated[float | None, typer.Option("--max-cost")] = None,
) -> None:
    """优化提示词并保存版本历史。"""
    try:
        template = services.templates.get(template_id) if template_id else None
        result = services.optimization.optimize(
            original_prompt=prompt,
            prompt=prompt,
            template=template,
            provider_name=provider,
            model=model,
            max_tokens=max_tokens,
            max_cost=max_cost,
        )
    except (ValueError, KeyError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    except ModelProviderError as exc:
        presentation = provider_error_presentation(exc)
        stderr_console.print(
            f"Provider error [{presentation.code}/{presentation.category}]: "
            f"{presentation.message}; recovery={presentation.recovery_action}"
            + (
                f"; request_id={presentation.request_id}"
                if presentation.request_id
                else ""
            )
        )
        raise typer.Exit(code=presentation.exit_code) from exc
    console.print(f"[bold green]已生成版本 #{result.version_id}[/bold green]")
    console.print(
        f"模型：{result.metadata.provider_used}"
        f"{'（已降级）' if result.metadata.fallback_used else ''}"
    )
    _print_analysis(result.analysis)
    console.print("\n[bold]优化后提示词[/bold]")
    console.print(result.analysis.optimized_prompt)


@app.command("run")
def run_agent(
    prompt: Annotated[str | None, typer.Argument(help="待执行的提示词")] = None,
    output: Annotated[
        Literal["text", "json", "jsonl"],
        typer.Option("--output", help="输出模式"),
    ] = "text",
) -> None:
    """运行共享 Agent Runtime。"""
    args = ["run", "--output", output]
    if prompt is not None:
        args.append(prompt)
    exit_code = agent_cli_main(args)
    if exit_code != EXIT_OK:
        raise typer.Exit(code=exit_code)


@app.command()
def version() -> None:
    """显示 Rabbit Code 版本。"""
    typer.echo(f"{PRODUCT_NAME} {package_version()}")


@app.command("path")
def show_paths(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """检查安装、数据和数据库路径。"""
    payload = installation_paths().to_dict()
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    for name, value in payload.items():
        typer.echo(f"{name}: {value}")


@app.command()
def doctor(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """诊断 Python、安装路径、数据目录和数据库路径。"""
    report = build_doctor_report()
    if json_output:
        typer.echo(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True))
    else:
        typer.echo(f"Rabbit Code {report.version} ({'ok' if report.ok else 'error'})")
        for check in report.checks:
            typer.echo(f"{check.status}: {check.name}: {check.detail}")
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def completion(
    shell: Annotated[CompletionShell, typer.Argument(help="bash, zsh, fish 或 powershell")],
) -> None:
    """输出指定 Shell 的补全脚本。"""
    typer.echo(render_completion(shell), nl=False)


@app.command()
def uninstall(
    purge_data: Annotated[bool, typer.Option("--purge-data")] = False,
    confirmed: Annotated[bool, typer.Option("--yes", help="确认执行清理")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """清理缓存；删除全部 Rabbit Code 数据必须显式确认。"""
    plan = build_uninstall_plan()
    if not confirmed:
        payload = {"dry_run": True, **plan.to_dict(), "purge_data": purge_data}
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            typer.echo("dry-run: no files removed")
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    removed = execute_uninstall(plan, purge_data=purge_data, confirmed=True)
    payload = {
        "dry_run": False,
        "purge_data": purge_data,
        "removed": [str(path) for path in removed],
    }
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        typer.echo("removed: " + (", ".join(str(path) for path in removed) or "nothing"))


@templates_app.command("list")
def list_templates(
    category: Annotated[str | None, typer.Option("--category", "-c")] = None,
) -> None:
    """列出模板。"""
    table = Table(title="提示词模板库")
    table.add_column("ID")
    table.add_column("名称")
    table.add_column("分类")
    table.add_column("描述")
    for template in services.templates.list_templates(category):
        table.add_row(template.id, template.name, template.category, template.description)
    console.print(table)


@templates_app.command("show")
def show_template(template_id: Annotated[str, typer.Argument(help="模板 ID")]) -> None:
    """查看模板详情。"""
    try:
        template = services.templates.get(template_id)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"[bold]{template.name}[/bold] ({template.category})")
    console.print(template.description)
    console.print("\n[bold]模板[/bold]")
    console.print(template.template)
    console.print("\n[bold]最佳实践[/bold]")
    for item in template.best_practices:
        console.print(f"- {item}")


@history_app.command("list")
def list_history() -> None:
    """列出优化历史。"""
    table = Table(title="版本历史")
    table.add_column("ID")
    table.add_column("分数")
    table.add_column("原始提示词")
    table.add_column("创建时间")
    for item in services.versions.list():
        table.add_row(
            str(item.id),
            str(item.score),
            item.original_preview,
            item.created_at.isoformat(),
        )
    console.print(table)


@history_app.command("diff")
def diff_history(
    old_id: Annotated[int, typer.Argument(help="旧版本 ID")],
    new_id: Annotated[int, typer.Argument(help="新版本 ID")],
) -> None:
    """对比两个版本。"""
    try:
        result = services.versions.diff(old_id, new_id)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"分数变化：{result.old_score} -> {result.new_score} ({result.score_delta:+})")
    console.print("\n".join(result.diff_lines))


@app.command("export")
@prompt_app.command("export")
def export_version(
    version_id: Annotated[int, typer.Argument(help="版本 ID")],
    format: Annotated[ExportFormat, typer.Option("--format", "-f")] = "md",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """导出优化结果。"""
    try:
        version = services.versions.get(version_id)
        content = services.export.render(version, format)
    except (KeyError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]已导出到 {output}[/green]")
    else:
        console.print(content)


@app.command()
@prompt_app.command()
def evaluate(
    dataset: Annotated[Path, typer.Option("--dataset", "-d")],
    output: Annotated[Path, typer.Option("--output", "-o")],
    provider: Annotated[ModelProviderName, typer.Option("--provider", "-p")] = "offline",
) -> None:
    """运行提示词评测集并生成 Markdown 报告。"""
    try:
        report = EvaluationService(services).run_markdown(dataset, provider)
    except (KeyError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    console.print(f"[green]评测报告已生成：{output}[/green]")


@config_app.command("show")
# RC ID: RC-065. Show non-sensitive merged configuration sources in the CLI.
def show_config(
    user_config: Annotated[Path | None, typer.Option("--user-config")] = None,
    workspace: Annotated[Path | None, typer.Option("--workspace")] = None,
    session: Annotated[list[str] | None, typer.Option("--session")] = None,
    override: Annotated[list[str] | None, typer.Option("--override")] = None,
) -> None:
    """显示合并后的配置和来源，不显示敏感值。"""
    try:
        snapshot = ConfigService(
            user_path=user_config,
            workspace_root=workspace,
        ).resolve(
            session=_parse_overrides(session or [], "--session"),
            cli=_parse_overrides(override or [], "--override"),
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    table = Table(title="Rabbit Code 配置")
    table.add_column("配置项")
    table.add_column("值")
    table.add_column("来源")
    table.add_column("作用域")
    for name, entry in snapshot.display().items():
        table.add_row(name, str(entry["value"]), str(entry["source"]), str(entry["scope"]))
    console.print(table)


@app.command()
@prompt_app.command()
def serve(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8000,
    startup_token: Annotated[
        str | None,
        typer.Option("--startup-token", help="严格 App Server 模式的本地启动令牌"),
    ] = None,
) -> None:
    """启动本地 Web 服务。"""
    application = create_app_server(startup_token=startup_token) if startup_token else create_app()
    uvicorn.run(application, host=host, port=port)


def _print_analysis(analysis: PromptAnalysis) -> None:
    score = analysis.score
    console.print(f"[bold]总分：{score.total_score}/100[/bold]")
    table = Table(title="评分维度")
    table.add_column("维度")
    table.add_column("分数")
    table.add_column("说明")
    for dimension in score.dimensions:
        table.add_row(dimension.label, str(dimension.score), dimension.reason)
    console.print(table)
    console.print("\n[bold]优化建议[/bold]")
    for suggestion in analysis.suggestions:
        console.print(f"- [{suggestion.priority}] {suggestion.title}: {suggestion.detail}")


def _parse_overrides(values: list[str], option_name: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for raw_value in values:
        name, separator, raw = raw_value.partition("=")
        if not separator or not name:
            raise ValueError(f"{option_name} 必须使用 key=value 格式。")
        try:
            parsed[name] = json.loads(raw)
        except json.JSONDecodeError:
            parsed[name] = raw
    return parsed
