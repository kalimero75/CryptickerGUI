# CryptickerGUI
Ein Python-basiertes Tool zur Überwachung von Kryptowährungspreisen in Echtzeit, das mit der CCXT-Bibliothek arbeitet. Es bietet eine intuitive Möglichkeit, Preisdaten, Tageshöchst- und -tiefststände sowie die Volatilität ausgewählter Kryptowährungen anzuzeigen. 

# Megatux-CryptoTicker

**Megatux-CryptoTicker** ist ein Python-basiertes GUI-Tool zur Anzeige von Kryptowährungsdaten in Echtzeit. Es verwendet die `ccxt`-Bibliothek, um Marktdaten von Binance abzurufen, und `tkinter`, um eine interaktive Benutzeroberfläche bereitzustellen.

## Features
- Anzeige von Preisen, Tageshoch/-tief und Volatilität für ausgewählte Handelspaare.
- Dynamische Aktualisierung der Daten in benutzerdefinierten Intervallen.
- Auswahl der Handelspaare über eine scrollbare Liste mit Checkboxen.
- Intuitive Steuerung zum Starten und Stoppen der Updates.

---

# Installation

## Voraussetzungen
Stelle sicher, dass die folgenden Voraussetzungen auf deinem System installiert sind:

1. **Python 3.7 oder höher**
 
2. **Python-Bibliotheken**
   - Die benötigten Bibliotheken können mit `pip` installiert werden.
  
 tkinter,threading,time & sys 

3. **Anwendung starten**  
   Starte das Programm:  
   
   python3 cryptickerGUI.py

## Hinweis
- Die Anwendung verwendet Binance als Standardbörse über die `ccxt`-Bibliothek.
- Stelle sicher, dass dein Internetzugang funktioniert, um die aktuellen Daten abzurufen.


