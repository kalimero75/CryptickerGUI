#!/bin/python3

import ccxt
import tkinter as tk
from tkinter import messagebox
import threading
import time
import sys

def get_exchange():
    """Initialisiere die Binance-Börse mit ccxt."""
    try:
        exchange = ccxt.binance()
        return exchange
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Initialisieren der Börse: {e}")
        exit()

def list_all_symbols(exchange):
    """Zeige alle verfügbaren Handelspaare auf Binance an."""
    try:
        markets = exchange.load_markets()
        symbols = sorted([symbol for symbol in markets.keys() if symbol.endswith("/USDT")])  # Alphabetisch sortieren
        return symbols
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Abrufen der Symbole: {e}")
        return []

def fetch_ticker_data(exchange, symbol):
    """Hole die Ticker-Daten für ein bestimmtes Symbol."""
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    except Exception:
        return None

def calculate_volatility(high, low):
    """Berechne die Volatilität in Prozent basierend auf dem Tageshoch und Tagestief."""
    if high and low:
        return (high - low) / low * 100
    return None

def update_table(exchange, selected_symbols, table_frame, frequency_var, is_running):
    """Aktualisiere die Tabelle mit Kryptowährungsdaten und sortiere nach Volatilität."""
    try:
        frequency = int(frequency_var.get())
        while is_running[0]:  # Solange is_running True ist, weiter aktualisieren
            for widget in table_frame.winfo_children():
                if widget.grid_info()["row"] > 0:  # Behalte die Header in Zeile 0
                    widget.destroy()

            # Liste für die sortierten Daten
            data_list = []

            for symbol in selected_symbols:
                ticker = fetch_ticker_data(exchange, symbol)
                if ticker:
                    high = ticker['high']
                    low = ticker['low']
                    volatility = calculate_volatility(high, low)
                    price_usd = ticker['last']
                    data_list.append({
                        "symbol": symbol,
                        "price_usd": price_usd,
                        "volatility": volatility,
                        "high": high,
                        "low": low,
                    })

            # Daten nach Volatilität sortieren (höchste zuerst)
            sorted_data = sorted(data_list, key=lambda x: x["volatility"] or 0, reverse=True)

            # Sortierte Daten in die Tabelle schreiben
            for row, data in enumerate(sorted_data, start=1):
                table_data = [
                    data["symbol"],
                    f"{data['price_usd']:.6f} USD" if data["price_usd"] else "N/A",
                    f"{data['volatility']:.6f} %" if data["volatility"] else "N/A",
                    f"{data['high']:.6f} USD" if data["high"] else "N/A",
                    f"{data['low']:.6f} USD" if data["low"] else "N/A",
                ]

                for col, value in enumerate(table_data):
                    tk.Label(
                        table_frame, text=value, bg="#23272a", fg="white", font=("Arial", 12)
                    ).grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            time.sleep(frequency)
    except ValueError:
        messagebox.showerror("Fehler", "Bitte geben Sie eine gültige Zahl für die Wiederholungsfrequenz ein.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Abrufen der Daten: {e}")

def start_ticker(exchange, selected_symbols, table_frame, frequency_var, is_running):
    """Starte den Ticker in einem separaten Thread."""
    is_running[0] = True
    threading.Thread(target=update_table, args=(exchange, selected_symbols, table_frame, frequency_var, is_running), daemon=True).start()

def stop_ticker(is_running, submit_button, stop_button):
    """Stoppe den Ticker-Update-Prozess und reaktiviere den Absenden-Button."""
    is_running[0] = False
    submit_button.config(state=tk.NORMAL)  # Absenden-Button wieder aktivieren
    stop_button.config(state=tk.DISABLED)  # Stop-Button deaktivieren

def on_submit(exchange, all_symbols, checkboxes, table_frame, frequency_var, is_running, submit_button, stop_button):
    """Verarbeite die Benutzereingabe und starte den Ticker."""
    stop_ticker(is_running, submit_button, stop_button)  # Stoppe den aktuellen Ticker-Prozess
    
    selected_symbols = [symbol for symbol, var in checkboxes.items() if var.get()]
    
    if selected_symbols:
        start_ticker(exchange, selected_symbols, table_frame, frequency_var, is_running)
        submit_button.config(state=tk.DISABLED)  # Absenden-Button deaktivieren
        stop_button.config(state=tk.NORMAL)     # Stop-Button aktivieren
    else:
        messagebox.showinfo("Info", "Bitte wähle mindestens eine Währung aus.")

# GUI erstellen
def create_gui():
    exchange = get_exchange()
    all_symbols = list_all_symbols(exchange)
    
    root = tk.Tk()
    root.title("Megatux-CryptoTicker")  # Setze den Titel
    root.geometry("1200x700")
    root.configure(bg="#2c2f33")

    # Styling
    button_style = {"bg": "#7289da", "fg": "white", "font": ("Arial", 14, "bold"), "relief": "flat"}
    header_style = {"bg": "#7289da", "fg": "white", "font": ("Arial", 14, "bold"), "relief": "flat"}

    # Scrollbare Liste mit Checkboxen
    checkbox_frame = tk.Frame(root, bg="#2c2f33")
    checkbox_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)

    canvas = tk.Canvas(checkbox_frame, bg="#2c2f33", highlightthickness=0)
    scrollbar = tk.Scrollbar(checkbox_frame, orient="vertical", command=canvas.yview, width=20)  # Scrollbar verbreitern
    scrollable_frame = tk.Frame(canvas, bg="#2c2f33")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Ermöglicht das Scrollen mit dem Mausrad
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    checkboxes = {}  # Zustandsbehaftete Speicherung der Checkboxen
    default_selected = ['BTC/USDT', 'LTC/USDT', 'TRUMP/USDT', 'SOL/USDT', 'ETH/USDT','PEPE/USTD','MEME/USTD']  # Standard-Auswahl
    for symbol in all_symbols:
        var = tk.BooleanVar(value=(symbol in default_selected))  # Standardmäßig auswählen, falls im default_selected
        checkboxes[symbol] = var
        color = "#7289da" if var.get() else "#2c2f33"  # Hintergrundfarbe Blau, wenn ausgewählt
        fg_color = "white" if var.get() else "gray"  # Textfarbe Weiß, wenn ausgewählt
        checkbutton = tk.Checkbutton(
            scrollable_frame, text=symbol, variable=var, bg=color, fg=fg_color, selectcolor=color, font=("Arial", 12, "italic"),
            anchor="w", relief="flat", padx=10, pady=5, highlightthickness=0,
            command=lambda symbol=symbol: update_checkbutton_color(symbol, checkboxes)  # Call when toggled
        )
        checkbutton.pack(fill=tk.X, pady=1)

    def update_checkbutton_color(symbol, checkboxes):
        """Aktualisiere die Farbe des Checkbuttons, wenn er ausgewählt oder abgewählt wird."""
        var = checkboxes[symbol]
        checkbutton = [widget for widget in scrollable_frame.winfo_children() if widget.cget("text") == symbol][0]
        if var.get():
            checkbutton.config(bg="#7289da", fg="white")
        else:
            checkbutton.config(bg="#2c2f33", fg="gray")

    # Wiederholungsfrequenz und Buttons
    frequency_var = tk.StringVar(value="20")  # Standard-Wert: 20 Sekunden
    control_frame = tk.Frame(root, bg="#2c2f33")
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)

    tk.Label(
        control_frame, text="Wiederholungsfrequenz (Sekunden):", bg="#2c2f33", fg="white", font=("Arial", 12)
    ).pack(side=tk.LEFT, padx=5)
    tk.Entry(control_frame, textvariable=frequency_var, width=5, font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

    submit_button = tk.Button(
        control_frame, text="Absenden", command=lambda: on_submit(exchange, all_symbols, checkboxes, table_frame, frequency_var, is_running, submit_button, stop_button), **button_style
    )
    submit_button.pack(side=tk.LEFT, padx=5)

    stop_button = tk.Button(
        control_frame, text="Stop", command=lambda: stop_ticker(is_running, submit_button, stop_button), **button_style, state=tk.DISABLED
    )
    stop_button.pack(side=tk.LEFT, padx=5)

    # Tabelle für die Daten
    table_frame = tk.Frame(root, bg="#23272a")
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Tabellen-Header
    headers = ["Symbol", "Preis (USD)", "Volatilität (%)", "Tageshoch (USD)", "Tagestief (USD)"]
    for col, header in enumerate(headers):
        tk.Label(
            table_frame, text=header, **header_style
        ).grid(row=0, column=col, padx=5, pady=5, sticky="nsew")

    # Globaler Ticker-Status
    is_running = [False]  # Liste, um den Wert zu ändern

    root.mainloop()

if __name__ == "__main__":
    create_gui()
