import os
import re
import glob
import yaml

POSTS_DIR = '_posts/'
SCAN_DIRS = ['_posts/', '_pages/', 'index.md']

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def rename_posts():
    print("--- TASK 1: Renaming Posts ---")
    files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    rename_map = {}

    for filepath in files:
        filename = os.path.basename(filepath)
        match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.*)\.md$', filename)
        if not match: continue
        
        date, old_slug = match.groups()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            yaml_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not yaml_match: continue
                
            data = yaml.safe_load(yaml_match.group(1))
            title = data.get('title')
            if not title: continue

            new_slug = slugify(title)
            new_filename = f"{date}-{new_slug}.md"
            new_filepath = os.path.join(POSTS_DIR, new_filename)

            if filename != new_filename:
                rename_map[old_slug] = new_slug
                os.rename(filepath, new_filepath)
                print(f"Renamed: {filename} -> {new_filename}")
            else:
                rename_map[old_slug] = old_slug

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    return rename_map

def update_links(mapping):
    print("\n--- TASK 2: Updating Internal Links ---")
    if not mapping: return

    sorted_old_slugs = sorted(mapping.keys(), key=len, reverse=True)
    all_files = []
    
    for d in SCAN_DIRS:
        if d.endswith('.md') and os.path.exists(d):
            all_files.append(d)
        elif os.path.isdir(d):
            all_files.extend(glob.glob(os.path.join(d, "**/*.md"), recursive=True))

    total_replacements = 0

    for fpath in all_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            for old_slug in sorted_old_slugs:
                new_slug = mapping[old_slug]
                if old_slug == new_slug: continue

                # NEW REGEX: Matches /posts/old-slug followed by a slash, parenthesis, hashtag, or space
                # This catches: /posts/slug/, /posts/slug), /posts/slug#header
                pattern = rf"(/posts/){re.escape(old_slug)}([/#)?\s])"
                replacement = rf"\g<1>{new_slug}\g<2>"
                
                if re.search(pattern, content):
                    content, count = re.subn(pattern, replacement, content)
                    total_replacements += count
                    print(f"Updated {count} link(s) for '{old_slug}' in {os.path.basename(fpath)}")

            if content != original_content:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)

        except Exception as e:
            print(f"Error processing links in {fpath}: {e}")

    print(f"\nTotal links updated across all files: {total_replacements}")

    # --- DEBUG SCANNER ---
    # Scans for ANY leftover /posts/ links just in case they didn't match the old_slug exactly
    print("\n--- DEBUG SCANNER ---")
    print("Checking for leftover /posts/ links that didn't get updated...")
    for fpath in all_files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                leftover_links = re.findall(r'(/posts/[a-zA-Z0-9-]+/?)', content)
                for link in leftover_links:
                    # Strip slashes to get just the slug
                    clean_slug = link.strip('/').replace('posts/', '')
                    if clean_slug not in mapping.values():
                        print(f"⚠️ Warning: Found link '{link}' in {os.path.basename(fpath)}. (Did not match any new filenames!)")
        except:
            pass

if __name__ == "__main__":
    mapping = rename_posts()
    if mapping:
        update_links(mapping)
    print("\nCaptain, the deck is swept! Check the terminal output above.")