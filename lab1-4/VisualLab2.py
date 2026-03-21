import os
import xml.etree.ElementTree as ET
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Цвета по типу узла
NODE_COLORS = {
    'program': '#7c6fcd',
    'var_block': '#2a9d8f',
    'block': '#2a9d8f',
    'var_decl': '#4a90d9',
    'assign': '#4a90d9',
    'repeat': '#e07b5a',
    'condition': '#e07b5a',
    'increment': '#e9a84c',
    'binop': '#e9a84c',
    'ident': '#888780',
    'number': '#888780',
    'type': '#888780',
}


def node_label(el):
    tag = el.tag
    if tag == 'ident':      return f"ident\n{el.attrib.get('name', '')}"
    if tag == 'number':     return f"number\n{el.attrib.get('value', '')}"
    if tag == 'type':       return f"type\n{el.attrib.get('name', '')}"
    if tag == 'assign':     return f"assign\nvar={el.attrib.get('var', '')}"
    if tag == 'binop':      return f"binop\nop={el.attrib.get('op', '')}"
    if tag == 'increment':  return f"increment\nvar={el.attrib.get('var', '')}"
    if tag == 'condition':  return f"condition\nop={el.attrib.get('op', '')}"
    return tag


# Обход дерева и вычисление координат
def calc_positions(el, depth=0, counter=[0]):
    positions = {}
    children = list(el)
    child_positions = {}
    for child in children:
        child_positions.update(calc_positions(child, depth + 1, counter))

    if children:
        xs = [child_positions[id(c)][0] for c in children]
        x = sum(xs) / len(xs)
    else:
        x = counter[0]
        counter[0] += 1

    positions[id(el)] = (x, -depth)
    positions.update(child_positions)
    return positions


# отрисовка
def draw_tree(root, ax):
    positions = calc_positions(root)

    def draw(el):
        x, y = positions[id(el)]
        color = NODE_COLORS.get(el.tag, '#cccccc')
        label = node_label(el)
        lines = label.split('\n')

        # Рамка узла
        bbox = dict(boxstyle='round,pad=0.4', facecolor=color, edgecolor='white',
                    linewidth=1.2, alpha=0.92)
        ax.text(x, y, label, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold',
                bbox=bbox, zorder=3)

        # Рёбра к детям
        for child in el:
            cx, cy = positions[id(child)]
            ax.plot([x, cx], [y - 0.18, cy + 0.18],
                    color='#aaaaaa', linewidth=0.9, zorder=1)
            draw(child)

    draw(root)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ast_path = os.path.join(here, 'xml', 'ast.xml')

    if not os.path.exists(ast_path):
        print("[ОШИБКА] Файл ast.xml не найден. Сначала запустите парсер (parser.py).")
        return

    tree = ET.parse(ast_path)
    root = tree.getroot()

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_facecolor('#1e1e2e')
    fig.patch.set_facecolor('#1e1e2e')
    ax.axis('off')

    draw_tree(root, ax)

    # Легенда
    legend_items = [
        ('program', 'корень'),
        ('var_block', 'блоки'),
        ('assign', 'операторы'),
        ('repeat', 'цикл / условие'),
        ('binop', 'выражения'),
        ('ident', 'листья'),
    ]
    patches = [mpatches.Patch(color=NODE_COLORS[k], label=v) for k, v in legend_items]
    ax.legend(handles=patches, loc='lower left', fontsize=8,
              facecolor='#2a2a3e', edgecolor='#555', labelcolor='white',
              framealpha=0.9)

    ax.set_title('AST — Абстрактное синтаксическое дерево', color='white',
                 fontsize=13, pad=12)

    out_path = os.path.join(here, 'img', 'ast_tree.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Дерево сохранено в {out_path}")


if __name__ == '__main__':
    main()
