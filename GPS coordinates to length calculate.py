from math import cos, asin, sqrt, log, tan, pi, atan2

lat1 = float(52.289633) #De breedtegraad van het coordinaat van het startpunt
lon1 = float(4.843559) #De lengtegraad van het coordinaat van het startpunt
lat2 = float(52.289845) #De breedtegraad van het coordinaat van het eindpunt
lon2 = float(4.843619) #De lengte van het coordinaat van het startpunt

const = pi / 180.0
formule = 0.5 - cos((lat2 - lat1) * const)/2 + (cos(lat1 * const) * cos(lat2 * const) * (1 - cos((lon2 - lon1) * const))) / 2
afstandinkm = 12742 * asin(sqrt(formule)) 
afstandinm = afstandinkm*1000

radianlat1 = lat1 * const
radianlon1 = lon1 * const
radianlat2 = lat2 * const
radianlon2 = lon2 * const

dLon = radianlon2 - radianlon1

dPhi = log(tan(radianlat2/2.0+pi/4.0)/tan(radianlat1/2.0+pi/4.0))
if abs(dLon) > pi:
     if dLon == abs(dLon):
         dLon = -(2.0 * pi - dLon)
     else:
         dLon = (2.0 * pi + dLon)

draai = (atan2(dLon, dPhi))/const #hierbij berekenen we hoeveel de drone moet draaien, waarbij het is uitgebeeld in graden, in een hoek ten opzichte van het noorden.

print(afstandinm)
print(draai) #Een negatieve hoek is een draai richting links of naar het westen en een positieve hoek is een draai richting rechts of naar het oosten.
