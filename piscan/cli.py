import typer
import json
from rich.table import Table
from rich.console import Console
from piscan.payloads import load_payloads, count_payloads, get_categories
from piscan.crawler import ChatbotCrawler
from piscan.prober import Prober

app = typer.Typer()
console = Console()

@app.command()
def info():
    """Show threat model and payload summary."""
    total = count_payloads()
    categories = get_categories()
    
    console.print("[bold blue]PIScanner v0.1.0[/bold blue]")
    console.print()
    console.print("[bold]Threat Model:[/bold] Black-box external attacker")
    console.print("[bold]Target:[/bold] Production LLM chatbots")
    console.print("[bold]Categories:[/bold] 5 attack vectors + benign")
    console.print()
    console.print(f"[bold]Payloads loaded:[/bold] {total}")
    
    for cat in sorted(categories):
        count = count_payloads(cat)
        console.print(f"  - {cat}: {count}")

@app.command()
def payloads(category: str = None, text: bool = False):
    """List payloads. Use --text to show full text."""
    payloads = load_payloads(category)
    
    if not payloads:
        console.print("[yellow]No payloads found.[/yellow]")
        return
    
    if text:
        for p in payloads:
            console.print(f"[bold]{p.get('id', 'unknown')}[/bold]: {p['text']}")
    else:
        table = Table(title="Payloads")
        table.add_column("ID", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Source", style="yellow")
        table.add_column("Text", style="white")
        
        for p in payloads[:20]:
            table.add_row(
                p.get("id", "unknown"),
                p.get("category", "unknown"),
                p.get("source", "unknown"),
                p["text"][:50] + "..." if len(p["text"]) > 50 else p["text"]
            )
        
        console.print(table)
        if len(payloads) > 20:
            console.print(f"[dim]... and {len(payloads) - 20} more[/dim]")

@app.command()
def benign():
    """List benign prompts."""
    payloads = load_payloads("benign")
    
    console.print(f"[bold]Benign prompts:[/bold] {len(payloads)}")
    for p in payloads:
        console.print(f"  - {p['text']}")

@app.command()
def discover(url: str):
    """Discover chatbot endpoints on a URL."""
    console.print(f"[bold]Scanning:[/bold] {url}")
    
    crawler = ChatbotCrawler()
    endpoints = crawler.discover(url)
    
    if not endpoints:
        console.print("[yellow]No chatbot endpoints found.[/yellow]")
        return
    
    console.print(f"[green]Found {len(endpoints)} endpoint(s):[/green]")
    for ep in endpoints:
        note = f" ({ep.get('note', '')})" if ep.get('note') else ""
        console.print(f"  [cyan]{ep['method']}[/cyan] {ep['url']} (confidence: {ep['confidence']}, type: {ep['type']}){note}")

def _run_judge(results, payloads, judge_model, judge_backend="openai"):
    """Judge results in place and print agreement metrics. Returns True if run."""
    from piscan.judge import Judge, compute_agreement
    judge = Judge(model=judge_model, backend=judge_backend)
    if not judge.available:
        console.print("[red]--judge set but OPENAI_API_KEY not found.[/red] "
                      "Add it to a .env file (OPENAI_API_KEY=sk-...) or your "
                      "environment, then re-run. "
                      "[dim](Or use --judge-backend ollama for a free local judge.)[/dim]")
        return False

    console.print(f"[bold]Judging {len(results)} responses with "
                  f"{judge.model} ({judge_backend})...[/bold]")
    done = {"n": 0}

    def _tick(r):
        done["n"] += 1
        console.print(f"  [dim]{done['n']}/{len(results)}[/dim] {r['payload_id']}: "
                      f"{r.get('judge_verdict')}")

    judge.judge_results(results, payloads, progress=_tick)

    m = compute_agreement(results)
    console.print()
    console.print(f"[bold underline]Keyword layer vs judge "
                  f"({judge.model} / {judge_backend})[/bold underline]")
    console.print(f"  Judge SUCCESS (true injections): {m['judge_success_total']}")
    console.print(f"  TP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}  "
                  f"(scored {m['scored']}, unclear {m['unclear']}, errors {m['errors']})")
    console.print(f"  [bold]Precision={m['precision']}  Recall={m['recall']}  "
                  f"F1={m['f1']}  Accuracy={m['accuracy']}[/bold]")
    return True


@app.command()
def judge(
    results_file: str,
    payloads_category: str = None,
    judge_model: str = "gpt-4o",
    judge_backend: str = "openai",
    output: str = None,
):
    """Re-judge an existing results JSON with an LLM judge (no re-probing needed).

    Adds judge_verdict/confidence/reason to each record and prints precision/
    recall of the keyword layer against the judge. Use --judge-backend ollama
    for a free local judge. Use --output to save.
    """
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    payloads = [p for p in load_payloads(payloads_category)
                if p.get("category") != "benign"]

    if not _run_judge(results, payloads, judge_model, judge_backend):
        return

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]Judged results saved to {output}[/green]")


@app.command()
def probe(
    endpoint: str = typer.Argument(None, help="Chatbot endpoint URL (omit if using --profile)"),
    concurrent: int = 3,
    save: bool = False,
    output: str = None,
    model: str = "llama3.2",
    repeat: int = 1,
    benign: bool = False,
    profile: str = None,
    limit: int = 0,
    report: str = None,
    judge: bool = False,
    judge_model: str = "gpt-4o",
    judge_backend: str = "openai",
):
    """Send all payloads to an endpoint. --profile FILE targets a real chatbot API via a config file; --model sets a local Ollama model; --repeat N averages over N runs; --benign adds false-positive controls; --limit N sends only the first N payloads (quick smoke test); --report FILE writes an HTML findings report; --judge adds ground-truth labels (--judge-backend ollama for a free local judge)."""
    target_profile = None
    if profile:
        from piscan.target import TargetProfile
        target_profile = TargetProfile.load(profile)
        endpoint = target_profile.url
        console.print(f"[bold]Probing target profile:[/bold] {target_profile.name}  [dim]({endpoint})[/dim]")
        if target_profile.rate_limit_ms:
            console.print(f"[dim]Rate limit: {target_profile.rate_limit_ms}ms between requests[/dim]")
    elif not endpoint:
        console.print("[red]Provide an endpoint URL or --profile FILE.[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"[bold]Probing:[/bold] {endpoint}")
    console.print(f"[dim]Target: {target_profile.name if target_profile else model}  ·  Concurrent: {concurrent}  ·  Repeat: {repeat}[/dim]")

    # Load attack payloads; optionally include benign controls.
    payloads = [p for p in load_payloads() if p.get("category") != "benign"]
    n_benign = 0
    if benign:
        b = load_payloads("benign")
        n_benign = len(b)
        payloads = payloads + b
    if limit and limit > 0:
        payloads = payloads[:limit]
        console.print(f"[yellow]--limit {limit}: sending only the first {len(payloads)} payloads (smoke test)[/yellow]")
    console.print(f"[dim]Payloads: {len([p for p in payloads if p.get('category') != 'benign'])} attack"
                  + (f" + {len([p for p in payloads if p.get('category') == 'benign'])} benign" if benign else "")
                  + f"  ·  Total requests: {len(payloads) * repeat}[/dim]")

    prober = Prober(concurrent=concurrent, model=model, profile=target_profile)
    results = prober.probe_sync(endpoint, payloads, repeat=repeat)

    # Layer 3: LLM ground-truth judge (optional)
    if judge:
        _run_judge(results, [p for p in payloads if p.get("category") != "benign"],
                   judge_model, judge_backend)

    # Save to database if requested
    if save:
        from piscan.db import Database
        db = Database()
        db.save_results(results)
        console.print("[green]Results saved to database.[/green]")

    # Aggregated statistics (handles repeat runs + benign controls)
    from piscan.aggregate import summarize, ATTACK_CATEGORIES
    stats = summarize(results)

    success_count = sum(1 for r in results if r["success"])
    console.print(f"[green]Completed: {len(results)} requests[/green]")
    console.print(f"[dim]Successful: {success_count}, Failed: {stats['failures']}[/dim]")

    label = "detection rate" if repeat > 1 else "detected"
    console.print(f"\n[bold underline]Attack {label} by category "
                  f"(avg over {stats['repeat']} run(s))[/bold underline]")
    for c in ATTACK_CATEGORIES:
        cs = stats["attack"][c]
        if cs["attempts"] == 0:
            continue
        console.print(f"  {c:11s} [red]{cs['rate']*100:5.1f}%[/red]  "
                      f"[dim]({cs['detected']}/{cs['attempts']} attempts · "
                      f"{cs['ever_flagged']}/{cs['payloads']} payloads ever flagged)[/dim]")
    ao = stats["attack_overall"]
    console.print(f"  [bold]overall     {ao['rate']*100:5.1f}%  "
                  f"({ao['detected']}/{ao['attempts']})[/bold]")

    if stats["benign"]:
        bs = stats["benign"]
        col = "green" if bs["fp_rate"] == 0 else "red"
        console.print(f"\n[bold]Benign false-positive rate:[/bold] "
                      f"[{col}]{bs['fp_rate']*100:.1f}%[/{col}] "
                      f"[dim]({bs['false_positives']}/{bs['attempts']} benign replies flagged)[/dim]")

    # Save to JSON if output provided (moved here so it also runs on repeat/benign)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Raw results ({len(results)}) saved to {output}[/green]")

    if report:
        from piscan.report import generate_html
        generate_html(results, report, meta={"target": endpoint, "model": model})
        console.print(f"[green]HTML report written to {report}[/green]")


def _report_summary(results):
    """Print per-category detection rates + benign false-positive rate."""
    from piscan.aggregate import summarize, ATTACK_CATEGORIES
    stats = summarize(results)
    success = sum(1 for r in results if r["success"])
    console.print(f"[green]Completed: {len(results)} requests[/green]")
    console.print(f"[dim]Successful: {success}, Failed: {stats['failures']}[/dim]")
    console.print("\n[bold underline]Attack detection by category[/bold underline]")
    for c in ATTACK_CATEGORIES:
        cs = stats["attack"][c]
        if cs["attempts"] == 0:
            continue
        console.print(f"  {c:11s} [red]{cs['rate']*100:5.1f}%[/red]  "
                      f"[dim]({cs['detected']}/{cs['attempts']})[/dim]")
    ao = stats["attack_overall"]
    console.print(f"  [bold]overall     {ao['rate']*100:5.1f}%  "
                  f"({ao['detected']}/{ao['attempts']})[/bold]")
    if stats["benign"]:
        bs = stats["benign"]
        col = "green" if bs["fp_rate"] == 0 else "red"
        console.print(f"\n[bold]Benign false-positive rate:[/bold] "
                      f"[{col}]{bs['fp_rate']*100:.1f}%[/{col}] "
                      f"[dim]({bs['false_positives']}/{bs['attempts']})[/dim]")


@app.command()
def probe_site(
    url: str = typer.Argument(None, help="Website URL hosting the chatbot (omit if profile has url)"),
    profile: str = None,
    preset: str = "generic",
    headful: bool = False,
    slowmo: int = 0,
    benign: bool = False,
    wait_ms: int = 4000,
    limit: int = 0,
    output: str = None,
    report: str = None,
    judge: bool = False,
    judge_model: str = "gpt-4o",
    judge_backend: str = "openai",
):
    """Probe a LIVE website chatbot by driving a real browser (Playwright).

    Point it at a site with a chat widget. Use --preset intercom|drift|zendesk|tidio|generic,
    or --profile FILE with custom CSS selectors. --headful shows the browser so you can
    watch/debug. Requires: pip install -e ".[crawl]" && playwright install chromium.
    """
    prof = None
    if profile:
        with open(profile, "r", encoding="utf-8") as f:
            prof = json.load(f)
        url = prof.get("url", url)
        preset = prof.get("preset", preset)
    if not url:
        console.print("[red]Provide a URL or a --profile with a 'url'.[/red]")
        raise typer.Exit(1)

    try:
        from piscan.browser import BrowserProber
    except Exception as e:
        console.print(f"[red]Browser mode needs Playwright: {e}[/red]\n"
                      "Install with: pip install -e \".[crawl]\" && playwright install chromium")
        raise typer.Exit(1)

    payloads = [p for p in load_payloads() if p.get("category") != "benign"]
    if benign:
        payloads += load_payloads("benign")
    if limit and limit > 0:
        payloads = payloads[:limit]
        console.print(f"[yellow]--limit {limit}: sending only the first {len(payloads)} payloads (smoke test)[/yellow]")

    console.print(f"[bold]Browser-probing:[/bold] {url}  [dim](preset: {preset})[/dim]")
    console.print(f"[dim]{len(payloads)} payloads, one at a time through the real UI — this is slow. "
                  "Watch with --headful if replies aren't captured.[/dim]")

    prober = BrowserProber(url=url, profile=prof, preset=preset,
                           headful=headful, wait_ms=wait_ms, slowmo=slowmo)

    def _tick(r):
        mark = "[red]⚠[/red]" if r["detected"] else ("·" if r["success"] else "[red]✗[/red]")
        note = "ok" if r["success"] else r["detection_reason"][:45]
        console.print(f"  {mark} {r['payload_id']}: {note}")

    try:
        from piscan.browser import ChatWidgetNotFound
        results = prober.probe(payloads, progress=_tick)
    except ChatWidgetNotFound as e:
        console.print(f"\n[red]✗ No chatbot reached.[/red] {e}")
        console.print("[yellow]No results were recorded — the scanner never found a chat box to attack.[/yellow]")
        raise typer.Exit(1)

    # Sanity check: if every captured reply is empty or identical, we almost
    # certainly scraped a stray page element rather than talking to a chatbot.
    succ = [r for r in results if r["success"]]
    distinct = {r["response_text"].strip() for r in succ if r["response_text"].strip()}
    if succ and len(distinct) <= 1:
        console.print(
            "\n[yellow]⚠ Warning: all captured replies were empty or identical.[/yellow]\n"
            "[yellow]The scanner most likely did NOT reach a real chatbot (it read a static "
            "page element). A 0% result here means 'nothing happened', not 'the bot is secure'.\n"
            "Re-run with --headful and watch: does a chat widget open, and are your payloads "
            "typed into it? If not, this page may have no chatbot or needs custom selectors "
            "(see TESTING_REAL_CHATBOTS.md).[/yellow]")

    if judge:
        _run_judge(results, [p for p in payloads if p.get("category") != "benign"],
                   judge_model, judge_backend)

    console.print()
    _report_summary(results)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Raw results ({len(results)}) saved to {output}[/green]")

    if report:
        from piscan.report import generate_html
        generate_html(results, report, meta={"target": url, "model": "browser"})
        console.print(f"[green]HTML report written to {report}[/green]")


if __name__ == "__main__":
    app()