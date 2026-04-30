# Magic Card Finder

Find Commander cards that look powerful for a specific strategy or commander, but may be underplayed on EDHREC.

## Setup

```powershell
pip install -r requirements.txt
```

## Build the local data

Scryfall and EDHREC data are generated locally and are intentionally not committed to git.

```powershell
python main.py fetch-scryfall
python main.py normalize
python main.py tag
python main.py fetch-edhrec --limit 100
python main.py score
python main.py load-db
```

Increase the EDHREC limit once the small test run works:

```powershell
python main.py fetch-edhrec --limit 1000
python main.py score
python main.py load-db
```

## Commands

Show hidden-gem style results:

```powershell
python main.py top
```

Find recommendations for a commander:

```powershell
python main.py commander "Muldrotha" --limit 50 --min-power 50
```

This also writes a commander-specific JSON report under:

```text
data/processed/commander-recommendations/
```

You can choose a custom output path:

```powershell
python main.py commander "Muldrotha" --output "data/processed/Muldrotha recommended.json"
```
