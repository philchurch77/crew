"""Load a directory of Markdown guidance into a new Corpus version.

    python manage.py load_corpus docs/guidance --corpus-version 2026-09

Each file starts with front matter (title, source). Passages split on
'## ' headings. The new corpus becomes current; older ones are kept."""
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ...models import Corpus, Document, Passage

FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def parse(text):
    meta = {}
    m = FRONT.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    sections = []
    title, buf = "Introduction", []
    for line in text.splitlines():
        if line.startswith("## "):
            if "".join(buf).strip():
                sections.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((title, "\n".join(buf).strip()))
    return meta, sections


class Command(BaseCommand):
    help = "Load Markdown guidance documents into a new corpus version."

    def add_arguments(self, parser):
        parser.add_argument("directory")
        parser.add_argument("--corpus-version", required=True)

    @transaction.atomic
    def handle(self, directory, corpus_version, **options):
        version = corpus_version
        root = Path(directory)
        files = sorted(root.glob("**/*.md"))
        if not files:
            raise CommandError(f"no .md files under {root}")
        if Corpus.objects.filter(version=version).exists():
            raise CommandError(f"corpus {version} already exists; choose a new version")
        Corpus.objects.update(is_current=False)
        corpus = Corpus.objects.create(version=version, is_current=True)
        n = 0
        for path in files:
            meta, sections = parse(path.read_text(encoding="utf-8"))
            doc = Document.objects.create(
                corpus=corpus,
                title=meta.get("title") or path.stem,
                source=meta.get("source", ""),
                path=str(path.relative_to(root)),
            )
            for i, (section, body) in enumerate(sections):
                Passage.objects.create(document=doc, section=section[:200], position=i, text=body)
                n += 1
        self.stdout.write(f"corpus {version}: {len(files)} documents, {n} passages")
