from math import cos, asin, sqrt, log, tan, pi, atan2  # Importeer wiskundige functies voor berekeningen

# Coördinaten van het start- en eindpunt
lat1 = float(52.289633)  # Breedtegraad van het startpunt
lon1 = float(4.843559)  # Lengtegraad van het startpunt
lat2 = float(52.289845)  # Breedtegraad van het eindpunt
lon2 = float(4.843619)  # Lengtegraad van het eindpunt

# Constante om graden naar radialen om te rekenen
const = pi / 180.0

# Berekening van de afstand tussen de twee punten met de haversine-formule
formule = (
    0.5
    - cos((lat2 - lat1) * const) / 2
    + (cos(lat1 * const) * cos(lat2 * const) * (1 - cos((lon2 - lon1) * const))) / 2
)
afstandinkm = 12742 * asin(sqrt(formule))  # Afstand in kilometers
afstandinm = afstandinkm * 1000  # Afstand in meters

# Converteer breedte- en lengtegraden naar radialen
radianlat1 = lat1 * const
radianlon1 = lon1 * const
radianlat2 = lat2 * const
radianlon2 = lon2 * const

# Verschil in lengtegraad
dLon = radianlon2 - radianlon1

# Berekening van de hoek met de inverse van Mercator-projectie
dPhi = log(
    tan(radianlat2 / 2.0 + pi / 4.0) / tan(radianlat1 / 2.0 + pi / 4.0)
)

# Corrigeer als het verschil in lengtegraad groter is dan π
if abs(dLon) > pi:
    if dLon == abs(dLon):  # Als dLon positief is
        dLon = -(2.0 * pi - dLon)  # Corrigeer door naar links te gaan
    else:  # Als dLon negatief is
        dLon = (2.0 * pi + dLon)  # Corrigeer door naar rechts te gaan

# Berekening van de draaihoek in graden
draai = (atan2(dLon, dPhi)) / const  # Hoek in graden t.o.v. het noorden

# Resultaten printen
print(afstandinm)  # Afstand tussen de twee coördinaten in meters
print(draai)  # Draaihoek: negatief is naar links (west), positief is naar rechts (oost)
