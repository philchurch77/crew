---
type: regex
pattern: '\?pupil=|["'']pupil["'']\s*:\s*[^}\n]*pk|pupil_id\s*=|["'']pupil["'']\s*:\s*[^}\n]*\.id'
target: { source: file, path: tolerance/tests.py }
weight: 2
---
