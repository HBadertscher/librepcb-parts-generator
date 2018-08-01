"""
Generate pin header and socket strip packages.

             +---+- width
             v   v
             +---+ <-+
             |   |   | top
          +->| O | <-+
  spacing |  |(…)|
          +->| O |
             |   |
             +---+

"""
from datetime import datetime
from os import path, makedirs
from typing import Callable, List, Tuple
from uuid import uuid4

import common

generator = 'librepcb-parts-generator (generate_connectors.py)'

width = 2.54
spacing = 2.54
pad_drill = 1.0
pad_size = (2.54, 1.27 * 1.25)
line_width = 0.25
text_height = 1.0


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_connectors.csv'
uuid_cache = common.init_cache(uuid_cache_file)


def now() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def uuid(kind: str, typ: str, pin_number: int, identifier: str = None) -> str:
    if identifier:
        key = '{}-{}-1x{}-{}'.format(kind, typ, pin_number, identifier).lower().replace(' ', '~')
    else:
        key = '{}-{}-1x{}'.format(kind, typ, pin_number).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, spacing: float):
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned.

    The pin number is 1 index based.

    """
    mid = (pin_count + 1) // 2
    return -round(pin_number * spacing - mid * spacing, 2)


def get_rectangle_bounds(pin_count: int, spacing: float, top_offset: float) -> Tuple[float, float]:
    """
    Return (y_max/y_min) of the rectangle around the pins.
    """
    even = pin_count % 2 == 0
    offset = spacing / 2 if even else 0
    height = (pin_count - 1) / 2 * spacing + top_offset
    return (height - offset, -height - offset)


def generate(
    dirpath: str,
    name: str,
    name_lower: str,
    kind: str,
    pkgcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
    top_offset: float,
    generate_silkscreen: Callable[[List[str], str, int, float], None]
):
    for i in range(min_pads, max_pads + 1):
        lines = []

        pkg_uuid = uuid(kind, 'pkg', i)

        # General info
        lines.append('(librepcb_package {}'.format(pkg_uuid))
        lines.append(' (name "{} 1x{}")'.format(name, i))
        lines.append(' (description "A 1x{} {} with {}mm pin spacing.\\n\\n'
                     'Generated with {}")'.format(name_lower, i, spacing, generator))
        lines.append(' (keywords "connector, 1x{}, {}")'.format(i, keywords))
        lines.append(' (author "LibrePCB")')
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        pad_uuids = [uuid(kind, 'pad', i, str(p)) for p in range(i)]
        for j in range(1, i + 1):
            lines.append(' (pad {} (name "{}"))'.format(pad_uuids[j - 1], j))
        lines.append(' (footprint {}'.format(uuid(kind, 'footprint', i, 'default')))
        lines.append('  (name "default")')
        lines.append('  (description "")')

        # Pads
        for j in range(1, i + 1):
            y = get_y(j, i, spacing)
            shape = 'rect' if j == 1 else 'round'
            lines.append('  (pad {} (side tht) (shape {})'.format(pad_uuids[j - 1], shape))
            lines.append('   (pos 0.0 {}) (rot 0.0) (size {} {}) (drill {})'.format(
                y, pad_size[0], pad_size[1], pad_drill,
            ))
            lines.append('  )')

        # Silkscreen
        generate_silkscreen(lines, kind, i, top_offset)

        # Labels
        y_max, y_min = get_rectangle_bounds(i, spacing, top_offset + 1.27)
        text_attrs = '(height {}) (stroke_width 0.2) ' \
                     '(letter_spacing auto) (line_spacing auto)'.format(text_height)
        lines.append('  (stroke_text {} (layer top_names)'.format(uuid(kind, 'label-name', i)))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center bottom) (pos 0.0 {}) (rot 0.0) (auto_rotate true)'.format(
            y_max,
        ))
        lines.append('   (mirror false) (value "{{NAME}}")')
        lines.append('  )')
        lines.append('  (stroke_text {} (layer top_values)'.format(uuid(kind, 'label-value', i)))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center top) (pos 0.0 {}) (rot 0.0) (auto_rotate true)'.format(
            y_min,
        ))
        lines.append('   (mirror false) (value "{{VALUE}}")')
        lines.append('  )')

        lines.append(' )')
        lines.append(')')

        pkg_dir_path = path.join(dirpath, pkg_uuid)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('1x{}: Wrote package {}'.format(i, pkg_uuid))


def generate_silkscreen_female(
    lines: List[str],
    kind: str,
    pin_count: int,
    top_offset: float,
) -> None:
    lines.append('  (polygon {} (layer top_placement)'.format(
        uuid(kind, 'polygon', pin_count, 'contour')
    ))
    lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
    y_max, y_min = get_rectangle_bounds(pin_count, spacing, top_offset)
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y_min))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_min))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('  )')


def generate_silkscreen_male(
    lines: List[str],
    kind: str,
    pin_count: int,
    top_offset: float,
) -> None:
    offset = spacing / 2

    # Start in left bottom corner, go around the pads clockwise
    lines.append('  (polygon {} (layer top_placement)'.format(
        uuid(kind, 'polygon', pin_count, 'contour')
    ))
    lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
    steps = pin_count // 2
    # Up on the left
    for pin in range(-steps, steps + (pin_count % 2)):
        # Up on the left
        base_y = pin * 2.54 - offset
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(base_y + 0.27))
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(base_y + 2.27))
        lines.append('   (vertex (pos -1 {}) (angle 0.0))'.format(base_y + 2.54))
    for pin in reversed(range(-steps, steps + (pin_count % 2))):
        # Down on the right
        base_y = pin * 2.54 - offset
        lines.append('   (vertex (pos 1.0 {}) (angle 0.0))'.format(base_y + 2.54))
        lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(base_y + 2.27))
        lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(base_y + 0.27))
    # Back to start
    bottom_y = -steps * 2.54 - offset
    lines.append('   (vertex (pos 1.0 {}) (angle 0.0))'.format(bottom_y))
    lines.append('   (vertex (pos -1.0 {}) (angle 0.0))'.format(bottom_y))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(bottom_y + 0.27))
    lines.append('  )')


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/connectors')
    _make('out/connectors/pkg')
    generate(
        dirpath='out/connectors/pkg',
        name='Socket Strip 2.54mm',
        name_lower='female socket strip',
        kind='socketstrip',
        pkgcat='3fe529fe-b8b1-489b-beae-da54e01c9b20',
        keywords='socket strip, female header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.5,
        generate_silkscreen=generate_silkscreen_female,
    )
    generate(
        dirpath='out/connectors/pkg',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind='pinheader',
        pkgcat='f8be0636-474e-41ea-8340-05caf137596c',
        keywords='pin header, male header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.27,
        generate_silkscreen=generate_silkscreen_male,
    )
    generate(
        dirpath='out/connectors/pkg',
        name='Soldered Wire Connector',
        name_lower='soldered wire connecto',
        kind='wireconnector',
        pkgcat='f8be0636-474e-41ea-8340-05caf137596c',
        keywords='generic connector, soldered wire connector, tht',
        min_pads=1,
        max_pads=10,
        top_offset=1.5,
        generate_silkscreen=generate_silkscreen_female,
    )
    common.save_cache(uuid_cache_file, uuid_cache)
