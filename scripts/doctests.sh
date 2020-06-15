#!/bin/bash
set -ev
export PWD="Lib/pagebotosx"
python3 $PWD/__init__.py
python3 $PWD/osxcolor.py
python3 $PWD/errors.py
python3 $PWD/contexts/__init__.py
python3 $PWD/contexts/drawbotcontext/__init__.py
python3 $PWD/contexts/drawbotcontext/drawbotcontext.py
python3 $PWD/graphics/__init__.py
python3 $PWD/graphics/graphic.py
python3 $PWD/fonttoolbox/__init__.py
python3 $PWD/fonttoolbox/svg2drawbot.py
python3 $PWD/strings/__init__.py
python3 $PWD/strings/formattedstring.py
python3 $PWD/strings/pattern.py
python3 $PWD/strings/tryinstallfont.py
