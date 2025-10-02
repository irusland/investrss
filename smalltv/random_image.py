import datetime
import random
from pathlib import Path

from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle


def generate_image():
    # Dark theme + larger fonts
    plt.style.use("dark_background")
    plt.rcParams.update(
        {
            "font.size": 14,  # base font size
            "axes.titlesize": 28,  # title
            "axes.labelsize": 24,  # x/y labels
            "xtick.labelsize": 20,  # x tick labels
            "ytick.labelsize": 20,  # y tick labels
        }
    )

    time_now = datetime.datetime.now()
    dates = [time_now - datetime.timedelta(days=9 - i) for i in range(10)]
    ohlc = []
    for date in dates:
        o = random.uniform(100, 200)
        c = o + random.uniform(-10, 10)
        h = max(o, c) + random.uniform(0, 5)
        l = min(o, c) - random.uniform(0, 5)
        ohlc.append((date, o, h, l, c))

    # Create a high-res figure
    fig, ax = plt.subplots(dpi=300)
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    width = 0.6
    for idx, (d, o, h, l, c) in enumerate(ohlc):
        ax.plot([idx, idx], [l, h], color="lightgray", linewidth=1)
        bottom = o if c >= o else c
        height = abs(c - o)
        color = "lime" if c >= o else "crimson"
        bar = Rectangle(
            (idx - width / 2, bottom),
            width,
            height,
            facecolor=color,
            edgecolor="white",
            linewidth=0.5,
        )
        ax.add_patch(bar)

    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(
        [d.strftime("%m-%d") for d, *_ in ohlc], rotation=45, color="white"
    )
    ax.tick_params(axis="y", colors="white")
    ax.set_title("Sample Candlestick Chart", color="white")
    ax.set_ylabel("Price", color="white")

    output_path = Path(
        f'/Users/ruslansirazhetdinov/Downloads/'
        f'plot_{time_now.strftime("%d.%m.%Y_%H:%M:%S")}.jpg'
    )
    # Save at high DPI for extra detail
    fig.savefig(
        output_path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=300
    )
    plt.close(fig)

    # Then downsample to 240×240
    img = Image.open(output_path)
    img = img.resize((240, 240), Image.LANCZOS)
    img.save(output_path, "JPEG")

    if not output_path.is_file():
        raise Exception("was not saved")
    return output_path
