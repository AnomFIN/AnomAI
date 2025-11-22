# Toiston esto -ongelma korjattu! / Repetition Issue Fixed!

## Mikä oli ongelma? / What was the problem?

Paikallinen AI-malli (GGUF) toisti sanoja ja lauseita liikaa, vaikka asetukset olivat "maksimit miinuksella". Kuvakaappaus näytti tekstiä kuten:

```
"Kyllä, kiitos! Entä kyllä, kiitos! Entä sinä?Kyllä, kiitos! Entä sinä?"
"Kaukana metsän siimeKaukana metsän siimeksessäKaukana metsän siimeksessä asuiKaukana..."
```

**Syy**: Sovellus käytti OpenAI:n parametreja (`frequency_penalty` ja `presence_penalty`), jotka **eivät toimi** llama-cpp-python-kirjaston kanssa.

## Ratkaisu / Solution

✅ **Lisätty `repeat_penalty` -parametri paikallisille malleille!**

`repeat_penalty` on llama-cpp-python-kirjaston oma parametri toiston estoon:
- **1.0** = Ei rangaistusta (enemmän toistoa)
- **1.1** = Kevyt esto (oletusarvo, suositeltu)
- **1.2-1.3** = Kohtuullinen esto
- **1.4-2.0** = Vahva esto (voi vaikuttaa laatuun)

## Miten käytän? / How to use?

### Vaihtoehto 1: Asetuksista / Option 1: Settings

1. Avaa **Asetukset** ⚙
2. Siirry **Paikallinen**-välilehdelle
3. Säädä **Toiston esto (repeat_penalty)** -liukusäädintä
4. Tallenna

![Repeat Penalty Settings](https://via.placeholder.com/800x400?text=Repeat+Penalty+Settings)

### Vaihtoehto 2: Profiileista / Option 2: Profiles

1. Avaa **Profiilit**
2. Valitse tai luo profiili
3. Säädä **repeat_penalty (paikallinen)** -arvoa
4. Tallenna

## Suositellut arvot / Recommended values

### Jos toisto on kevyttä / For light repetition
```
repeat_penalty: 1.1 - 1.2
```
Tämä vähentää toistoa hieman muuttamatta vastausten laatua.

### Jos toisto on kohtalaista / For moderate repetition  
```
repeat_penalty: 1.2 - 1.3
```
Hyvä tasapaino toiston eston ja vastausten laadun välillä.

### Jos toisto on vakavaa / For severe repetition
```
repeat_penalty: 1.3 - 1.5
```
Voimakas esto. Voi vaikuttaa hieman vastausten luonnollisuuteen.

⚠️ **Varoitus**: Arvot yli 1.5 voivat aiheuttaa epäluonnollisia vastauksia!

## Tekniset yksityiskohdat / Technical details

### Mitä tehtiin? / What was done?

1. ✅ Lisättiin `repeat_penalty` parametri DEFAULT_CONFIG:iin (oletus: 1.1)
2. ✅ Päivitettiin `_call_local_llm()` käyttämään `repeat_penalty`-parametria
3. ✅ Lisättiin UI-kontrollit:
   - Liukusäädin Asetukset → Paikallinen -välilehdellä
   - Spinbox Profiilit-dialogissa
4. ✅ Integroitu profiilinhallinnan kanssa
5. ✅ Luotu 16 uutta testiä
6. ✅ Lisätty dokumentaatio (`docs/REPEAT_PENALTY.md`)

### Taaksepäin yhteensopivuus / Backward compatibility

Vanhat config-tiedostot toimivat! Jos `repeat_penalty` puuttuu, käytetään oletusarvoa 1.1.

### Testit / Tests

✅ **Kaikki 151 testiä läpäistiin**, mukaan lukien:
- 10 uutta yksikköä testiä (`test_repeat_penalty.py`)
- 6 uutta integraatiotestiä (`test_repeat_penalty_integration.py`)

### Turvallisuus / Security

✅ CodeQL-tarkistus suoritettu - **ei haavoittuvuuksia**

## Lisätietoja / More information

Katso tarkempi dokumentaatio: **docs/REPEAT_PENALTY.md**

### Usein kysytyt kysymykset / FAQ

**K: Toimiiko tämä OpenAI-mallien kanssa?**  
V: Ei, eikä tarvitsekaan. OpenAI-mallit käyttävät omia parametrejaan (`frequency_penalty` ja `presence_penalty`), jotka toimivat hyvin.

**K: Pitääkö minun ladata malli uudelleen?**  
V: Ei! Parametri astuu voimaan heti seuraavassa viestissä.

**K: Mikä on paras arvo?**  
V: Aloita arvolla 1.2. Jos toisto jatkuu, nosta 1.3:een. Jos edelleen ongelma, kokeile 1.4.

**K: Voiko arvon laittaa alle 1.0?**  
V: Ei. Arvot alle 1.0 lisäisivät toistoa, mikä ei ole toivottavaa.

## Kiitokset / Credits

Korjaus toteutettu [GitHub Copilot](https://github.com/features/copilot) -avulla.

Issue raportoitu: [GitHub Issue](https://github.com/AnomFIN/AnomAI/issues)

---

**Versionumero**: Korjaus lisätty versioon joka sisältää commit `ca515ce`  
**Päivämäärä**: 2025-01-22  
**Status**: ✅ Valmis ja testattu
