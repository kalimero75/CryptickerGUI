#!/bin/python3

import ccxt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import os
import json
from PIL import Image, ImageTk

PROGRAM_TITLE = "MegaTUX-Crypticker"
CACHE_FILE = "cached_symbols.json"

headers = [
    "Symbol",
    "Preis (EUR)",
    "Volatilität (%)",
    "% Change",
    "Eröffnungspreis (EUR)",
    "Durchschnittlicher Kaufpreis (EUR)",
    "Tageshoch (EUR)",
    "Tagestief (EUR)"
]

is_running = False
update_thread = None
USDT_to_EUR = 1
search_active = False
cached_symbols = []

def get_exchange():
    """Initialize the Binance exchange with ccxt."""
    try:
        exchange = ccxt.binance()
        return exchange
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Initialisieren der Börse: {e}")
        exit()

def load_cached_symbols():
    """Load cached symbols from a file if available."""
    global cached_symbols
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached_symbols = json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden des Cache: {e}")

def save_cached_symbols(symbols):
    """Save symbols to a cache file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(symbols, f)
    except Exception as e:
        print(f"Fehler beim Speichern des Cache: {e}")

def list_all_symbols(exchange):
    """Show all available trading pairs on Binance."""
    global cached_symbols
    try:
        if not cached_symbols:
            markets = exchange.load_markets()
            cached_symbols = sorted([symbol for symbol in markets.keys() if symbol.endswith("/USDT")])
            save_cached_symbols(cached_symbols)
        return cached_symbols
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Abrufen der Symbole: {e}")
        return []

def fetch_ticker_data(exchange, symbol):
    """Fetch the ticker data for a specific symbol."""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    except Exception:
        return None

def calculate_volatility(high, low):
    """Calculate the volatility in percent based on the day's high and low."""
    if high and low:
        return (high - low) / low * 100
    return None

def calculate_percent_change(last, open_price):
    """Calculate the percentage price change."""
    if last and open_price:
        return ((last - open_price) / open_price) * 100
    return None

def update_table(exchange, selected_symbols, tree):
    """Update the table with cryptocurrency data and sort by volatility."""
    global USDT_to_EUR

    if search_active:
        return  # Skip update if search is active

    try:
        ticker = exchange.fetch_ticker("USDT/EUR")
        USDT_to_EUR = ticker['last']
    except Exception:
        USDT_to_EUR = 1

    data_list = []

    all_tickers = exchange.fetch_tickers(selected_symbols)
    
    for symbol in selected_symbols:
        ticker = all_tickers.get(symbol)
        if ticker:
            high = ticker['high'] * USDT_to_EUR
            low = ticker['low'] * USDT_to_EUR
            last = ticker['last'] * USDT_to_EUR
            open_price = ticker['open'] * USDT_to_EUR
            vwap = (ticker.get('vwap') or 0) * USDT_to_EUR
            volatility = calculate_volatility(high, low)
            percent_change = calculate_percent_change(last, open_price)

            data_list.append({
                "symbol": symbol,
                "price_eur": last,
                "volatility": volatility,
                "percent_change": percent_change,
                "open_price": open_price,
                "vwap": vwap,
                "high": high,
                "low": low,
            })

    # Sort data by volatility (highest first)
    sorted_data = sorted(data_list, key=lambda x: x["volatility"] or 0, reverse=True)

    # Update table
    for item in tree.get_children():
        tree.delete(item)

    for data in sorted_data:
        tree.insert("", "end", values=[
            data["symbol"],
            f"{data['price_eur']:.6f}" if data["price_eur"] else "N/A",
            f"{data['volatility']:.6f}" if data["volatility"] else "N/A",
            f"{data['percent_change']:.6f}" if data["percent_change"] else "N/A",
            f"{data['open_price']:.6f}" if data["open_price"] else "N/A",
            f"{data['vwap']:.6f}" if data["vwap"] else "N/A",
            f"{data['high']:.6f}" if data["high"] else "N/A",
            f"{data['low']:.6f}" if data["low"] else "N/A",
        ])

def start_update_process(exchange, selected_symbols, tree, interval_var):
    """Start the data retrieval process in a separate thread."""
    global is_running, update_thread

    def run():
        while is_running:
            if not search_active and selected_symbols:
                update_table(exchange, selected_symbols, tree)
            time.sleep(interval_var.get())

    if not is_running:
        is_running = True
        update_thread = threading.Thread(target=run, daemon=True)
        update_thread.start()

def stop_update_process():
    """Stop the data retrieval process."""
    global is_running
    is_running = False

def restart_update_process(exchange, selected_symbols, tree, interval_var):
    """Restart the data retrieval process."""
    stop_update_process()
    start_update_process(exchange, selected_symbols, tree, interval_var)

def toggle_symbol(symbol, var, selected_symbols, tree, exchange, interval_var):
    """Toggle a symbol in the selection and update the table."""
    if var.get():
        selected_symbols.append(symbol)
    else:
        if symbol in selected_symbols:
            selected_symbols.remove(symbol)
    restart_update_process(exchange, selected_symbols, tree, interval_var)

def filter_symbols(search_var, scrollable_frame, all_symbols, selected_symbols):
    """Filter the displayed symbols based on the input in the search field."""
    global search_active
    search_text = search_var.get().lower()

    # Wenn das Suchfeld leer ist, wird das Coin-Menü nicht gefüllt
    if search_text == "":
        for widget in scrollable_frame.winfo_children():
            widget.destroy()  # Löscht alle Widgets
        return

    search_active = True  # Aktiviert den Suchmodus

    # Alle Symbole anzeigen, die dem Suchtext entsprechen
    for widget in scrollable_frame.winfo_children():
        widget.destroy()  # Löscht alle vorherigen Widgets

    for symbol in all_symbols:
        if search_text in symbol.lower():
            var = tk.BooleanVar(value=(symbol in selected_symbols))
            checkbox = tk.Checkbutton(
                scrollable_frame,
                text=symbol,
                variable=var,
                command=lambda s=symbol, v=var: toggle_symbol(s, v, selected_symbols, tree, exchange, interval_var),
                bg="#36393f" if symbol in selected_symbols else "#2c2f33",
                fg="white",
                selectcolor="#7289da",
                font=("Arial", 10)
            )
            checkbox.pack(fill=tk.X, padx=2, pady=1)

    search_active = False  # Deaktiviert den Suchmodus nach Abschluss der Anzeige



def show_loading_message(root, message_var):
    """Display a loading message."""
    loading_label = tk.Label(root, textvariable=message_var, bg="#2c2f33", fg="white", font=("Arial", 12))
    loading_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    return loading_label

def hide_loading_message(loading_label):
    """Hide the loading message."""
    loading_label.destroy()

def create_gui():
    global root, tree, interval_var, exchange, selected_symbols
    exchange = get_exchange()

    root = tk.Tk()
    root.title(PROGRAM_TITLE)
    root.geometry("800x400")
    root.configure(bg="#2c2f33")
    root.minsize(800, 400)  # Minimum window size

    # Allow resizing
    root.resizable(True, True)

    # Show loading message
    message_var = tk.StringVar(value="Bitte warten, lade Coins...")
    loading_label = show_loading_message(root, message_var)

    # Load symbols with caching
    threading.Thread(target=lambda: list_all_symbols(exchange), daemon=True).start()
    load_cached_symbols()
    selected_symbols = ["BTC/USDT", "ETH/USDT", "LTC/USDT", "SOL/USDT", "TRUMP/USDT"]

    # Hide loading message after loading
    root.after(1000, lambda: hide_loading_message(loading_label))

    # Control panel at the top with logo and branding
    control_frame = tk.Frame(root, bg="#2c2f33")
    control_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

    # Add branding text before the logo
    branding_label = tk.Label(control_frame, text="MegaTux-Crypticker", bg="#2c2f33", fg="white", font=("Arial", 14, "bold"))
    branding_label.pack(side=tk.LEFT, padx=(5, 0))

    # Load and place the logo image while maintaining aspect ratio
    try:
        logo = Image.open("logo.png")
        # Calculate new dimensions while maintaining aspect ratio
        w, h = logo.size
        max_width = 100  # Adjust this value based on your space
        ratio = max_width / float(w)
        h = int(float(h) * float(ratio))
        logo = logo.resize((max_width, h), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(logo)
        logo_label = tk.Label(control_frame, image=logo_img, bg="#2c2f33")
        logo_label.image = logo_img  # Keep a reference to avoid garbage collection
        logo_label.pack(side=tk.LEFT, padx=5)  # Position the logo after the branding text
    except Exception as e:
        print(f"Could not load logo image: {e}")

    interval_var = tk.IntVar(value=5)  # Reduced interval for faster updates
    tk.Label(control_frame, text="Intervall (Sekunden):", bg="#2c2f33", fg="white", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
    tk.Entry(control_frame, textvariable=interval_var, width=5, font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

    tk.Button(control_frame, text="Start", command=lambda: start_update_process(exchange, selected_symbols, tree, interval_var), bg="#7289da", fg="white").pack(side=tk.LEFT, padx=5)
    tk.Button(control_frame, text="Stop", command=stop_update_process, bg="#7289da", fg="white").pack(side=tk.LEFT, padx=5)

    # Table
    tree = ttk.Treeview(root, columns=headers, show="headings", height=5)
    tree.pack(fill=tk.BOTH, expand=True)

    for header in headers:
        tree.heading(header, text=header)
        tree.column(header, width=150)

    # Coin menu at the bottom of the GUI
    coin_menu_frame = tk.Frame(root, bg="#2c2f33")
    coin_menu_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

    search_var = tk.StringVar()
    search_entry = tk.Entry(coin_menu_frame, textvariable=search_var, font=("Arial", 12), bg="#2c2f33", fg="white")
    search_entry.pack(fill=tk.X, padx=5, pady=5)

    canvas = tk.Canvas(coin_menu_frame, bg="#2c2f33", highlightthickness=0)
    scrollbar = tk.Scrollbar(coin_menu_frame, orient="vertical", command=canvas.yview, width=20)
    scrollable_frame = tk.Frame(canvas, bg="#2c2f33")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    search_var.trace_add("write", lambda *args: filter_symbols(search_var, scrollable_frame, cached_symbols, selected_symbols))
    filter_symbols(search_var, scrollable_frame, cached_symbols, selected_symbols)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
