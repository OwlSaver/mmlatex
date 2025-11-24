import re
import sys
import argparse

# --- Configuration ---
INPUT_FILE = "map_data.txt"
OUTPUT_FILE = "project_mindmap.tex"
INDENT_SPACES = 4 

LEVEL_1_ANGLES = [150, 30, 270, 210, 90, 330]

# --- LaTeX Template Sections ---

LATEX_START_TEMPLATE = r"""
\documentclass[11pt, a4paper]{article}
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{tikz}
\usepackage{fontspec}
\usepackage[english]{babel}
\usepackage{longtable} 
\usepackage{booktabs}

% Use Noto Sans for clean, modern look
\babelfont{rm}{Noto Sans} 

% FIXED: Loaded 'babel' library to prevent conflicts with TikZ syntax
\usetikzlibrary{mindmap, trees, shadows, babel}

\pagestyle{empty} 

\begin{document}
\centering
\section*{Project Phases Mind Map}

\begin{tikzpicture}[
    mindmap,
    grow cyclic, 
    text=white,
    concept color=blue!70!black, 
    every node/.style={concept, minimum width=2.5cm, align=center, font=\large},
    level 1 concept/.append style={
        level distance=4cm, 
        sibling angle=120, 
        concept color=red!70, 
        font=\Large\bfseries
    },
    level 2 concept/.append style={
        level distance=3.5cm, 
        sibling angle=60, 
        concept color=orange!70,
        font=\large\sffamily
    },
    level 3 concept/.append style={
        level distance=3cm, 
        sibling angle=45, 
        concept color=green!70!black,
        font=\small\sffamily
    },
]

  % START OF TIKZ NODES
"""

TIKZ_END = r"""
  ; % End of the main node structure

\end{tikzpicture}

\vspace{0.5in}
\footnotesize
\textit{This mind map was generated from an indented text file using a Python script.}
"""

LATEX_END = r"""

\end{document}
"""

def generate_latex_table(data):
    """Generates the LaTeX longtable code."""
    table_lines = [
        r"\newpage", 
        r"\section*{Mind Map Node Descriptions}",
        r"{\centering",
        r"\begin{longtable}{@{} p{0.3\textwidth} p{0.6\textwidth} @{}}",
        r"    \caption{Node Details and Descriptions} \label{tab:node_details} \\",
        r"    \toprule",
        r"    \textbf{Node Name} & \textbf{Description} \\",
        r"    \midrule",
        r"    \endfirsthead",
        r"",
        r"    \multicolumn{2}{c}",
        r"    {\normalfont\textbf{\tablename~\thetable\ -- continued}} \\",
        r"    \toprule",
        r"    \textbf{Node Name} & \textbf{Description} \\",
        r"    \midrule",
        r"    \endhead"
    ]
    
    for item in data:
        # Escape critical LaTeX characters for the table
        node_name = item['node'].replace('\\', r'\textbackslash ').replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
        description = item['desc'].replace('\\', r'\textbackslash ').replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
        
        table_lines.append(f"    {node_name} & {description} \\\\")
        table_lines.append(r"    \midrule") 
    
    table_lines.append(r"    \bottomrule")
    table_lines.append(r"\end{longtable}",)
    table_lines.append(r"}") 
    
    return "\n" + "\n".join(table_lines) + "\n"

def get_indentation_level(line):
    """Calculates indentation level, handling potential non-breaking spaces."""
    # Replace non-breaking spaces (char 160) with standard spaces just in case
    clean_line = line.replace('\xa0', ' ')
    leading_spaces = len(clean_line) - len(clean_line.lstrip(' '))
    return leading_spaces // INDENT_SPACES

def parse_line(line):
    full_text = line.strip()
    parts = full_text.split(' - ', 1)
    concept_text = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else ""
    return concept_text, description

def generate_tikz_code(lines):
    tikz_nodes = []
    table_data = [] 
    current_depth = 0 
    angle_index = 0
    
    if not lines:
        return ""

    # --- 1. Process Root Node ---
    root_line = lines[0].rstrip()
    root_concept, root_description = parse_line(root_line)
    table_data.append({'node': root_concept, 'desc': root_description})
    
    # Safe escaping for root node
    safe_root = root_concept.replace('&', r'\&').replace('%', r'\%')
    # Use double backslash for line breaks in TikZ instead of \par
    formatted_root = safe_root.replace(' ', r'\\ ')
    
    root_node_definition = f"\n  \\node[concept] {{ \\textbf{{{formatted_root}}} }}"

    # --- 2. Process Child Nodes ---
    lines_to_process = lines[1:]

    for line in lines_to_process:
        line = line.rstrip() 
        if not line.strip():
            continue 

        raw_depth = get_indentation_level(line)
        
        # Safety: Force depth to be at least 1 and at most +1 of previous
        depth = max(1, raw_depth)
        if depth > current_depth + 1:
            depth = current_depth + 1

        concept_text, description = parse_line(line)
        
        # Escape special characters
        safe_concept = concept_text.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
        
        table_data.append({'node': concept_text, 'desc': description})
        
        # Close previous branches if we are stepping back or staying at same level
        if depth <= current_depth:
            brackets_to_close = (current_depth - depth) + 1
            tikz_nodes.append("    " * depth + "} " * brackets_to_close + "\n")
        
        # Open new child
        if depth == 1:
            angle = LEVEL_1_ANGLES[angle_index % len(LEVEL_1_ANGLES)]
            tikz_nodes.append(f"    " * depth + f"child[grow={angle}] {{\n")
            angle_index += 1
        else:
            tikz_nodes.append(f"    " * depth + "child {\n")
            
        tikz_nodes.append(f"    " * (depth + 1) + f"node[concept] {{{safe_concept}}}")
            
        current_depth = depth

    # Close any remaining open child nodes
    if current_depth > 0:
        tikz_nodes.append("} " * current_depth) 
        
    tikz_code_body = "".join(tikz_nodes)
    latex_table = generate_latex_table(table_data)
    
    return (LATEX_START_TEMPLATE + root_node_definition + 
            tikz_code_body + TIKZ_END + latex_table + LATEX_END)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default=INPUT_FILE)
    parser.add_argument('-o', '--output', type=str, default=OUTPUT_FILE)
    args = parser.parse_args()

    input_lines = []
    if args.input == '-':
        input_lines = sys.stdin.readlines()
    else:
        try:
            with open(args.input, 'r') as f:
                input_lines = f.readlines()
        except Exception as e:
            sys.exit(1)

    if not input_lines:
        full_latex = LATEX_START_TEMPLATE + '\n' + LATEX_END
    else:
        full_latex = generate_tikz_code(input_lines)

    if args.output == '-':
        sys.stdout.write(full_latex)
    else:
        with open(args.output, 'w') as f:
            f.write(full_latex)

if __name__ == "__main__":
    main()