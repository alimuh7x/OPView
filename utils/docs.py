"""
Documentation rendering utilities for OPView.

Provides functionality to render the Documentation.md file as HTML.
"""

from pathlib import Path
import markdown
from flask import render_template_string


DOCUMENTATION_FILE = Path("assets/Documentation.md")


def render_docs():
    """
    Render the Documentation.md file as HTML with table of contents.

    Returns:
        HTML string containing the rendered documentation page
    """
    if not DOCUMENTATION_FILE.exists():
        return render_template_string(
            "<h1>Documentation</h1><p>Documentation file not found.</p>"
        )
    content = DOCUMENTATION_FILE.read_text(encoding='utf-8')
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc'])
    html_body = md.convert(content)
    toc_html = md.toc
    template = """
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenPhase Documentation</title>
        <link rel="stylesheet" href="/assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { background: var(--bg-gradient); }
            .doc-article {
                background: var(--surface);
                border-radius: 18px;
                padding: 32px 40px;
                box-shadow: var(--shadow-lg);
                line-height: 1.7;
                color: var(--text-main);
                word-wrap: break-word;
            }
            .doc-article h1, .doc-article h2, .doc-article h3 {
                color: #183568;
            }
            .doc-article pre {
                background: #0d2244;
                color: #fff;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
            }
            .doc-article code {
                color: #c50623;
            }
            .doc-sidebar .sidebar-tabs {
                overflow: visible;
            }
            .doc-sidebar .toc {
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .doc-sidebar .toc ul {
                list-style: none;
                padding-left: 16px;
                margin-top: 6px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .doc-sidebar .toc a {
                color: rgba(255,255,255,0.75);
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                display: block;
                padding: 8px 12px;
                border-radius: 12px;
                transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
            }
            .doc-sidebar .toc a:hover {
                color: #fff;
                background: rgba(255,255,255,0.1);
            }
            .doc-sidebar .toc a.active {
                color: #fff;
                background: rgba(255,255,255,0.15);
                box-shadow: inset 3px 0 0 #c50623;
            }
            .doc-main {
                max-width: 1080px;
                width: 100%;
                margin: 0 auto;
            }
            /* Ensure doc header logo matches main app sizing */
            .app-logo {
                width: 42px;
                height: 42px;
                object-fit: contain;
            }
        </style>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    <body>
        <div id="app-container">
            <div class="app-header">
                <div class="top-bar">
                    <div class="top-left">
                        <img src="/assets/OP_Logo_main.png" class="app-logo" alt="OP logo">
                        <h1 class="app-title">OPV<span class="app-title-sub">iew</span></h1>
                    </div>
                    <div class="top-right">
                        <a class="doc-link" href="/">Back to App</a>
                    </div>
                </div>
            </div>
            <div class="layout-shell">
                <div class="sidebar doc-sidebar" style="position: sticky; top: 0; max-height: 100vh; overflow-y: auto; width: 280px;">
                    <span class="sidebar-title">Contents</span>
                    <div class="sidebar-tabs">
                        {{ toc|safe }}
                    </div>
                </div>
                <div class="main-panel">
                    <div class="doc-main">
                        <article class="doc-article">
                            {{ body|safe }}
                        </article>
                    </div>
                </div>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const tocLinks = Array.from(document.querySelectorAll('.doc-sidebar .toc a'));
                if (!tocLinks.length) {
                    return;
                }
                const headingMap = tocLinks.map(link => {
                    const hash = decodeURIComponent(link.hash || '').replace('#', '');
                    const target = document.getElementById(hash);
                    return { link, target };
                }).filter(item => item.target);

                function setActive(link) {
                    tocLinks.forEach(l => l.classList.remove('active'));
                    if (link) {
                        link.classList.add('active');
                    }
                }

                tocLinks.forEach(link => {
                    link.addEventListener('click', () => setActive(link));
                });

                const observer = new IntersectionObserver((entries) => {
                    const visible = entries
                        .filter(entry => entry.isIntersecting)
                        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
                    if (visible.length > 0) {
                        const match = headingMap.find(item => item.target === visible[0].target);
                        if (match) {
                            setActive(match.link);
                        }
                    }
                }, {
                    rootMargin: '-150px 0px -60% 0px',
                    threshold: [0.2, 0.4, 0.6]
                });

                headingMap.forEach(item => observer.observe(item.target));

                // highlight first item initially
                setActive(tocLinks[0]);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(template, body=html_body, toc=toc_html)
