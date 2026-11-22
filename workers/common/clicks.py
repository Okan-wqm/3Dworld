"""Parsing and validation of object-selection clicks (model-free, unit-tested).

A click spec is `X,Y` (starts a new object) or `X,Y,+` / `X,Y,-` (adds a positive /
negative refinement click to the previous object). Coordinates are pixels of the
resized working image.
"""

from __future__ import annotations

Click = tuple[float, float, bool]  # x, y, positive


class ClickError(ValueError):
    pass


def parse_clicks(specs: list[str]) -> list[list[Click]]:
    """One list of clicks per object, in the order given. Raises `ClickError` on any
    malformed spec instead of guessing."""
    objects: list[list[Click]] = []
    for spec in specs:
        parts = spec.split(",")
        if len(parts) not in (2, 3):
            raise ClickError(f"click {spec!r}: expected X,Y or X,Y,+ or X,Y,-")
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            raise ClickError(f"click {spec!r}: X and Y must be numbers") from None
        if len(parts) == 2:
            objects.append([(x, y, True)])
            continue
        sign = parts[2].strip()
        if sign not in ("+", "-"):
            raise ClickError(f"click {spec!r}: refinement sign must be + or -")
        if not objects:
            raise ClickError(f"click {spec!r}: a refinement click needs an object before it")
        objects[-1].append((x, y, sign == "+"))
    return objects


def check_bounds(objects: list[list[Click]], width: int, height: int) -> None:
    """Raises `ClickError` if any click lies outside the image."""
    for i, clicks in enumerate(objects, 1):
        for x, y, _ in clicks:
            if not (0 <= x < width and 0 <= y < height):
                raise ClickError(
                    f"object {i}: click ({x:g}, {y:g}) is outside the {width}x{height} image"
                )


def object_id(index: int) -> str:
    """Id of the object selected by the `index`-th (1-based) click group. Ids follow the
    click order even when an object is dropped, so click k always maps to obj-k."""
    return f"obj-{index:02d}"
