JugiAI (Python/Tkinter)
=======================

JugiAI on kevyt työpöytäsovellus (yksi `jugiai.py`), joka keskustelee joko OpenAI:n rajapinnan tai paikallisen GGUF-mallin (llama-cpp-python) kanssa. Yläpalkissa on "JugiAI" sekä pikanapit asetuksiin ja keskustelun tyhjentämiseen.

Pika-aloitus (Windows)
----------------------
1) Asenna Python 3 (suositus 3.10+): https://www.python.org/downloads/windows/
2) Pura `JugiAI_Python.zip` haluamaasi kansioon.
3) Käynnistä sovellus:
   - Tuplaklikkaa `start_jugiai.bat` (yrittää käyttää `pythonw` ettei konsoli näy), tai
   - Tuplaklikkaa `jugiai.py`, tai
   - Komentoriviltä: `python jugiai.py`
4) Avaa ⚙️ Asetukset ja valitse taustajärjestelmä (OpenAI tai Paikallinen), syötä tarvittavat asetukset ja tallenna.

Taustajärjestelmän valinta
--------------------------
- Yläpalkin pikasäädin: vaihtaa "openai" ↔ "local" nopeasti (synkronoitu asetuksiin).
- Asetukset > Yleiset -välilehti: sama valinta löytyy myös täältä.

OpenAI-tila
-----------
- Asetukset > OpenAI:
  - `OpenAI API Key`: liitä avain muodossa `sk-...`
  - `Malli`: esim. `gpt-4o-mini` (voit valita muun tilisi salliman mallin)
- Asetukset > Yleiset: säädä `system prompt`, `temperature`, `top_p`, `max_tokens`, `presence/frequency penalty`.
- Huom: avain tallentuu vain paikalliseen `config.json`-tiedostoon. Kutsut lähetetään suoraan `api.openai.com`-palveluun.

Paikallinen malli (.gguf)
-------------------------
- Riippuvuus: `pip install llama-cpp-python`
- Asetukset > Paikallinen:
  - `Paikallinen malli (.gguf)`: valitse mallin tiedosto.
  - `Säikeet`: CPU-säikeiden määrä (0 = automaattinen).
- Vihje: Mallien koko vaikuttaa RAM-/VRAM-tarpeeseen ja nopeuteen. Aloita pienemmällä (esim. 7B) ja kasvata tarpeen mukaan.

Ulkoasu ja logo
---------------
- Asetukset > Ulkoasu:
  - `Taustakuva`: valitse PNG (oletus yrittää `logo.png` tästä tai ylemmästä kansiosta).
  - `Näytä taustakuva/watermark`: kytkee vesileiman chatin taustalle.
  - `Watermark-koko`: 1–8 (suurempi arvo = pienempi kuva).
  - `Fonttikoko`: chat- ja syötekentän tekstin koko.
- Sovellus käyttää samaa kuvaa myös ikonikuvana.

Keskusteluhistoria ja asetukset
--------------------------------
- Asetukset tallentuvat `config.json`-tiedostoon.
- Keskustelu tallentuu `history.json`-tiedostoon ja palautuu seuraavalla käynnistyksellä.
- "Tyhjennä"-painike yläpalkissa nollaa nykyisen historian.

Vikatilanteet
-------------
- 401/403/429 tms.: tarkista API-avain, mallin käyttöoikeudet ja mahdolliset käyttörajat.
- Paikallinen malli ei käynnisty: varmista `llama-cpp-python` asennus ja että .gguf-polku on oikein.
- Python ei käynnisty tuplaklikkaamalla: suorita `start_jugiai.bat` tai avaa komentokehote kansioon ja aja `python jugiai.py`.

Tiedostot
---------
- `jugiai.py`: Sovelluksen lähdekoodi (Tkinter). Ei vaadi ulkoisia riippuvuuksia OpenAI-tilassa.
- `start_jugiai.bat`: Windows-käynnistin (yrittää ensin `pythonw`, sitten `py -3`, sitten `python`).
- `README.md`: tämä ohje.
- `README.txt`: lyhyet ohjeet.
- `config.json` ja `history.json`: luodaan automaattisesti.
- `logo.png` (valinnainen): käytetään ikonina ja vesileimana, jos löytyy.

Rakennus: JugiAI.exe (Windows)
--------------------------------
Voit luoda erillisen Windows-suoritettavan tiedoston (JugiAI.exe) PyInstallerilla.

1) Avaa komentokehote tähän kansioon.
2) Aja: `build_exe.bat`
   - Luo virtuaaliympäristön `.venv_build/` ja asentaa: pyinstaller, pillow, pyinstaller-hooks-contrib, llama-cpp-python.
   - Muuntaa `logo.png` → `app.ico` (jos `logo.png` löytyy).
   - Kääntää `JugiAI.exe` ilman konsoli-ikkunaa.
   - Pakkaa valmiin kansion `dist/JugiAI` zipiin `JugiAI_Windows.zip`.
3) Lopputulokset:
   - EXE: `dist/JugiAI/JugiAI.exe`
   - ZIP: `JugiAI_Windows.zip`

Huom:
- `llama-cpp-python` sisällytetään build-ympäristöön, jotta paikallinen .gguf-moodi toimii myös EXE:ssä (mallitiedosto ei sisälly — valitse oma malli asetuksista).
- Jos haluat käyttää omaa `.ico`-tiedostoa, korvaa `app.ico` tai tarjoa `logo.png` ennen buildia.
