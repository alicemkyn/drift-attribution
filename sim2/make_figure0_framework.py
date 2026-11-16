"""Framework figure (schematic, no data): the setting, why the symmetric
attribution game is not identified, and the policy-last decomposition.

Panel a: the causal graph before and after deployment; the edge from the risk
score to the action exists only after deployment.
Panel b: the covariate plane of the simulator, split by clinical suspicion and
by the risk score; where only the alert triggers treatment there are no
treated pre-deployment patients.
Panel c: what a monitor without action logs reports against the policy-last
decomposition. Segment lengths are schematic.

Colours follow make_figures2.py: covariates blue, policy green, outcome
mechanism red.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import save_figure

CX, CP, CY, CG = "#4477AA", "#228833", "#EE6677", "#888888"   # X, policy, Y|X(,A), grey
INK = "#222222"
BASE, NOTE, SMALL = 7.5, 6.8, 6.2                              # title/identity, annotation, tick-level text


def _arrow(ax, p, q, color=INK, lw=0.9, rad=0.0, ls="-"):
    ax.annotate("", xy=q, xytext=p, zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, linestyle=ls, shrinkA=8.5, shrinkB=8.5,
                                mutation_scale=7, connectionstyle=f"arc3,rad={rad}"))


def _node(ax, x, y, label, edge=INK, ls="-", text=INK):
    ax.scatter([x], [y], s=235, facecolor="white", edgecolor=edge, linewidth=0.9, linestyle=ls, zorder=3)
    ax.text(x, y, label, ha="center", va="center", fontsize=BASE, color=text, zorder=4)


def _header(ax, letter, title):
    ax.text(-0.02, 1.045, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="bottom")
    ax.text(0.0, 1.045, "    " + title.replace("\n", "\n    "), transform=ax.transAxes, fontsize=BASE, ha="left", va="bottom", linespacing=1.15)


def panel_graph(ax):
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    xs = {"X": 0.9, "r": 3.6, "A": 6.3, "Y": 9.0}
    for y, deployed, head in ((6.6, False, r"$e_0$ before deployment: $A\sim\pi_0(a\mid x)$"),
                              (1.8, True, r"$e_1$ after deployment: $A\sim\pi_1(a\mid x,\hat r)$")):
        ax.text(0.0, y + 1.75, head, fontsize=NOTE, ha="left", va="bottom", color=INK)
        _arrow(ax, (xs["X"], y), (xs["r"], y), color=INK if deployed else CG)
        _arrow(ax, (xs["A"], y), (xs["Y"], y))
        _arrow(ax, (xs["X"], y), (xs["Y"], y), rad=-0.25)
        _arrow(ax, (xs["X"], y), (xs["A"], y), rad=0.3)
        if deployed:
            _arrow(ax, (xs["r"], y), (xs["A"], y), color=CP, lw=1.8)
            ax.text((xs["r"] + xs["A"]) / 2, y + 0.3, "alert", fontsize=NOTE, color=CP, ha="center", va="bottom")
        else:
            ax.text((xs["r"] + xs["A"]) / 2 + 0.05, y + 0.35, "no alert", fontsize=SMALL, color=CG, ha="center", va="bottom")
        _node(ax, xs["X"], y, "$X$")
        _node(ax, xs["r"], y, r"$\hat r$", edge=INK if deployed else CG, ls="-" if deployed else (0, (2, 1.5)),
              text=INK if deployed else CG)
        _node(ax, xs["A"], y, "$A$")
        _node(ax, xs["Y"], y, "$Y$")
    _header(ax, "a", "Deployment adds a mechanism\nwith no earlier counterpart")


def panel_support(ax):
    ts, tr = 0.60, 0.50
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((ts, 0), 1 - ts, 1, facecolor="#E4E4E4", edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((0, tr), ts, 1 - tr, facecolor="#DCEBDD", edgecolor=CP, hatch="////", linewidth=0.0, zorder=0))
    ax.axvline(ts, color=INK, lw=0.7); ax.plot([0, ts], [tr, tr], color=CP, lw=1.2)
    box = dict(facecolor="white", edgecolor="none", pad=1.2, alpha=0.92)
    ax.text(ts / 2, (1 + tr) / 2, "only the alert\ntriggers treatment:\n" + r"$\pi_0\approx 0,\ \pi_1>0$", fontsize=NOTE,
            ha="center", va="center", color=INK, bbox=box, linespacing=1.2)
    ax.text(ts / 2, tr / 2, "untreated in\nboth periods", fontsize=NOTE, ha="center", va="center", color=INK, linespacing=1.2)
    ax.text((1 + ts) / 2, 0.5, "treated by\nstandard\ncare", fontsize=NOTE, ha="center", va="center", color=INK, linespacing=1.2)
    ax.set_xticks([ts]); ax.set_xticklabels([r"$\tau_s$"], fontsize=SMALL)
    ax.set_yticks([tr]); ax.set_yticklabels([r"$\tau$"], fontsize=SMALL)
    ax.tick_params(length=2.5, width=0.6)
    ax.set_xlabel("clinical suspicion $s(X)$", fontsize=BASE, labelpad=2)
    ax.set_ylabel(r"risk score $\hat r=f(X)$", fontsize=BASE, labelpad=2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    _header(ax, "b", "No pre-deployment treatment\nwhere only the alert acts")


def _segment(ax, x0, x1, y0, h, color, label, hatch=None, text_box=False):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, h, facecolor=color + "55", edgecolor=color, linewidth=0.9, hatch=hatch, zorder=1))
    ax.text((x0 + x1) / 2, y0 + h / 2, label, fontsize=NOTE, ha="center", va="center", color=INK, zorder=3,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=0.9) if text_box else None)


def _bracket(ax, x0, x1, y, label, color=INK, drop=0.3):
    ax.plot([x0, x0, x1, x1], [y + drop, y, y, y + drop], color=color, lw=0.7, solid_capstyle="butt")
    ax.text((x0 + x1) / 2, y - 0.18, label, fontsize=NOTE, ha="center", va="top", color=color, linespacing=1.2)


def panel_decomposition(ax):
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    a, b, c, d, h = 0.2, 2.3, 6.0, 9.8, 1.15
    ax.annotate("", xy=(d, 9.25), xytext=(a, 9.25), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.7, shrinkA=0, shrinkB=0,
                                                                   mutation_scale=6))
    ax.text((a + d) / 2, 9.4, r"observed change in loss $\Delta R$", fontsize=NOTE, ha="center", va="bottom")
    ax.text(a, 8.1, "monitor without action logs", fontsize=BASE, ha="left", va="bottom")
    y1 = 6.75
    _segment(ax, a, b, y1, h, CX, "$P(X)$")
    _segment(ax, b, c, y1, h, CY, r"$P(Y\mid X)$")
    ax.add_patch(Rectangle((c, y1), d - c, h, facecolor=CY + "55", edgecolor=CY, linewidth=0.9, zorder=1))
    ax.add_patch(Rectangle((c, y1), d - c, h, facecolor="none", edgecolor=CP, linewidth=0.0, hatch="////", zorder=2))
    ax.text((c + d) / 2, y1 + h / 2, "alert's effect", fontsize=NOTE, ha="center", va="center", zorder=3,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=0.92))
    ax.text(a, 5.0, "proposed: policy ordered last", fontsize=BASE, ha="left", va="bottom")
    y2 = 3.65
    _segment(ax, a, b, y2, h, CX, r"$\Delta_X$")
    _segment(ax, b, c, y2, h, CY, r"$\Delta_{Y\mid X,A}$")
    _segment(ax, c, d, y2, h, CP, r"$\Delta_\pi$")
    for x in (c, d):
        ax.plot([x, x], [y2 + h, y1], color=CG, lw=0.6, ls=(0, (1, 1.5)), zorder=0)
    _bracket(ax, a, c - 0.08, y2 - 0.45, "exogenous change\n(under standard care $\\pi_0$)")
    _bracket(ax, c + 0.08, d, y2 - 0.45, "policy contrast:\nrandomised arm", color=CP)
    _header(ax, "c", "A monitor books the alert's effect to\n$P(Y\\mid X)$; policy-last ordering isolates it")


def build():
    plt.rcParams.update({"font.size": BASE, "pdf.fonttype": 42, "hatch.linewidth": 0.5, "hatch.color": CP})
    fig = plt.figure(figsize=(7.0, 2.0))
    y0, hgt = 0.18, 0.62
    panel_graph(fig.add_axes([0.012, y0, 0.283, hgt]))
    panel_support(fig.add_axes([0.378, y0, 0.212, hgt]))
    panel_decomposition(fig.add_axes([0.632, y0, 0.363, hgt]))
    return fig


def main():
    fig = build()
    save_figure(fig, "fig0_framework.pdf")
    plt.close(fig)
    print("wrote fig0_framework.pdf")


if __name__ == "__main__":
    main()
