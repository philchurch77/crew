#!/usr/bin/env bash
exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/_fixture/seed.sh" --with-django
