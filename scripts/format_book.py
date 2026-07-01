#!/usr/bin/env python3
import os
import sys
import textwrap
import glob

# Known prefixes of narrative lines that follow dialogue lines without a blank line
NARRATIVE_STARTERS = [
    "Me levanto. Mi pantalón",
    "Un chico con barba",
    "Solange camina",
    "No espero. Bajo",
    "Javier entrecierra",
    "Morales mira el",
    "Escucho sus botas",
    "Morales entra en el",
    "Morales escupe en"
]

def should_be_narrative(line):
    line_stripped = line.strip()
    for starter in NARRATIVE_STARTERS:
        if line_stripped.startswith(starter):
            return True
    return False

def is_new_dialogue(line):
    stripped = line.strip()
    if not stripped.startswith("—"):
        return False
    text = stripped[1:].lstrip()
    if not text:
        return False
    # If the text after '—' starts with a lowercase letter, it's a speech tag continuation (e.g. —digo)
    if text[0].islower():
        return False
    return True

def parse_blocks(lines):
    blocks = []
    i = 0
    in_frontmatter = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Frontmatter check
        if i == 0 and line.startswith("---"):
            in_frontmatter = True
            block = {"type": "frontmatter", "lines": [line]}
            i += 1
            while i < len(lines) and in_frontmatter:
                block["lines"].append(lines[i])
                if lines[i].startswith("---"):
                    in_frontmatter = False
                i += 1
            blocks.append(block)
            continue
            
        if stripped == "":
            i += 1
            continue
            
        if stripped.startswith("#"):
            blocks.append({"type": "heading", "lines": [line]})
            i += 1
            continue
            
        # Check if list item
        is_list_start = False
        lstrips = line.lstrip()
        if lstrips.startswith("* ") or lstrips.startswith("- ") or (lstrips and lstrips[0].isdigit() and lstrips[1:].startswith(". ")):
            is_list_start = True
            
        if is_list_start:
            block = {"type": "list_item", "lines": [line]}
            i += 1
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                if next_stripped == "":
                    break
                if next_stripped.startswith("#"):
                    break
                next_lstrips = next_line.lstrip()
                if next_lstrips.startswith("* ") or next_lstrips.startswith("- ") or (next_lstrips and next_lstrips[0].isdigit() and next_lstrips[1:].startswith(". ")):
                    break
                block["lines"].append(next_line)
                i += 1
            blocks.append(block)
            continue
            
        # Paragraph or Dialogue block
        block = {"type": "paragraph", "lines": [line]}
        i += 1
        while i < len(lines):
            next_line = lines[i]
            next_stripped = next_line.strip()
            if next_stripped == "":
                break
            if next_stripped.startswith("#"):
                break
            next_lstrips = next_line.lstrip()
            if next_lstrips.startswith("* ") or next_lstrips.startswith("- ") or (next_lstrips and next_lstrips[0].isdigit() and next_lstrips[1:].startswith(". ")):
                break
            # Split if it is a new dialogue block
            if is_new_dialogue(next_line):
                break
            # Split if it is a narrative block that run-on after dialogue
            if should_be_narrative(next_line):
                break
            block["lines"].append(next_line)
            i += 1
        blocks.append(block)
        
    return blocks

def wrap_list_item(block, width=80):
    lines = block['lines']
    first_line = lines[0]
    stripped = first_line.lstrip()
    indent_len = len(first_line) - len(stripped)
    indent = first_line[:indent_len]
    
    if stripped.startswith("* ") or stripped.startswith("- "):
        prefix = stripped[:2]
        body_start = stripped[2:]
    elif stripped[0].isdigit() and ". " in stripped:
        dot_idx = stripped.find(". ")
        prefix = stripped[:dot_idx + 2]
        body_start = stripped[dot_idx + 2:]
    else:
        prefix = ""
        body_start = stripped
        
    body_parts = [body_start.strip()]
    for l in lines[1:]:
        body_parts.append(l.strip())
    body_text = " ".join(body_parts)
    
    initial_indent = indent + prefix
    subsequent_indent = indent + " " * len(prefix)
    wrapped = textwrap.wrap(body_text, width=width, initial_indent=initial_indent, subsequent_indent=subsequent_indent)
    return wrapped

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.splitlines()
    blocks = parse_blocks(lines)
    
    final_lines = []
    for idx, block in enumerate(blocks):
        # Determine if we need to prepend a blank line
        if idx > 0:
            # We add a blank line between blocks, EXCEPT if the current block and the previous block are both list items.
            # In markdown, list items in the same list should not have blank lines between them.
            prev_block = blocks[idx - 1]
            if not (block['type'] == 'list_item' and prev_block['type'] == 'list_item'):
                final_lines.append("")
                
        if block['type'] in ('frontmatter', 'heading'):
            final_lines.extend(block['lines'])
        elif block['type'] == 'list_item':
            wrapped = wrap_list_item(block)
            final_lines.extend(wrapped)
        elif block['type'] == 'paragraph':
            text = " ".join(l.strip() for l in block['lines'])
            wrapped = textwrap.wrap(text, width=80)
            final_lines.extend(wrapped)
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines) + "\n")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_pattern = os.path.join(base_dir, "content", "docs", "**", "*.md")
    
    files = glob.glob(docs_pattern, recursive=True)
    files = [f for f in files if os.path.basename(f) != "_index.md"]
    files.sort()
    
    print(f"Found {len(files)} markdown files to format.")
    for f in files:
        rel_path = os.path.relpath(f, base_dir)
        process_file(f)
        print(f"Formatted and wrapped: {rel_path}")

if __name__ == "__main__":
    main()
