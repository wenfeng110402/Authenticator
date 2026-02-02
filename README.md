# Authenticator

```text
  ______               __      __                                                  __                         
 /      \             /  |    /  |                                                /  |                        
/$$$$$$  | __    __  _$$ |_   $$ |____    ______   _______    _______   ______   _$$ |_     ______    ______  
$$ |__$$ |/  |  /  |/ $$   |  $$      \  /      \ /       \  /       | /      \ / $$   |   /      \  /      \ 
$$    $$ |$$ |  $$ |$$$$$$/   $$$$$$$  |/$$$$$$  |$$$$$$$  |/$$$$$$$/  $$$$$$  |$$$$$$/   /$$$$$$  |/$$$$$$  |
$$$$$$$$ |$$ |  $$ |  $$ | __ $$ |  $$ |$$    $$ |$$ |  $$ |$$ |       /    $$ |  $$ | __ $$ |  $$ |$$ |  $$/ 
$$ |  $$ |$$ \__$$ |  $$ |/  |$$ |  $$ |$$$$$$$$/ $$ |  $$ |$$ \_____ /$$$$$$$ |  $$ |/  |$$ \__$$ |$$ |      
$$ |  $$ |$$    $$/   $$  $$/ $$ |  $$ |$$       |$$ |  $$ |$$       |$$    $$ |  $$  $$/ $$    $$/ $$ |      
$$/   $$/  $$$$$$/     $$$$/  $$/   $$/  $$$$$$$/ $$/   $$/  $$$$$$$/  $$$$$$$/    $$$$/   $$$$$$/  $$/       
```

A simple, polished CLI for managing and viewing TOTP (one-time password) codes.

## Features

- Store and manage TOTP secrets (add / rename / delete / list)
- View live, continuously updating TOTP codes
- Textual-based dashboard for a modern terminal UI

## Requirements

- Python 3.9+

## Installation

Run `pip install hackauth`

Another way from the project root:

- Create and activate an environment (example uses a local .conda):

  - `conda create -p .conda python=3.11 -y`
  - `conda activate .conda`
- Install dependencies and register the CLI:

  - `pip install -e .`

## Usage

Show version:

`auth version`

Generate a TOTP code from a secret (replace with your own secret):

`auth now JBSWY3DPEHPK3PXP`

Manage stored secrets (add/rename/delete/list):

`auth settings`

Open the live dashboard:

`auth panel`

Show your stored keys:

`auth output`

Optionally, export in different formats:

`auth output --format json`
`auth output --format plain`
