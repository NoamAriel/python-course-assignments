"""hebrew_date.py

Provides a simple function to convert a Gregorian date to a Hebrew date.
Uses the `convertdate` package if available.

Function:
- gregorian_to_hebrew(year, month, day) -> dict with keys: year, month, day, month_name, formatted

Also provides a small CLI when run as __main__.
"""
from typing import Tuple, Dict

try:
    from convertdate import hebrew, jd
except Exception as e:
    hebrew = None
    jd = None

HEBREW_MONTH_NAMES = [
    "Nisan",
    "Iyar",
    "Sivan",
    "Tamuz",
    "Av",
    "Elul",
    "Tishri",
    "Cheshvan",
    "Kislev",
    "Tevet",
    "Shevat",
    "Adar",
    "Adar II"
]

def gregorian_to_hebrew(year: int, month: int, day: int) -> Dict[str, object]:
    """Convert a Gregorian date to a Hebrew date.

    Returns a dict with:
      - year (int)
      - month (int, 1-based Hebrew month index)
      - day (int)
      - month_name (str)
      - formatted (str) e.g. '5 Nisan 5785'

    This function requires the `convertdate` package. If the package is not
    installed, it raises ImportError.
    """
    if hebrew is None or jd is None:
        raise ImportError("This function requires the 'convertdate' package. Install with: pip install convertdate")

    # convert Gregorian to Julian day then to Hebrew
    j = jd.from_gregorian(year, month, day)
    h_year, h_month, h_day = hebrew.from_jd(j)

    # convert month index into a name
    # Note: convertdate returns months as numbers 1..13 where Adar II is 13 in leap years
    # We'll map 1..13 to readable names; for Adar (non-leap) the month returned will be 12.
    if h_month == 13:
        month_name = "Adar II"
    else:
        # map typical months; adjust index because our list starts at Nisan (1)
        # The convertdate hebrew month numbers: 1=Nisan ... 6=Elul, 7=Tishri ... 12=Adar (or Adar I in leap years), 13=Adar II
        # Our HEBREW_MONTH_NAMES is aligned so index-1 is correct for 1..13 except Adar II handled above
        month_name = HEBREW_MONTH_NAMES[h_month - 1]

    formatted = f"{h_day} {month_name} {h_year}"

    return {
        "year": int(h_year),
        "month": int(h_month),
        "day": int(h_day),
        "month_name": month_name,
        "formatted": formatted,
    }


def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="Convert Gregorian date to Hebrew date")
    parser.add_argument("year", type=int, nargs="?", help="Gregorian year")
    parser.add_argument("month", type=int, nargs="?", help="Gregorian month (1-12)")
    parser.add_argument("day", type=int, nargs="?", help="Gregorian day (1-31)")
    parser.add_argument("--mode", choices=["cli", "interactive", "gui"], default="cli",
                        help="Interface mode: cli (default), interactive (prompts), gui (Tkinter)")
    args = parser.parse_args()

    mode = args.mode
    if mode == "interactive":
        interactive_input()
        return
    if mode == "gui":
        run_gui()
        return

    # CLI mode: require year/month/day as positional args
    if args.year is None or args.month is None or args.day is None:
        parser.error("year month day are required in cli mode")

    try:
        res = gregorian_to_hebrew(args.year, args.month, args.day)
    except ImportError as e:
        print(str(e))
        print("Install with: python -m pip install convertdate")
        raise

    print(res["formatted"])


def interactive_input() -> None:
    """Prompt the user for a Gregorian date using input() and print the Hebrew date.

    This function is useful when running the script in a REPL or when the
    user wants to type the date interactively.
    """
    try:
        y = int(input("Enter Gregorian year (e.g. 2025): ").strip())
        m = int(input("Enter Gregorian month (1-12): ").strip())
        d = int(input("Enter Gregorian day (1-31): ").strip())
    except ValueError:
        print("Invalid input — please enter integer values for year, month and day")
        return

    try:
        res = gregorian_to_hebrew(y, m, d)
    except ImportError as e:
        print(str(e))
        print("Install with: python -m pip install convertdate")
        return

    print(res["formatted"])


def run_gui() -> None:
    """Run a tiny Tkinter GUI to enter a Gregorian date and display the Hebrew date.

    The GUI is intentionally minimal: three entry fields and a button to convert.
    """
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception:
        print("Tkinter is not available on this system. The GUI cannot be started.")
        return

    def on_convert():
        try:
            y = int(year_var.get())
            m = int(month_var.get())
            d = int(day_var.get())
        except ValueError:
            messagebox.showerror("Input error", "Please enter valid integers for year, month and day")
            return

        try:
            res = gregorian_to_hebrew(y, m, d)
        except ImportError:
            messagebox.showerror("Missing dependency", "Please install 'convertdate' (pip install convertdate)")
            return
        except Exception as exc:
            messagebox.showerror("Conversion error", str(exc))
            return

        result_var.set(res["formatted"])

    root = tk.Tk()
    root.title("Gregorian → Hebrew date")

    frm = ttk.Frame(root, padding=12)
    frm.grid()

    ttk.Label(frm, text="Year:").grid(column=0, row=0, sticky="e")
    year_var = tk.StringVar(value=str(2025))
    ttk.Entry(frm, textvariable=year_var, width=10).grid(column=1, row=0)

    ttk.Label(frm, text="Month:").grid(column=0, row=1, sticky="e")
    month_var = tk.StringVar(value=str(11))
    ttk.Entry(frm, textvariable=month_var, width=10).grid(column=1, row=1)

    ttk.Label(frm, text="Day:").grid(column=0, row=2, sticky="e")
    day_var = tk.StringVar(value=str(7))
    ttk.Entry(frm, textvariable=day_var, width=10).grid(column=1, row=2)

    ttk.Button(frm, text="Convert", command=on_convert).grid(column=0, row=3, columnspan=2, pady=8)

    result_var = tk.StringVar(value="")
    ttk.Label(frm, textvariable=result_var, foreground="blue").grid(column=0, row=4, columnspan=2)

    root.mainloop()


if __name__ == "__main__":
    _cli()