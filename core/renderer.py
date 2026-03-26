from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def render(data: dict, mode: str) -> None:
    console.print()
    console.rule(f"[bold cyan]Erisia Research System[/bold cyan]  [dim]({mode.upper()} MODE)[/dim]")
    console.print()

    console.print(f"[dim]Paper:[/dim] [bold]{data.get('paper_title', 'Unknown')}", highlight=False)
    console.print()

    verdict = data.get("final_verdict", "")
    if verdict:
        console.print(Panel(verdict, title="[green]Final Verdict[/green]", border_style="green"))

    technical_summary = data.get("technical_summary", {})
    if technical_summary:
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column(style="dim", width=12)
        table.add_column()
        table.add_row("Problem", technical_summary.get("problem", ""))
        table.add_row("Method", technical_summary.get("method", ""))
        table.add_row("Result", technical_summary.get("result", ""))
        console.print(Panel(table, title="[white]Technical Summary[/white]", border_style="white"))

    if mode in ("understand", "dual"):
        understanding = data.get("understanding", {})
        if understanding:
            content = Text()
            content.append("Simple Explanation\n", style="bold cyan")
            content.append(understanding.get("simple_explanation", "") + "\n\n")
            content.append("Core Idea\n", style="bold cyan")
            content.append(f"\"{understanding.get('one_line_core', '')}\"\n\n", style="italic")
            content.append("Mental Model\n", style="bold cyan")
            content.append(understanding.get("mental_model", "") + "\n\n")
            content.append("Why It Matters\n", style="bold cyan")
            content.append(understanding.get("why_it_matters", ""))
            console.print(Panel(content, title="[cyan]Understanding[/cyan]", border_style="cyan"))

    if mode in ("apply", "dual"):
        application = data.get("application_to_erisia", {})
        if application:
            relevance = application.get("relevance", {})
            relevance_line = "  ".join(
                f"[green]yes[/green] {key.capitalize()}" if value else f"[dim]no {key.capitalize()}[/dim]"
                for key, value in relevance.items()
            )

            takeaways = "\n".join(f"- {item}" for item in application.get("key_takeaways", []))
            experiments = "\n".join(
                f"{index + 1}. {item}"
                for index, item in enumerate(application.get("experiment_suggestions", []))
            )

            content = Text()
            content.append("Relevance\n", style="bold green")
            content.append(relevance_line + "\n\n")
            content.append("Key Takeaways\n", style="bold green")
            content.append((takeaways or "- None") + "\n\n")
            content.append("Implementation Ideas\n", style="bold green")
            console.print(Panel(content, title="[green]Application[/green]", border_style="green"))

            ideas_text = Text()
            for idea in application.get("implementation_ideas", []):
                feasibility = idea.get("feasibility", "MEDIUM")
                color = {"HIGH": "green", "MEDIUM": "yellow", "LOW": "red"}.get(feasibility, "white")
                ideas_text.append(f"[{feasibility}] ", style=f"bold {color}")
                ideas_text.append(idea.get("idea", "") + "\n", style="bold")
                ideas_text.append("  " + idea.get("description", "") + "\n\n")
            if ideas_text:
                console.print(Panel(ideas_text, title="[green]Implementation Ideas[/green]", border_style="dim green"))
            if experiments:
                console.print(Panel(experiments, title="[green]Experiment Suggestions[/green]", border_style="dim green"))

    critical_analysis = data.get("critical_analysis", {})
    if critical_analysis:
        content = Text()
        content.append("Limitations\n", style="bold")
        content.append(critical_analysis.get("limitations", "") + "\n\n")
        content.append("Overhyped Parts\n", style="bold red")
        content.append(critical_analysis.get("overhyped_parts", "") + "\n\n", style="red")
        content.append("Real Value\n", style="bold green")
        content.append(critical_analysis.get("real_value", ""), style="green")
        console.print(Panel(content, title="[red]Critical Filter[/red]", border_style="red"))

    deep_research = data.get("deep_research", {})
    if deep_research:
        learnings = deep_research.get("learnings", [])
        sources = deep_research.get("visited_sources", [])
        queries = deep_research.get("generated_queries", [])
        if deep_research.get("depth_requested", 0) or learnings or sources or queries:
            content = Text()
            content.append(
                f"Depth Completed: {deep_research.get('depth_completed', 0)}/{deep_research.get('depth_requested', 0)}\n",
                style="bold cyan",
            )
            content.append(
                f"Breadth Used: {deep_research.get('breadth_used', 0)}\n"
                f"Queries Generated: {len(queries)}\n"
                f"Sources Visited: {len(sources)}\n\n"
            )
            content.append("Top Learnings\n", style="bold cyan")
            content.append(
                "\n".join(f"- {item}" for item in learnings[:6]) or "- No external learnings collected."
            )
            follow_ups = deep_research.get("follow_up_questions", [])
            if follow_ups:
                content.append("\n\nNext Directions\n", style="bold cyan")
                content.append("\n".join(f"- {item}" for item in follow_ups[:5]))
            console.print(Panel(content, title="[cyan]Deep Research[/cyan]", border_style="cyan"))

            if sources:
                source_lines = "\n".join(
                    f"- {item.get('title', 'Untitled')} ({item.get('year', 'n.d.')})\n  {item.get('url', '')}"
                    for item in sources[:5]
                )
                console.print(Panel(source_lines, title="[cyan]External Sources[/cyan]", border_style="dim cyan"))

    if data.get("report_markdown"):
        console.print(
            Panel(
                "A markdown report is ready and will be saved alongside the JSON output when --save is used.",
                title="[white]Report[/white]",
                border_style="white",
            )
        )

    console.print()
