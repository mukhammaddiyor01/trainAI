"""Render the current SQLAlchemy/PostgreSQL ER model as a standalone SVG."""

from html import escape
from pathlib import Path

from sqlalchemy.dialects import postgresql

from backend.database import Base
import backend.models  # noqa: F401 - register model tables


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "trainai-postgresql-er.svg"
WIDTH, HEIGHT = 2770, 1850
CARD_WIDTH = 550
ROW_HEIGHT = 29
POSITIONS = {
    "users": (80, 240),
    "login_sessions": (80, 615),
    "weight_entries": (80, 1020),
    "sleep_entries": (80, 1350),
    "profiles": (745, 240),
    "goals": (745, 620),
    "movement_limitations": (745, 885),
    "training_preferences": (1400, 240),
    "food_preferences": (1400, 650),
    "energy_preferences": (1400, 1110),
    "calorie_proposals": (2095, 240),
    "calorie_target_versions": (2095, 1060),
}
ACCENTS = {
    "users": "#b6f36b", "login_sessions": "#b6f36b",
    "weight_entries": "#7bdfa9",
    "sleep_entries": "#7bdfa9",
    "profiles": "#7bdfa9", "goals": "#7bdfa9",
    "movement_limitations": "#7bdfa9",
    "training_preferences": "#77d8ad", "food_preferences": "#77d8ad",
    "energy_preferences": "#77d8ad",
    "calorie_proposals": "#d8e98c", "calorie_target_versions": "#d8e98c",
}


def type_label(column) -> str:
    value = column.type.compile(dialect=postgresql.dialect()).upper()
    return (value.replace("CHARACTER VARYING", "VARCHAR")
                 .replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMPTZ")
                 .replace("DOUBLE PRECISION", "FLOAT"))


def card(name: str) -> str:
    table = Base.metadata.tables[name]
    x, y = POSITIONS[name]
    height = 102 + len(table.columns) * ROW_HEIGHT
    accent = ACCENTS[name]
    output = [
        f'<g class="card" transform="translate({x} {y})">',
        f'<rect width="{CARD_WIDTH}" height="{height}" rx="22" fill="#101a17" stroke="#30443a" stroke-width="2"/>',
        f'<path d="M22 0 H{CARD_WIDTH - 22} Q{CARD_WIDTH} 0 {CARD_WIDTH} 22 V71 H0 V22 Q0 0 22 0" fill="#17251f"/>',
        f'<rect x="25" y="22" width="8" height="28" rx="4" fill="{accent}"/>',
        f'<text x="51" y="48" class="table-name">{escape(name)}</text>',
        '<line x1="25" x2="525" y1="71" y2="71" stroke="#30443a"/>',
    ]
    for index, column in enumerate(table.columns):
        baseline = 104 + index * ROW_HEIGHT
        key = "PK/FK" if column.primary_key and column.foreign_keys else "PK" if column.primary_key else "FK" if column.foreign_keys else ""
        key_color = "#b6f36b" if key == "PK" else "#72d7bd"
        if key:
            output.append(f'<text x="25" y="{baseline}" class="key" fill="{key_color}">{key}</text>')
        output.append(f'<text x="103" y="{baseline}" class="field">{escape(column.name)}</text>')
        output.append(f'<text x="520" y="{baseline}" class="type" text-anchor="end">{escape(type_label(column))}{" ?" if column.nullable else ""}</text>')
    output.append('</g>')
    return "\n".join(output)


def connector(path: str, label: str, lx: int, ly: int, color: str = "#6dcda3") -> str:
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5" '
            'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"/>'
            f'<text x="{lx}" y="{ly}" class="edge-label">{escape(label)}</text>')


def render() -> str:
    if set(POSITIONS) != set(Base.metadata.tables):
        raise RuntimeError("ER layout must be updated to match the current model tables")
    cards = "\n".join(card(name) for name in POSITIONS)
    edges = [
        connector("M630 340 H745", "1 : 0..1", 650, 328),
        connector("M355 427 V576 H355 V615", "1 : many", 376, 585),
        connector("M745 475 H680 V1130 H630", "1 : many", 650, 1108),
        connector("M745 500 H700 V1460 H630", "1 : many", 650, 1438),
        connector("M1020 487 V620", "1 : 0..1", 1039, 562),
        connector("M935 487 V855 H950 V885", "1 : 0..1", 954, 835),
        connector("M1295 337 H1400", "1 : 0..1", 1307, 324),
        connector("M1295 393 H1350 V725 H1400", "1 : 0..1", 1307, 709),
        connector("M1295 447 H1327 V1183 H1400", "1 : 0..1", 1340, 1166),
        connector("M1295 284 H1340 V225 H2370 V240", "1 : many", 1980, 219),
        connector("M1295 466 H1360 V1020 H2020 V1140 H2095", "1 : many", 1945, 1008),
        connector("M2370 923 V1060", "1 : 0..1", 2391, 1013, "#c4d878"),
    ]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">TrainAI PostgreSQL entity relationship model</title>
<desc id="desc">Twelve current PostgreSQL tables: users, login sessions, profiles, weight and sleep entries, goals, movement limitations, training, food, and energy preferences, calorie proposals, and calorie target versions. Lines show foreign-key relationships.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1 L9 5 L0 9" fill="none" stroke="#80dbaa" stroke-width="1.6"/></marker></defs>
<style>
text{{font-family:Inter,Arial,sans-serif}}
.eyebrow{{font-size:21px;font-weight:700;letter-spacing:5px;fill:#99d881}}
.headline{{font-size:66px;font-weight:780;letter-spacing:-2px;fill:#f1f6ef}}
.subtitle{{font-size:25px;fill:#9fb6aa}}
.table-name{{font-size:28px;font-weight:750;fill:#f2f7ef}}
.field{{font-size:20px;fill:#e4ede6}}
.type{{font-size:17px;fill:#9fb6aa;font-family:ui-monospace,Menlo,monospace}}
.key{{font-size:15px;font-weight:800;letter-spacing:1px}}
.edge-label{{font-size:17px;font-weight:650;fill:#91bbaa}}
.footer{{font-size:20px;fill:#92a99b}}
</style>
<rect width="100%" height="100%" fill="#080e0b"/>
<circle cx="2580" cy="-120" r="580" fill="#102419" opacity=".42"/>
<text x="80" y="88" class="eyebrow">TRAINAI  /  DATA ARCHITECTURE</text>
<text x="80" y="166" class="headline">PostgreSQL ER model</text>
<text x="80" y="207" class="subtitle">Current schema · revision 0011 · 12 tables · owner-scoped fitness data</text>
<g>{''.join(edges)}</g>
<g>{cards}</g>
<line x1="80" x2="2690" y1="1710" y2="1710" stroke="#30443a"/>
<text x="80" y="1755" class="footer">PK  Primary key</text>
<text x="315" y="1755" class="footer">FK  Foreign key</text>
<text x="565" y="1755" class="footer">?  Nullable</text>
<text x="795" y="1755" class="footer">1 : 0..1  Optional one-to-one</text>
<text x="1210" y="1755" class="footer">1 : many  One-to-many</text>
<text x="2690" y="1755" class="footer" text-anchor="end">Generated from SQLAlchemy metadata</text>
</svg>'''


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(OUTPUT)
