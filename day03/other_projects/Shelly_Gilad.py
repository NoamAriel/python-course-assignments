#!/usr/bin/env python3
# PCR genotyping calculator for DDW, Mix (2X/5X), and primers by sample count.
import argparse
import sys

PER_SAMPLE_TOTAL = 11.0  # total reaction volume per sample (µL)
PRIMER_PER = 0.5         # each primer per sample (µL)
DEFAULT_EXCESS = 10.0    # default excess (%)

def round_to_half(x: float) -> float:
    return round(x * 2) / 2.0

def per_sample_volumes(mix_x: int):
    """
    Compute per-sample volumes that preserve the same final composition
    as 6 µL of 2X mix in an 11 µL reaction.
    """
    if mix_x not in (2, 5):
        raise ValueError("mix_x must be 2 or 5")
    mix_vol = 6.0 * (2.0 / mix_x)         # µL per sample for chosen X
    primers_total = 2 * PRIMER_PER        # 1.0 µL
    ddw_vol = PER_SAMPLE_TOTAL - (mix_vol + primers_total)
    if ddw_vol < 0:
        raise ValueError("Computed DDW volume is negative; check inputs.")
    # return in a fixed order
    return {
        "DDW (µL)": ddw_vol,
        f"Mix {mix_x}X (µL)": mix_vol,
        "Primer F (µL)": PRIMER_PER,
        "Primer R (µL)": PRIMER_PER,
    }

def compute_totals(n_samples: int, excess_percent: float, mix_x: int):
    per = per_sample_volumes(mix_x)
    factor = 1.0 + (excess_percent / 100.0)
    totals = {k: round_to_half(v * n_samples * factor) for k, v in per.items()}
    total_master_mix = round_to_half(sum(totals.values()))
    return per, totals, total_master_mix

def as_table(n_samples, excess, mix_x, per, totals, total_master_mix):
    lines = []
    lines.append(f"Samples: {n_samples} | Excess: {excess:.1f}% | Mix: {mix_x}X")
    lines.append(f"Per-sample total volume: {PER_SAMPLE_TOTAL:.1f} µL")
    lines.append("-" * 46)
    lines.append("Per-sample recipe:")
    for k, v in per.items():
        lines.append(f"  {k:<16} = {v:.1f} µL")
    lines.append("-" * 46)
    lines.append("Totals to prepare (rounded to 0.5 µL):")
    for k in per.keys():
        lines.append(f"  {k:<16} = {totals[k]:.1f} µL")
    lines.append("-" * 46)
    lines.append(f"TOTAL master mix       = {total_master_mix:.1f} µL")
    return "\n".join(lines)

def try_int_positive(x, name="value"):
    try:
        xv = int(x)
        if xv < 1:
            raise ValueError
        return xv
    except Exception:
        print(f"Error: {name} must be a positive integer.", file=sys.stderr)
        sys.exit(2)

def try_nonneg_float(x, name="value"):
    try:
        xv = float(x)
        if xv < 0:
            raise ValueError
        return xv
    except Exception:
        print(f"Error: {name} must be a non-negative number.", file=sys.stderr)
        sys.exit(2)

def run_cli(samples: int, excess: float, mix_x: int):
    per, totals, total_master_mix = compute_totals(samples, excess, mix_x)
    print(as_table(samples, excess, mix_x, per, totals, total_master_mix))

def interactive_prompt(excess_default: float, mix_default: int):
    raw = input("Enter number of PCR samples: ").strip()
    n = try_int_positive(raw, "samples")
    raw_ex = input(f"Excess % (ENTER for {excess_default}%): ").strip()
    ex = excess_default if raw_ex == "" else try_nonneg_float(raw_ex, "excess")
    raw_mx = input(f"Mix concentration (2 or 5) [ENTER for {mix_default}]: ").strip()
    mx = mix_default if raw_mx == "" else try_int_positive(raw_mx, "mix")
    if mx not in (2, 5):
        print("Error: mix must be 2 or 5.", file=sys.stderr)
        sys.exit(2)
    run_cli(n, ex, mx)

def main():
    parser = argparse.ArgumentParser(
        description="PCR genotyping calculator for DDW, Mix (2X/5X), and primers by sample count."
    )
    parser.add_argument("--samples", "-n", type=int, help="Number of PCR samples.")
    parser.add_argument("--excess", "-e", type=float, default=DEFAULT_EXCESS,
                        help=f"Excess %% for pipetting loss (default {DEFAULT_EXCESS}).")
    parser.add_argument("--mix", "-m", type=int, choices=[2, 5], default=2,
                        help="Mix concentration (2 or 5). Default 2.")
    parser.add_argument("--no-gui", action="store_true",
                        help="Run in terminal (no GUI). If --samples not given, you’ll be prompted.")
    args = parser.parse_args()

    # Terminal mode
    if args.no_gui:
        if args.samples is not None:
            run_cli(try_int_positive(args.samples, "samples"),
                    try_nonneg_float(args.excess, "excess"),
                    args.mix)
        else:
            interactive_prompt(excess_default=max(args.excess, 0.0), mix_default=args.mix)
        return

    # GUI mode
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception:
        # Fallback to CLI if tkinter unavailable
        if args.samples is not None:
            run_cli(try_int_positive(args.samples, "samples"),
                    try_nonneg_float(args.excess, "excess"),
                    args.mix)
        else:
            interactive_prompt(excess_default=max(args.excess, 0.0), mix_default=args.mix)
        return

    root = tk.Tk()
    root.title("PCR Genotyping Calculator")

    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Samples input (Spinbox + Slider)
    ttk.Label(frm, text="Number of samples:").grid(row=0, column=0, sticky="w")
    samples_var = tk.IntVar(value=args.samples if args.samples and args.samples > 0 else 8)
    spn = ttk.Spinbox(frm, from_=1, to=999, textvariable=samples_var, width=8)
    spn.grid(row=0, column=1, sticky="w", padx=(8, 0))
    sld = ttk.Scale(frm, from_=1, to=96, orient="horizontal",
                    command=lambda v: samples_var.set(int(float(v))))
    sld.set(samples_var.get())
    sld.grid(row=0, column=2, sticky="ew", padx=(10, 0))
    frm.columnconfigure(2, weight=1)

    # Excess % (Spinbox, default visible; 0.5% steps)
    ttk.Label(frm, text="Excess (%):").grid(row=1, column=0, sticky="w", pady=(6, 0))
    excess_var = tk.DoubleVar(value=max(args.excess, 0.0))
    ex_spn = ttk.Spinbox(frm, from_=0.0, to=100.0, increment=0.5, width=8, textvariable=excess_var)
    ex_spn.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

    # Mix concentration (2X / 5X)
    ttk.Label(frm, text="Mix concentration:").grid(row=2, column=0, sticky="w", pady=(6, 0))
    mix_var = tk.StringVar(value=f"{args.mix}X")
    mix_cmb = ttk.Combobox(frm, textvariable=mix_var, state="readonly", width=6,
                           values=["2X", "5X"])
    mix_cmb.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

    # Results display
    txt = tk.Text(frm, height=12, width=52, wrap="word")
    txt.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
    frm.rowconfigure(4, weight=1)

    # Buttons
    btns = ttk.Frame(frm)
    btns.grid(row=5, column=0, columnspan=3, sticky="e", pady=(8, 0))

    def compute_and_show():
        try:
            n = int(samples_var.get())
            if n < 1:
                raise ValueError
            ex = float(excess_var.get())
            if ex < 0:
                raise ValueError
            mix_label = mix_var.get().strip().upper()
            mx = 2 if mix_label.startswith("2") else 5
        except Exception:
            messagebox.showerror("Invalid input", "Check samples (≥1), excess (≥0), and mix (2X/5X).")
            return

        per, totals, total_mm = compute_totals(n, ex, mx)
        txt.delete("1.0", "end")
        txt.insert("1.0", as_table(n, ex, mx, per, totals, total_mm))

    def copy_clipboard():
        root.clipboard_clear()
        root.clipboard_append(txt.get("1.0", "end").strip())
        messagebox.showinfo("Copied", "Results copied to clipboard.")

    def cli_preview():
        messagebox.showinfo(
            "CLI Preview",
            "Example CLI:\n\n"
            "  python pcr_mix_calculator.py --samples 24 --excess 10 --mix 2\n"
            "  python pcr_mix_calculator.py --samples 24 --excess 10 --mix 5\n\n"
            "Interactive terminal mode:\n"
            "  python pcr_mix_calculator.py --no-gui"
        )

    ttk.Button(btns, text="Calculate", command=compute_and_show).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="Copy", command=copy_clipboard).grid(row=0, column=1, padx=4)
    ttk.Button(btns, text="CLI Examples", command=cli_preview).grid(row=0, column=2, padx=4)
    ttk.Button(btns, text="Quit", command=root.destroy).grid(row=0, column=3, padx=4)

    # Prefill
    compute_and_show()
    root.mainloop()

if __name__ == "__main__":
    main()