import os
import requests
import json
from collections import defaultdict

# Configuración
USERNAME = "Haruki-24"
TOKEN = os.getenv("STATS_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

# Diccionario de extensiones
EXTENSIONS = {
    ".py": "Python (+Jupyter)", 
    ".ipynb": "Python (+Jupyter)",
    ".ts": "TypeScript", 
    ".tsx": "TypeScript",
    ".js": "JavaScript", 
    ".html": "HTML", 
    ".css": "CSS", 
    ".rs": "Rust",
    ".sql": "SQL",
    ".java": "Java"
}

COLORS = {
    "Python (incl. Jupyter)": "#FFD43B", # Amarillo Python
    "TypeScript": "#3178C6",            # Azul TypeScript
    "JavaScript": "#F1E05A",            # Amarillo JS
    "HTML": "#E34C26",                  # Naranja HTML
    "CSS": "#563D7C",                   # Morado CSS
    "Rust": "#DEA584",                  # Marrón Rust
    "SQL": "#E38C00"                    # Naranja SQL
}

# Ignorar 
IGNORE_DIRS = ["node_modules", "venv", ".git", "dist", "build", "__pycache__"]

def get_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error obteniendo repos: {response.status_code}")
            break
        data = response.json()
        if not data:
            break
        repos.extend([r for r in data if not r["fork"]])
        page += 1
    return repos

def get_repo_tree(repo_name, default_branch):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/git/trees/{default_branch}?recursive=1"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("tree", [])
    return []

def generate_svg(lang_stats, total_count, total_size):
    # Ordenar por el porcentaje compuesto
    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1]['compound'], reverse=True)[:6]
    
    # Generar las filas del SVG
    rows = ""
    y_offset = 50
    for lang, stats in sorted_langs:
        count_pct = (stats['count'] / total_count) * 100 if total_count else 0
        size_pct = (stats['size'] / total_size) * 100 if total_size else 0
        compound = stats['compound']

        bar_color = COLORS.get(lang, "#4FD1C5") 
        
        rows += f"""
        <text x="20" y="{y_offset}" fill="#E2E8F0" font-family="sans-serif" font-size="13" font-weight="bold">{lang}</text>
        <rect x="170" y="{y_offset - 12}" width="180" height="12" fill="#2D3748" rx="6" />
        <rect x="170" y="{y_offset - 12}" width="{compound * 1.8}" height="12" fill="{bar_color}" rx="6" />
        <text x="360" y="{y_offset}" fill="#A0AEC0" font-family="sans-serif" font-size="12" font-weight="bold">{compound:.1f}%</text>
        <text x="410" y="{y_offset}" fill="#718096" font-family="sans-serif" font-size="10">C: {count_pct:.1f}% | S: {size_pct:.1f}%</text>
        """
        y_offset += 28

    svg = f"""<svg width="550" height="{y_offset + 10}" xmlns="http://www.w3.org/2000/svg">
    <rect width="550" height="{y_offset + 10}" fill="#1A202C" rx="10" />
    <text x="20" y="30" fill="#63B3ED" font-family="sans-serif" font-size="16" font-weight="bold">Real Code Stats (Count + Size)</text>
    {rows}
    </svg>"""
    
    os.makedirs("profile", exist_ok=True)
    with open("profile/custom-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("✅ Archivo profile/custom-stats.svg generado.")

def main():
    repos = get_repos()
    lang_stats = defaultdict(lambda: {"count": 0, "size": 0, "compound": 0.0})
    total_count = 0
    total_size = 0

    print(f"Analizando {len(repos)} repositorios...")
    for repo in repos:
        tree = get_repo_tree(repo["name"], repo["default_branch"])
        for item in tree:
            if item["type"] == "blob":
                path = item["path"]
                if any(d in path for d in IGNORE_DIRS):
                    continue
                
                ext = os.path.splitext(path)[1].lower()
                if ext in EXTENSIONS:
                    lang = EXTENSIONS[ext]
                    size = item.get("size", 0)
                    
                    lang_stats[lang]["count"] += 1
                    lang_stats[lang]["size"] += size
                    total_count += 1
                    total_size += size

    # Calcular métricas compuestas (50% cantidad, 50% tamaño)
    for lang, stats in lang_stats.items():
        count_pct = (stats['count'] / total_count) * 100 if total_count else 0
        size_pct = (stats['size'] / total_size) * 100 if total_size else 0
        stats['compound'] = (count_pct * 0.5) + (size_pct * 0.5) # Promedio ponderado

    generate_svg(lang_stats, total_count, total_size)

if __name__ == "__main__":
    main()
