"""Draw the five-input, three-scenario simulation workflow for the manuscript."""

from argparse import ArgumentParser
from pathlib import Path

from matplotlib.font_manager import FontProperties, findfont
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 2200, 1510
NAVY = "#17324A"
TEAL = "#176B77"
GREY = "#5A6870"
EDGE = "#9DB4BB"


def make_figure(output: Path) -> None:
    """Write a PNG and PDF using fonts bundled with Matplotlib."""
    output.mkdir(parents=True, exist_ok=True)
    regular_path = findfont(FontProperties(family="DejaVu Sans"))
    bold_path = findfont(FontProperties(family="DejaVu Sans", weight="bold"))

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(bold_path if bold else regular_path, size)

    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    def box(x0, y0, x1, y1, title, lines, fill="#EAF2F4"):
        draw.rounded_rectangle(
            (x0, y0, x1, y1), radius=24, fill=fill, outline=EDGE, width=3
        )
        draw.text((x0 + 33, y0 + 23), title, font=font(48, True), fill=NAVY)
        for index, line in enumerate(lines):
            draw.text((x0 + 33, y0 + 91 + 52 * index), line, font=font(39), fill=GREY)

    def arrow(x, y0, y1):
        draw.line([(x, y0), (x, y1)], fill=TEAL, width=11)
        draw.polygon([(x - 20, y1 - 27), (x + 20, y1 - 27), (x, y1)], fill=TEAL)

    draw.text(
        (60, 35),
        "From mapped rules to annual planning outputs",
        font=font(59, True),
        fill=NAVY,
    )
    box(
        60, 140, 1040, 390, "Spatial inputs",
        ["AGB, reserve and harvest calendar", "Elevation and watercourses"],
    )
    box(
        1160, 140, 2140, 390, "Scenarios and sampling",
        ["Buffer, slope, threshold, retention", "K and q per run; kiln yield per year"],
    )
    arrow(550, 395, 465)
    arrow(1650, 395, 465)
    box(
        60, 480, 2140, 680, "Prepare the reporting landscape",
        ["Intersect reserve and calendar masks; derive slope and water distance"],
        fill="#F4F7F8",
    )
    arrow(1100, 685, 755)
    box(
        60, 770, 2140, 1030, "Annual update for each realization",
        [
            "Scheduled and eligible cells  →  harvest wood and retain biomass",
            "Apply one-year biomass recovery; convert harvested wood to potential charcoal",
        ],
    )
    arrow(1100, 1035, 1105)
    box(
        60, 1120, 2140, 1390, "Export and summarize",
        [
            "Annual standing biomass, wood harvest and charcoal by realization",
            "Parameter draws, diagnostics, rotation means and uncertainty ranges",
        ],
        fill="#F4F7F8",
    )
    draw.text(
        (65, 1432),
        "Three scenarios  •  1,000 realizations each  •  2015–2086 in three 24-year rotations",
        font=font(36),
        fill=GREY,
    )

    path = output / "figure_workflow.png"
    canvas.save(path, optimize=True)
    canvas.save(path.with_suffix(".pdf"), "PDF", resolution=300)
    print(path)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    make_figure(parser.parse_args().output)
