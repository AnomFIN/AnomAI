JugiAI (Python/Tkinter)
=======================

Kevyt .py-sovellus, joka keskustelee OpenAI:n kanssa tai vaihtoehtoisesti paikallisella .gguf-mallilla (llama-cpp-python). Ensimmäisellä käynnistyksellä syötä OpenAI API -avain ja malli, tai valitse paikallinen malli. Asetukset tallentuvat config.json-tiedostoon ja keskusteluhistoria history.json-tiedostoon.

Käyttöohje (Windows):
1) Asenna Python 3, jos sitä ei ole.
2) Pura tämä kansio (JugiAI_Python) minne tahansa.
3) Aja sovellus:
   - Tuplaklikkaa jugiai.py (jos .py on liitetty Python-tulkkiin), tai
   - Avaa komentokehote kansioon ja suorita:  python jugiai.py
4) Asetukset (⚙️):
   - Taustajärjestelmä: "openai" tai "local" (.gguf). OpenAI-moodissa syötä API Key (sk-...) ja malli (esim. gpt-4o-mini).
   - Paikallinen malli: valitse .gguf-tiedosto ja haluttu säiemäärä.
   - Promptit ja parametrit: system prompt, temperature, top_p, max_tokens, presence/frequency penalty.
   - Taustakuva: valitse PNG (oletus yrittää logo.png). Kokoa voi säätää (subsample 1–8) ja näkyvyyden voi kytkeä päälle/pois.
5) Kirjoita viesti alareunaan ja paina Enter (Shift+Enter = rivinvaihto). Keskustelu tallentuu automaattisesti ja jatkuu seuraavalla käynnistyskerralla.
6) "Tyhjennä"-painike poistaa nykyisen keskusteluhistorian.

Paikallinen malli (.gguf):
- Asenna riippuvuus: pip install llama-cpp-python
- Valitse .gguf-tiedosto asetuksista. Huomaa, että muistitarve ja suorituskyky riippuvat mallin koosta.

Huomio turvallisuudesta:
- OpenAI-tilassa pyyntö menee suoraan api.openai.com-palveluun; avain tallentuu vain paikalliseen config.jsoniin.
- Älä jaa API-avaintasi tai config/history-tiedostoja muille.
