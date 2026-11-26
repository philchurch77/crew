# Reference: the house style

The look of every project, as files. Copy `static/` and `templates/` into a
new Django project and set the client's colours; change nothing else.

```
static/css/tokens.css      every value; the Brand block is the client's
static/css/base.css        reset, fonts, type, focus ring, reduced motion, print
static/css/components.css  top bar, page, buttons, forms, cards, pills,
                           notices, tables, empty state, sign in
static/css/chat.css        the assistant screen; loaded by chat.html only
static/js/site.js          the bar's menus, and data-confirm on forms
static/js/chat.js          the chat's drawers, row menus and starter cards
static/fonts/              Inter and Space Grotesk (SIL OFL), self-hosted
static/img/favicon.svg     a tile in the primary colour
templates/layout.html      the base template every page extends
templates/partials/        form_field.html, form_errors.html
templates/styleguide.html  every component on one page, invented content
templates/chat.html        the assistant screen, as blocks to fill
templates/styleguide_chat.html  chat.html filled with an invented chat
check_contrast.py          fails a palette that is under WCAG AA
look.py                    screenshots a page at two widths and measures it
```

## A new client

1. In `tokens.css`, set the nine `--brand-*` values.

   | Token | Used for | Must pass |
   |---|---|---|
   | `--brand-primary` | buttons, links, the logo tile | 4.5:1 with white, and on the page |
   | `--brand-primary-strong` | hover | 4.5:1 with white |
   | `--brand-ink` | body text and headings | 4.5:1 on the page |
   | `--brand-tint` / `--brand-tint-ink` | the brand pill, your turn in a chat | 4.5:1 together, and ink on the tint |
   | `--brand-bar` | the top bar, the sign-in panel | 4.5:1 with white |
   | `--brand-bar-link` | resting links on the bar | 4.5:1 on the bar |
   | `--brand-bar-accent` | the current-page line | 3:1 on the bar |
   | `--brand-ring` | focus | 3:1 on white, the page and the bar |

   A client's guidelines usually give one or two colours. The primary is
   their main colour, darkened until white on it passes. The bar is their
   darkest colour, or the primary taken close to black. The tint is the
   primary at about 10% on white; its ink is the primary darkened. The
   values in the file are a teal and navy and are only the starting point.

2. `python check_contrast.py static/css/tokens.css` until it exits 0.
3. The names come from the context: `product_name` and `client_name` (the
   starter's `core.context_processors.names`), and `assistant_name` on the
   chat. In `layout.html` set the nav links, and the URL names (`home`,
   `login`, `logout`, `password_change`, and `chat` in `chat.html`) if the
   project's differ. Set the fill in `static/img/favicon.svg`.
4. Serve the style guide while `DEBUG` is on, and look at it at 1280 and
   390 wide:

   ```python
   if settings.DEBUG:
       urlpatterns += [
           path("styleguide/", TemplateView.as_view(template_name="styleguide.html")),
           path("styleguide/chat/", TemplateView.as_view(template_name="styleguide_chat.html")),
       ]
   ```

   `styleguide/chat/?empty` shows the empty chat.

## Looking at a page

```bash
python look.py /reports/ /reports/new/
```

It serves the project from Django's test database, opens each path in a
real browser at 1280 and 390 wide, saves screenshots outside the project
(and the style guide's, to compare), and prints what it measured: console
errors, sideways scroll, the number of h1s and primary buttons, small tap
targets, fields with no label. `--setup app.module.function` creates the
records a page needs. It needs `pip install playwright` and a browser
(`playwright install chromium`).

## Building a page

```django
{% extends 'layout.html' %}
{% block title %}Reports{% endblock %}
{% block content %}
<section class="page" aria-labelledby="page-heading">
    <div class="page__header">
        <div>
            <h1 id="page-heading">Reports</h1>
            <p class="page__lead">What this page holds, in a line.</p>
        </div>
        <a class="btn btn--primary" href="{% url 'report_new' %}">New report</a>
    </div>
    ...
</section>
{% endblock %}
```

A Django form is `<form class="form">` with
`{% include "partials/form_errors.html" %}` and one
`{% include "partials/form_field.html" %}` per field, then `.form__actions`.
A form that deletes carries `data-confirm="..."`.

## An assistant screen

The project's chat page extends `chat.html` and fills its blocks:

| Block | Holds |
|---|---|
| `chat_title` | the chat's title, as text |
| `chat_history` | `.chat-group`s of `.chat-row`s, the open one `.is-current` |
| `chat_about` | what the assistant can and cannot read |
| `chat_greeting`, `chat_lead`, `chat_starters` | the empty chat |
| `chat_turns` | stored turns; empty for a new chat, with no whitespace |
| `chat_actions` | header buttons beside Sources (Export) |
| `composer_note`, `composer_placeholder`, `composer_foot` | the composer |
| `chat_sources` | what was looked up, under `.section-label`s |

`chat.js` does layout only. The `ai-features` skill's chat reference is
the app that fills this screen in. A project writing its own script sends
the message, builds each turn with the markup in `styleguide_chat.html`
(`.message--user`, `.message--assistant`, `.message--status` while it
works, a `.notice` when it fails), and sets `aria-disabled` on Send while
a reply streams.

Three things in the markup are load-bearing: `#messages` has no whitespace
when empty and `.chat-empty` is its next sibling (the empty state and the
header hang on `:empty`); the box keeps a placeholder (the starter cards
hide on `:placeholder-shown`); and the box has no `<form>` and no `name`.

## Where it came from

Lifted from Ada (Anglian Learning, 2026-11) and tidied: one name per value,
a full spacing scale, flat left-aligned headings, one button and one field
shape. The chat screen is Ada's layout without her streaming, figure
checks, charts or printing, which are that project's own.
