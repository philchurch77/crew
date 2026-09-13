---
type: regex
pattern: 'status_code[^\n]*40[34]|40[34][^\n]*status_code|assertContains[^\n]*status_code=40[34]'
target: { source: file, path: tolerance/tests.py }
---
