# Skyhooper terminal game

The game is written in Python and uses the existing MariaDB database `flight_game`. It uses the existing `airport` and `game` tables and creates one additional `game_save` table. It does not recreate, clear, or modify the existing airport, country, game, goal, or goal_reached tables.

## Requirements

- Python 3.10 or newer
- MariaDB reachable at `localhost:3306`
- A MariaDB account that can read the existing tables and create/modify rows in `game` and `game_save`
- The `flight_game` database and its existing tables

Install the Python dependency:

```powershell
python -m pip install -r requirements.txt
```

Create your local `.env` from the template:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code and replace `your_mariadb_user` and `your_mariadb_password` with your MariaDB credentials. The `.env` file is ignored by Git; do not commit or share it.

Create the new save table once:

```powershell
python main.py --setup-db
```

Then start the game:

```powershell
python main.py
```

Each campaign uses an existing `game` row as its identity. Its named save and full resumable state are stored in `game_save`; every successful flight or purchase is saved transactionally. Quitting also writes a final save. The game loads database settings from `.env` automatically, so you do not need to set them again in each PowerShell session.

## Current rule choices

- Passenger and cargo capacities are separate: up to 20 passengers and up to 500 kg cargo may be carried together.
- Conventional fuel costs EUR 2/L and biofuel costs EUR 3/L. Biofuel emits 60% less CO2 than conventional fuel.
- Conventional combustion emits 2.52 kg CO2/L; hybrid and electric aircraft apply their configured consumption/emission factors.
- The campaign CO2 budget starts at 5,000 kg. Emissions beyond the remaining budget incur EUR 0.05/kg carbon tax.
- Fuel purchases are paid upfront. Flight profit is revenue minus the consumed fuel's cost and any carbon tax; flight history is retained in the save snapshot.

## Balance issue to resolve

The README's targets are not currently reachable with its stated earnings and capacity: maximum passenger/cargo revenue is EUR 1,000 per flight, before fuel costs, while the final target is EUR 25,000 in ten flights. Level 1's EUR 5,000 target in five flights is also at the absolute gross-revenue ceiling and cannot be met after fuel costs. The game currently applies these targets as written, so levels may end in failure. These targets need your approval for revision before a balanced campaign can be completed.
