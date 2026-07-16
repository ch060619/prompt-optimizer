from __future__ import annotations

from pathlib import Path
from time import sleep
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.models import ExportFormat, ModelProviderName, PromptAnalysis
from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.services import AppServices

app = typer.Typer(help="离线提示词分析、优化、模板管理和版本对比工具。")
templates_app = typer.Typer(help="模板库管理。")
history_app = typer.Typer(help="版本历史与对比。")
app.add_typer(templates_app, name="templates")
app.add_typer(history_app, name="history")

console = Console()
services = AppServices(cli_mode=True)


@app.command()
def analyze(prompt: Annotated[str, typer.Argument(help="待分析的提示词")]) -> None:
    """分析提示词质量并输出评分与建议。"""
    try:
        analysis = services.analyzer.analyze(prompt)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    _print_analysis(analysis)


@app.command()
def optimize(
    prompt: Annotated[str, typer.Argument(help="待优化的提示词")],
    template_id: Annotated[str | None, typer.Option("--template-id", "-t")] = None,
    provider: Annotated[ModelProviderName, typer.Option("--provider", "-p")] = "offline",
) -> None:
    """优化提示词并保存版本历史。"""
    try:
        template = services.templates.get(template_id) if template_id else None
        result = services.optimize_and_save(
            original_prompt=prompt,
            prompt=prompt,
            template=template,
            provider_name=provider,
            owner_id=services.cli_owner_id,
        )
    except (ValueError, KeyError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"[bold green]已生成版本 #{result.version_id}[/bold green]")
    console.print(
        f"模型：{result.metadata.provider_used}"
        f"{'（已降级）' if result.metadata.fallback_used else ''}"
    )
    _print_analysis(result.analysis)
    console.print("\n[bold]优化后提示词[/bold]")
    console.print(result.analysis.optimized_prompt)


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
    for item in services.versions.list(services.cli_owner_id or 0):
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
        result = services.versions.diff(old_id, new_id, services.cli_owner_id or 0)
    except KeyError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"分数变化：{result.old_score} -> {result.new_score} ({result.score_delta:+})")
    console.print("\n".join(result.diff_lines))


@app.command("export")
def export_version(
    version_id: Annotated[int, typer.Argument(help="版本 ID")],
    format: Annotated[ExportFormat, typer.Option("--format", "-f")] = "md",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """导出优化结果。"""
    try:
        version = services.versions.get(version_id, services.cli_owner_id or 0)
        content = services.export.render(version, format)
    except (KeyError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if output:
        output.write_text(content, encoding="utf-8")
        console.print(f"[green]已导出到 {output}[/green]")
    else:
        console.print(content)


@app.command()
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


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8000,
) -> None:
    """启动本地 Web 服务。"""
    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def worker(
    poll_seconds: Annotated[float, typer.Option("--poll-seconds")] = 1.0,
    once: Annotated[bool, typer.Option("--once")] = False,
) -> None:
    """Run the persistent SQLite task worker."""
    from prompt_optimizer.api.app import _run_evaluate_task, _run_export_task, _run_optimize_task
    from prompt_optimizer.core.models import EvaluateTaskRequest, ExportRequest, OptimizeRequest
    worker_services = AppServices()

    while True:
        task = worker_services.tasks.claim_next()
        if task is None:
            if once:
                return
            sleep(max(0.1, poll_seconds))
            continue
        if task.kind == "optimize":
            _run_optimize_task(
                worker_services,
                task.id,
                task.owner_id,
                OptimizeRequest.model_validate(task.input_json),
            )
        elif task.kind == "export":
            _run_export_task(
                worker_services,
                task.id,
                task.owner_id,
                ExportRequest.model_validate(task.input_json),
            )
        else:
            _run_evaluate_task(
                worker_services,
                task.id,
                task.owner_id,
                EvaluateTaskRequest.model_validate(task.input_json),
            )
        if once:
            return


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
