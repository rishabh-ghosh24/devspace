#!/usr/bin/env python3
"""
Medium to GitHub Markdown Converter

Converts a Medium article to GitHub-flavored markdown.

Usage:
  python medium_to_markdown.py <medium_url> [output_file.md]
  python medium_to_markdown.py --file <saved_html_file> [output_file.md]

If network restrictions prevent URL fetching, save the Medium page as HTML
in your browser (Ctrl+S / Cmd+S) and use the --file option.
"""

import sys
import re
import os
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def fetch_medium_article(url: str) -> str:
    """Fetch Medium article HTML with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def extract_article_content(html: str, source_url: str) -> dict:
    """Extract article metadata and content from Medium HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Extract title
    title = ""
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Extract author
    author = ""
    author_meta = soup.find('meta', {'name': 'author'})
    if author_meta:
        author = author_meta.get('content', '')

    # Extract publish date
    date = ""
    time_tag = soup.find('time')
    if time_tag:
        date = time_tag.get('datetime', time_tag.get_text(strip=True))

    # Extract article body - Medium uses 'article' tag
    article = soup.find('article')
    if not article:
        # Fallback: look for main content area
        article = soup.find('main') or soup.find('div', class_=re.compile(r'post|article|content'))

    return {
        'title': title,
        'author': author,
        'date': date,
        'source_url': source_url,
        'article_soup': article,
        'full_soup': soup
    }


def convert_element_to_markdown(element) -> str:
    """Convert a single HTML element to markdown."""
    if element.name is None:
        # Text node
        text = str(element).strip()
        return text if text else ""

    tag = element.name.lower()

    # Skip script, style, and other non-content tags
    if tag in ['script', 'style', 'noscript', 'button', 'svg', 'path']:
        return ""

    # Headers
    if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(tag[1])
        text = element.get_text(strip=True)
        if text:
            return f"\n{'#' * level} {text}\n"
        return ""

    # Paragraphs
    if tag == 'p':
        content = process_inline_elements(element)
        if content.strip():
            return f"\n{content}\n"
        return ""

    # Code blocks (pre + code)
    if tag == 'pre':
        code = element.find('code')
        if code:
            code_text = code.get_text()
            # Try to detect language from class
            lang = ""
            classes = code.get('class', [])
            for cls in classes:
                if cls.startswith('language-'):
                    lang = cls.replace('language-', '')
                    break
            return f"\n```{lang}\n{code_text}\n```\n"
        else:
            return f"\n```\n{element.get_text()}\n```\n"

    # Inline code
    if tag == 'code':
        # Only handle if not inside pre
        parent = element.find_parent('pre')
        if not parent:
            return f"`{element.get_text()}`"
        return element.get_text()

    # Blockquotes
    if tag == 'blockquote':
        text = element.get_text(strip=True)
        lines = text.split('\n')
        quoted = '\n'.join(f"> {line}" for line in lines)
        return f"\n{quoted}\n"

    # Lists
    if tag == 'ul':
        items = []
        for li in element.find_all('li', recursive=False):
            item_text = process_inline_elements(li)
            items.append(f"- {item_text}")
        return "\n" + "\n".join(items) + "\n"

    if tag == 'ol':
        items = []
        for i, li in enumerate(element.find_all('li', recursive=False), 1):
            item_text = process_inline_elements(li)
            items.append(f"{i}. {item_text}")
        return "\n" + "\n".join(items) + "\n"

    # Images
    if tag == 'img':
        src = element.get('src', '')
        alt = element.get('alt', 'image')
        if src:
            return f"\n![{alt}]({src})\n"
        return ""

    # Figure (often contains images on Medium)
    if tag == 'figure':
        img = element.find('img')
        caption = element.find('figcaption')
        result = ""
        if img:
            src = img.get('src', img.get('data-src', ''))
            alt = img.get('alt', '')
            if caption:
                alt = caption.get_text(strip=True)
            if src:
                result = f"\n![{alt}]({src})\n"
                if caption:
                    result += f"*{caption.get_text(strip=True)}*\n"
        return result

    # Links
    if tag == 'a':
        href = element.get('href', '')
        text = element.get_text(strip=True)
        if href and text:
            return f"[{text}]({href})"
        return text

    # Divs and sections - recurse into children
    if tag in ['div', 'section', 'article', 'main', 'span']:
        content = []
        for child in element.children:
            converted = convert_element_to_markdown(child)
            if converted:
                content.append(converted)
        return "".join(content)

    # Horizontal rule
    if tag == 'hr':
        return "\n---\n"

    # Bold
    if tag in ['strong', 'b']:
        text = element.get_text(strip=True)
        return f"**{text}**" if text else ""

    # Italic
    if tag in ['em', 'i']:
        text = element.get_text(strip=True)
        return f"*{text}*" if text else ""

    # Default: just get text content
    return element.get_text(strip=True)


def process_inline_elements(element) -> str:
    """Process inline elements (bold, italic, links, code) within a block."""
    if element.name is None:
        return str(element)

    result = []
    for child in element.children:
        if child.name is None:
            result.append(str(child))
        elif child.name == 'a':
            href = child.get('href', '')
            text = child.get_text()
            if href:
                result.append(f"[{text}]({href})")
            else:
                result.append(text)
        elif child.name in ['strong', 'b']:
            result.append(f"**{child.get_text()}**")
        elif child.name in ['em', 'i']:
            result.append(f"*{child.get_text()}*")
        elif child.name == 'code':
            result.append(f"`{child.get_text()}`")
        elif child.name == 'br':
            result.append("\n")
        else:
            result.append(process_inline_elements(child))

    return "".join(result)


def convert_to_markdown(article_data: dict) -> str:
    """Convert extracted article data to markdown."""
    md_parts = []

    # Frontmatter
    md_parts.append("---")
    md_parts.append(f"title: \"{article_data['title']}\"")
    if article_data['author']:
        md_parts.append(f"author: \"{article_data['author']}\"")
    if article_data['date']:
        md_parts.append(f"date: \"{article_data['date']}\"")
    md_parts.append(f"source: \"{article_data['source_url']}\"")
    md_parts.append("---")
    md_parts.append("")

    # Title as H1
    if article_data['title']:
        md_parts.append(f"# {article_data['title']}")
        md_parts.append("")

    # Convert article content
    if article_data['article_soup']:
        # Remove the first H1 if it matches the title (avoid duplication)
        first_h1 = article_data['article_soup'].find('h1')
        if first_h1 and first_h1.get_text(strip=True) == article_data['title']:
            first_h1.decompose()

        content = convert_element_to_markdown(article_data['article_soup'])

        # Clean up excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        md_parts.append(content)

    return "\n".join(md_parts)


def generate_filename(title: str) -> str:
    """Generate a safe filename from article title."""
    if not title:
        return "article.md"

    # Convert to lowercase and replace spaces with hyphens
    filename = title.lower()
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[\s_]+', '-', filename)
    filename = re.sub(r'-+', '-', filename)
    filename = filename.strip('-')

    return f"{filename[:60]}.md"


def load_html_from_file(filepath: str) -> str:
    """Load HTML content from a local file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(
        description='Convert Medium articles to GitHub-flavored Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://medium.com/@user/article-title-abc123
  %(prog)s https://medium.com/@user/article-title-abc123 output.md
  %(prog)s --file saved_article.html
  %(prog)s --file saved_article.html --output my-article.md

If you encounter network issues, save the Medium page in your browser
(Ctrl+S / Cmd+S) and use the --file option.
        """
    )

    parser.add_argument('url', nargs='?', help='Medium article URL')
    parser.add_argument('--file', '-f', dest='html_file',
                        help='Path to locally saved HTML file')
    parser.add_argument('--output', '-o', dest='output_file',
                        help='Output markdown filename')
    parser.add_argument('--source-url', dest='source_url',
                        help='Original URL (used with --file for frontmatter)')

    args = parser.parse_args()

    # Validate arguments
    if not args.url and not args.html_file:
        parser.print_help()
        print("\nError: Please provide a URL or use --file with a local HTML file")
        sys.exit(1)

    if args.url and args.html_file:
        print("Warning: Both URL and --file provided. Using --file.")

    try:
        # Load HTML content
        if args.html_file:
            if not os.path.exists(args.html_file):
                print(f"Error: File not found: {args.html_file}")
                sys.exit(1)

            print(f"Loading HTML from: {args.html_file}")
            html = load_html_from_file(args.html_file)
            source_url = args.source_url or args.html_file
            print("HTML loaded successfully!")
        else:
            if not REQUESTS_AVAILABLE:
                print("Error: 'requests' library not installed.")
                print("Install with: pip install requests")
                print("Or save the page as HTML and use: --file saved_page.html")
                sys.exit(1)

            url = args.url
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url

            if 'medium.com' not in url and 'towardsdatascience.com' not in url:
                print("Warning: URL doesn't appear to be from Medium. Proceeding anyway...")

            print(f"Fetching article from: {url}")
            html = fetch_medium_article(url)
            source_url = url
            print("Article fetched successfully!")

        print("Extracting content...")
        article_data = extract_article_content(html, source_url)

        print(f"Title: {article_data['title']}")
        print(f"Author: {article_data['author']}")

        print("Converting to markdown...")
        markdown = convert_to_markdown(article_data)

        # Determine output filename
        if args.output_file:
            output_file = args.output_file
        else:
            output_file = generate_filename(article_data['title'])

        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"\nSuccess! Markdown saved to: {output_file}")
        print(f"File size: {len(markdown)} characters")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
