# Toiston esto paikallisissa malleissa (Repeat Penalty)

## Ongelma

Paikallinen AI-malli (GGUF) saattaa toistaa sanoja ja lauseita liikaa, vaikka muut parametrit olisi säädetty minimaalisiksi.

## Ratkaisu

JugiAI käyttää nyt `repeat_penalty` -parametria paikallisten mallien kanssa. Tämä parametri on erityisesti suunniteltu `llama-cpp-python`-kirjastolle ja toimii paremmin kuin OpenAI:n `frequency_penalty` ja `presence_penalty` -parametrit.

## Käyttö

### Asetuksista

1. Avaa **Asetukset** ⚙
2. Siirry **Paikallinen**-välilehdelle
3. Säädä **Toiston esto (repeat_penalty)** -liukusäädintä:
   - **1.0** = ei rangaistusta (enemmän toistoa)
   - **1.1-1.3** = suositeltu arvo (vähentää toistoa kohtuullisesti)
   - **1.4-2.0** = voimakas rangaistus (vähentää toistoa voimakkaasti)

### Profiileista

Voit myös asettaa `repeat_penalty`-arvon profiilikohtaisesti:

1. Avaa **Profiilit**
2. Valitse profiili listasta
3. Säädä **repeat_penalty (paikallinen)** -arvoa
4. Tallenna muutokset

## Tekniset yksityiskohdat

### OpenAI vs. Paikalliset mallit

JugiAI käyttää eri parametreja eri taustamoottoreille:

| Backend | Toiston esto -parametri | Arvoalue | Oletusarvo |
|---------|-------------------------|----------|------------|
| **OpenAI** | `frequency_penalty` & `presence_penalty` | -2.0 – 2.0 | 0.0 |
| **Paikallinen** | `repeat_penalty` | 1.0 – 2.0 | 1.1 |

### Parametrin toiminta

`repeat_penalty` toimii seuraavasti:

- **1.0** = Ei rangaistusta, malli voi toistaa vapaasti
- **>1.0** = Rangaistus toistosta, mitä suurempi arvo, sitä vähemmän toistoa
- **1.1** = Kevyt rangaistus (oletus, toimii useimmissa tapauksissa)
- **1.3** = Keskivahva rangaistus (suositeltu, jos ongelma jatkuu)
- **1.5+** = Vahva rangaistus (käytä varoen, voi vaikuttaa vastausten laatuun)

### Milloin käyttää korkeampaa arvoa?

Korkeampi `repeat_penalty` -arvo on hyödyllinen, kun:

- Malli toistaa samoja sanoja tai lauseita moneen kertaan
- Vastaukset ovat liian toisteisia tai ennustettavia
- Haluat monimuotoisempia vastauksia

### Varoitukset

⚠️ **Liian korkea arvo** (>1.5) voi aiheuttaa:
- Epäluonnollisia vastauksia
- Vaikeuksia noudattaa ohjeita
- Katkelmaisuutta tai epäjohdonmukaisuutta

💡 **Suositus**: Aloita arvolla 1.1-1.3 ja nosta vain tarvittaessa.

## Esimerkkejä

### Matala toiston esto (1.0-1.1)
```
Käyttäjä: Kerro lyhyt tarina
Malli: Olipa kerran pieni poika. Poika asui pienessä talossa. 
       Pienessä talossa oli pieni koira...
```

### Keskivahva toiston esto (1.2-1.3)
```
Käyttäjä: Kerro lyhyt tarina  
Malli: Olipa kerran nuori poika, joka asui vanhassa talossa metsän 
       laidalla. Hänen koiransa oli uskollinen toveri...
```

### Vahva toiston esto (1.5+)
```
Käyttäjä: Kerro lyhyt tarina
Malli: Aikoja sitten eräässä syrjäisessä kylässä asui seikkailunhaluinen 
       nuorukainen. Tämän uskollisena seuralaisena kulki...
```

## Usein kysytyt kysymykset

**K: Vaikuttaako tämä OpenAI-malleihin?**  
V: Ei. `repeat_penalty` koskee vain paikallisia malleja. OpenAI-mallit käyttävät omia parametrejaan (`frequency_penalty` ja `presence_penalty`).

**K: Miksi oletusarvo on 1.1 eikä 1.0?**  
V: Arvo 1.1 vähentää toistoa hieman ilman negatiivisia vaikutuksia vastausten laatuun. Se on hyvä kompromissi.

**K: Voiko arvon asettaa alle 1.0?**  
V: Ei. Arvot alle 1.0 lisäisivät toistoa, mikä ei ole tarkoituksenmukaista.

**K: Täytyykö minun ladata malli uudelleen kun muutan arvoa?**  
V: Ei. Parametri astuu voimaan seuraavassa API-kutsussa automaattisesti.

## Yhteenveto

- `repeat_penalty` vähentää sanojen ja lauseiden toistoa paikallisissa malleissa
- Oletusarvo 1.1 toimii useimmissa tapauksissa hyvin
- Säädä arvoa 1.0-2.0 välillä tarpeen mukaan
- Aloita matalalla (1.1-1.3) ja nosta vain jos ongelma jatkuu
- Liian korkea arvo (>1.5) voi vaikuttaa negatiivisesti vastausten laatuun
