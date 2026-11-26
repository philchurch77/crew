---
name: house-style
description: >-
  The look and layout every one of this developer's Django projects shares,
  with a reference set of stylesheets, a base template and a style guide page
  to copy from. Load BEFORE writing or changing any template, stylesheet or
  page: a new project's first page, a new screen, a form, a table, a list, a
  card, a button, navigation, a sign-in or error page, a chat or assistant
  screen, a client's colours or branding; when the developer asks for something to look right, look the
  same as their other projects, be restyled or be rebranded; and when
  reviewing how a page looks.
---

# House style

Article 7 says what a page is held to. This skill is what that looks like:
one look across every project, with only the client's colours changing. It
carries the look as files in `reference/`, which the Captain copies rather
than designs afresh. Read `reference/README.md` for how the pieces fit; the
files are the pattern, and `styleguide.html` and `styleguide_chat.html`
show every piece in use.

## The look, in one paragraph

A dark top bar in the client's colour, edge to edge, over a pale grey page.
Content in one centred column, left-aligned. White cards with a hairline
border, generous radius and the faintest shadow. One solid button per
screen in the client's primary colour; everything else outlined. Space
Grotesk for headings, Inter for everything else. Small capitals for section
labels and table headers. Calm: no gradients on text, no stripes, no heavy
borders, no colour used for decoration.

## Two layers, and only one moves

- **Brand: nine values, set per client.** The `--brand-*` block at the top
  of `tokens.css`: primary and its hover, ink, a tint and its ink, the bar,
  its links, its accent, and the focus ring. A new client is those nine
  lines, the favicon's fill and the two names. Nothing else.
- **House style: fixed.** Type, the spacing scale, radii, shadows, neutrals,
  status colours, breakpoints and every component. A project that needs
  one changed raises it with the developer; it changes here, for everyone,
  or not at all.

After any brand value changes, run `python check_contrast.py tokens.css`.
It fails on any pair under WCAG AA where the colour is used. A client's
brand colour that fails is darkened until it passes, and the developer is
told which and by how much. Never ship a failing pair.

## Rules a page keeps

1. **Tokens only.** No colour, font size, radius or shadow in a rule
   outside `tokens.css`. Gaps, margins and card padding are `--space-*`
   steps; a control's own padding is set once, in its component.
2. **Components before new CSS.** Build the page from `components.css`. A
   piece that is missing is added there once, on the tokens, and to
   `styleguide.html` in the same change. Never a page-only variant of a
   button, card, pill or table.
3. **The page shell.** `layout.html`, then `.page` (`--narrow` for a form
   or a message), a `.page__header` with the `h1`, one line of lead and the
   page's single `.btn--primary`. Sections under a `.section-label`.
4. **Nothing inline.** No `<script>`, `on*=`, `style=` or `<style>` in a
   template: the Content Security Policy blocks them. Behaviour is in
   `site.js` and reads `data-` attributes; state is `aria-expanded` and
   `aria-current`, which the stylesheet reads.
5. **Nothing remote.** Fonts are self-hosted with their licences. No CDN,
   no CSS framework, no icon font. An icon is an inline SVG at
   `stroke="currentColor"`, `aria-hidden` when a word sits beside it.
6. **Reachable and readable.** Anything pressed is at least `--hit` (44px).
   Focus is the one global ring; never remove it without drawing it
   elsewhere. Status is a word in a `.pill` or a sentence in a `.notice`,
   never colour alone. A table sits in a labelled, focusable
   `.table-scroll`, figures right-aligned.
7. **Two widths.** 768px, where the nav folds and columns stack (also in
   `site.js`), and 480px, where the wordmark hides. Never a sideways
   scroll at 320px.
8. **Words.** Sentence case. A button says what it does ("Save report").
   An error says what to do next. An empty state says what will be there
   and offers the way to put it there.

## The assistant screen

A project with a chat extends `chat.html` and loads `chat.css` and
`chat.js` on that page only. Three columns under the bar: history, the
conversation at one reading width, and what the assistant looked up. Its
widths are its own: Sources is a drawer below 1101px, History below 901px,
and at 640px Send takes its own row.

- The assistant's reply sits on the page under its mark and name; the
  person's turn is a tinted bubble on the right. A turn built by script
  has the markup `styleguide_chat.html` shows.
- An empty chat is a greeting, one line saying this is an AI, and at most
  four starter cards that fill the box and never send.
- The composer is one card: a standing note saying what not to type, the
  box, Send. Every chat says it is an AI, in the header or the greeting.
- Nothing a person typed goes in an attribute, a URL or the page title.

This is the look only. Sending, streaming, storing and what reaches the
model are article 13 and the `ai-features` skill's chat reference, which
fills this screen in.

## What the Captain does with it

- **New project.** The `new-project` skill's starter first, then
  `reference/static/` and `reference/templates/` on top; set the brand
  block and run the contrast check. Then build pages.
- **Existing project.** Do not restyle uninvited. Bringing a project onto
  the house style is charted: tokens first, then the shell, then a page per
  leg.
- **Build.** A plan that adds a page names the components it uses. Then
  `python look.py <path>` and read the screenshots it saves, at both
  widths, beside the style guide's.
- **Lookout.** Runs `look.py` on every page the change touched and reads
  the screenshots: a finding is something seen there or a rule above
  broken, never taste. A hard-coded value, a second primary button, a
  component rebuilt locally and a failing contrast pair are each one.

## What this skill does not do

It has no charts or dashboard layout: those are built on the same tokens
when a project needs one and join the reference once proven there. It does
not theme the Django admin. It has no dark theme.
