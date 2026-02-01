import click
import time
import questionary
import urllib.parse
import os
import authenticator
import authenticator.core
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from authenticator.storage import Storage

console = Console()

ASCII_ART = """  ______               __      __                                                  __                         
 /      \             /  |    /  |                                                /  |                        
/$$$$$$  | __    __  _$$ |_   $$ |____    ______   _______    _______   ______   _$$ |_     ______    ______  
$$ |__$$ |/  |  /  |/ $$   |  $$      \  /      \ /       \  /       | /      \ / $$   |   /      \  /      \ 
$$    $$ |$$ |  $$ |$$$$$$/   $$$$$$$  |/$$$$$$  |$$$$$$$  |/$$$$$$$/  $$$$$$  |$$$$$$/   /$$$$$$  |/$$$$$$  |
$$$$$$$$ |$$ |  $$ |  $$ | __ $$ |  $$ |$$    $$ |$$ |  $$ |$$ |       /    $$ |  $$ | __ $$ |  $$ |$$ |  $$/ 
$$ |  $$ |$$ \__$$ |  $$ |/  |$$ |  $$ |$$$$$$$$/ $$ |  $$ |$$ \_____ /$$$$$$$ |  $$ |/  |$$ \__$$ |$$ |      
$$ |  $$ |$$    $$/   $$  $$/ $$ |  $$ |$$       |$$ |  $$ |$$       |$$    $$ |  $$  $$/ $$    $$/ $$ |      
$$/   $$/  $$$$$$/     $$$$/  $$/   $$/  $$$$$$$/ $$/   $$/  $$$$$$$/  $$$$$$$/    $$$$/   $$$$$$/  $$/       
                                                                                                              
                                                                                                              
                                                                                                              """

@click.group(invoke_without_command=True)
@click.option('-v', '--version', is_flag=True, help="Show version information")
#@click.group()
@click.pass_context
def cli(ctx, version):
    """TOTP Authenticator"""
    if version:
        console.print(ASCII_ART, style="cyan")
        console.print(f"v{authenticator.__version__}", style="bold")
    elif ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
@cli.command()
def version():
    console.print(ASCII_ART, style="cyan")
    console.print(f"v{authenticator.__version__}", style="bold")


# TOTP display with countdown
@cli.command()
@click.argument("secret")
@click.option("--refresh", default=4.0, show_default=True, type=float, help="Refresh rate per second")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--once", is_flag=True, help="Print once and exit")
def now(secret, refresh, no_color, once):
    gen = authenticator.core.TOTPGenerator(secret)
    if once:
        code = gen.now()
        remaining = gen.remaining()
        if no_color:
            console.print(Panel(f"{code}\nValid for {remaining} seconds", title="TOTP Code NOW"))
        else:
            console.print(Panel(f"[bold green]{code}[/bold green]\n[green]Valid for {remaining} seconds[/green]", title="TOTP Code NOW", border_style="green"))
        return

    with Live(refresh_per_second=refresh) as live:
        try:
            while True:
                code = gen.now()
                remaining = gen.remaining()

                if no_color:
                    panel = Panel(f"{code}\nValid for {remaining} seconds", title="TOTP Code NOW")
                else:
                    # color changes
                    if remaining <= 5:
                        panel = Panel(f"[bold red]{code}[/bold red]\n[red]Valid for {remaining} seconds[/red]", title="TOTP Code NOW", border_style="red")
                    elif remaining <= 10:
                        panel = Panel(f"[bold yellow]{code}[/bold yellow]\n[yellow]Valid for {remaining} seconds[/yellow]", title="TOTP Code NOW", border_style="yellow")
                    else:
                        panel = Panel(f"[bold green]{code}[/bold green]\n[green]Valid for {remaining} seconds[/green]", title="TOTP Code NOW", border_style="green")
                live.update(panel)
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\nExiting...")

# Settings menu
@cli.command()
def settings():
    """Manage stored secrets (add/rename/delete/list)."""
    storage = Storage()

    while True:
        choice = questionary.select(
            "Settings Menu",
            choices=[
                questionary.Choice("Add Key", "add"),
                questionary.Choice("Import from QR Image", "import_qr"),
                questionary.Choice("Rename Key", "rename"),
                questionary.Choice("Delete Key", "delete"),
                questionary.Choice("List Keys", "list"),
                questionary.Choice("Back", "back")
            ],
            use_arrow_keys=True,
            style=questionary.Style([
                ('qmark', 'fg:cyan bold'),
                ('pointer', 'fg:cyan bold'),
                ('highlighted', 'fg:cyan bold'),
                ('selected', 'fg:cyan'),
            ])
        ).ask()
        
        if choice == "back" or choice is None:
            break
            
        elif choice == "add":
            name = questionary.text("Account name (e.g. github/work):").ask()
            if name:
                if name in storage.list_keys():
                    console.print(f"[red]{name} already exists[/red]")
                    continue
                secret = questionary.password("Secret key (hidden input):").ask()
                if secret:
                    try:
                        # Validate secret format
                        gen = authenticator.core.TOTPGenerator(secret)
                        gen.now()
                        storage.add(name, secret)
                        console.print(f"[green]Added: {name}[/green]")
                    except Exception as e:
                        console.print(f"[red]Invalid secret: {e}[/red]")

        elif choice == "import_qr":
            path = questionary.path("Path to QR Code image:").ask()
            if path:
                if not os.path.exists(path):
                    console.print(f"[red]File not found: {path}[/red]")
                    continue
                
                try:
                    import cv2
                    img = cv2.imread(path)
                    if img is None:
                        console.print("[red]Failed to load image. Is it a valid image file?[/red]")
                        continue
                        
                    detector = cv2.QRCodeDetector()
                    data, bbox, _ = detector.detectAndDecode(img)
                    
                    if not data:
                        console.print("[red]No QR code found in the image.[/red]")
                        continue
                        
                    # Parse otpauth URL
                    # Format: otpauth://totp/Label?secret=SECRET&...
                    try:
                        parsed = urllib.parse.urlparse(data)
                        if parsed.scheme != "otpauth" or parsed.netloc != "totp":
                            console.print("[red]QR code is not a TOTP URL (must start with otpauth://totp/)[/red]")
                            console.print(f"Data found: {data}")
                            continue
                            
                        query = urllib.parse.parse_qs(parsed.query)
                        secret = query.get("secret", [None])[0]
                        
                        if not secret:
                            console.print("[red]No secret found in QR code.[/red]")
                            continue
                            
                        # Extract label from path (remove leading /)
                        label = parsed.path.lstrip('/')
                        # If label has issuer prefix (Issuer:Account), use it, or try issuer param
                        issuer = query.get("issuer", [None])[0]
                        
                        default_name = label
                        if issuer and issuer not in label:
                            default_name = f"{issuer}:{label}"
                            
                        # Confirm name
                        console.print(f"[green]Found secret for: {default_name}[/green]")
                        name = questionary.text("Account name:", default=default_name).ask()
                        
                        if name:
                            if name in storage.list_keys():
                                console.print(f"[red]{name} already exists. Please choose a different name.[/red]")
                                # Simple retry logic or just fail? Let's just fail back to menu for simplicity
                                continue
                                
                            # Verify secret works
                            gen = authenticator.core.TOTPGenerator(secret)
                            gen.now()
                            storage.add(name, secret)
                            console.print(f"[green]Successfully added: {name}[/green]")
                            
                    except Exception as e:
                        console.print(f"[red]Error parsing QR data: {e}[/red]")
                        
                except ImportError:
                    console.print("[red]OpenCV is required for QR scanning.[/red]")
                    console.print("Please install it with: [bold]pip install opencv-python[/bold]")
                except Exception as e:
                    console.print(f"[red]Error processing image: {e}[/red]")

        elif choice == "rename":
            keys = list(storage.list_keys().keys())
            if not keys:
                console.print("[yellow]No stored secrets[/yellow]")
                continue
            old = questionary.select("Select a key to rename:", choices=keys).ask()
            if old:
                new = questionary.text("New name:", default=old).ask()
                if new and new != old:
                    if storage.rename(old, new):
                        console.print(f"[green]{old} -> {new}[/green]")
                    else:
                        console.print("[red]Rename failed[/red]")
                        
        elif choice == "delete":
            keys = list(storage.list_keys().keys())
            if not keys:
                console.print("[yellow]No stored secrets[/yellow]")
                continue
            name = questionary.select("Select a key to delete:", choices=keys).ask()
            if name:
                confirm = questionary.confirm(f"Delete {name}?", default=False).ask()
                if confirm:
                    storage.delete(name)
                    console.print(f"[red]Deleted: {name}[/red]")
                    
        elif choice == "list":
            keys = storage.list_keys()
            if not keys:
                console.print("[yellow]No stored secrets[/yellow]")
            else:
                table = Table(title="Stored Secrets", border_style="cyan")
                table.add_column("Name", style="cyan bold")
                table.add_column("Secret Key", style="dim")
                table.add_column("Status", style="green")
                
                for name, secret in keys.items():
                    masked = secret[:4] + "****" + secret[-4:] if len(secret) > 8 else "****"
                    table.add_row(name, masked, "[green]OK[/green]")
                console.print(table)
                console.print(f"\nTotal: {len(keys)} account(s)")
            questionary.text("Press Enter to return").ask()

# panel UI (Textual)
@cli.command()
def panel():
    from authenticator.tui import run_panel

    run_panel()


@cli.command()
@click.option("--format", type=click.Choice(["table", "json", "plain"]), default="table", help="Output your key")
def output(format):
    """Export all stored keys."""
    storage = Storage()
    keys = storage.list_keys()
    
    if not keys:
        console.print("[yellow]No stored secrets[/yellow]")
        return

    if format == "json":
        import json
        console.print_json(data=keys)
    elif format == "plain":
        for name, secret in keys.items():
            console.print(f"{name}: {secret}")
    else:
        table = Table(title="Exported Secrets", border_style="bold magenta")
        table.add_column("Account Name", style="cyan bold")
        table.add_column("Secret Key", style="yellow")
        
        for name, secret in keys.items():
            table.add_row(name, secret)
        console.print(table)


def main():
    cli()

if __name__ == "__main__":
    main()