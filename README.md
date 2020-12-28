# Hackable imposition

Perform an imposition on the PDF file given in argument.


# Description

## Imposition

Imposition consists in the arrangement of the printed product’s pages on the printer’s sheet, in order to obtain faster printing, simplify binding and reduce paper waste (source: http://en.wikipedia.org/wiki/Imposition).

## Printing

    |-------------------------------------------------------------------------------
    |                                  EXT
    |    |------------------------------------------------------------------------
    |    |   O     |       O|          DEC         |O       |       0      |
    |    |    |--------------------------------------------------|    |---------
    |    |    |                        INT                       |    |
    |    | -- |    |----------------------------------------|    | -- |    |---
    |    |    |    |OVERFLOW|           |          |OVERFLOW|    |    |    |
    |    |    |    | MARGIN |    P..    |    P..   | MARGIN |    |    |    |
    |    |    |    |        |           |          |        |    |    |    |
    |    | -- |    |----------------------------------------|    | -- |    |-
    |    |    |                   cellule   INT                  |    |
    |    |    |--------------------------------------------------|    |------
    |    |   O     |       O|          DEC         |O       |       0
    |    |    |--------------------------------------------------|    |---
    |    |    |                        INT
    |    |
    |


## Install

    python3 -m pip install --user --upgrade setuptools wheel
    python3 setup.py sdist bdist_wheel
    pip install dist/hackimposition*.whl

## Use

    hackimposition --help
