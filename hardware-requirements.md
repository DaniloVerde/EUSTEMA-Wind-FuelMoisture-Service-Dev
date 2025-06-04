## Requisiti

| Ambiente | Sistema Operativo | Utente Root | CPU | RAM | Disco |
|----------|-------------------|-------------|-----|-----|-------|
| Sviluppo | Debian Based | Si | **Minimo**: 4 core (2.0 GHz)<br />**Raccomandato**: 6-8 core (2.5 GHz) | **Minimo**: 4 GB <br />**Raccomandato**: 8 GB | **Minimo**: 15 GB<br />**Raccomandato**: 20 GB |
| Collaudo | Debian Based | Si | **Minimo**: 6 core (2.0 GHz)<br />**Raccomandato**: 8-12 core (2.5 GHz) | **Minimo**: 8 GB <br />**Raccomandato**: 16 GB | **Minimo**: 15 GB<br />**Raccomandato**: 20 GB |
| Produzione | Debian Based | Si | **Minimo**: 8 core (2.5 GHz)<br />**Raccomandato**: 16-24 core (3.0 GHz) | **Minimo**: 16 GB<br />**Raccomandato**: 32 GB | **Minimo**: 20 GB<br />**Raccomandato**: 50 GB |

Per l'ambiente di produzione, non avendo una stima del carico, sto considerando circa 3-4 simulazioni concorrenti con minimo 2 core e 4 GB di RAM per simulazione, quindi 6-8 core e 12-16 GB di RAM. Per il disco, tenuto conto di circa 10 GB per il sistema operativo, il windninja e tutte le librerie necessarie, ho considerato circa 2.5 GB di dati (input + output) per simulazione, quindi 10 GB per 4 simulazioni. Ho aggiunto un margine di sicurezza per considerare la convivenza di dati di simulazioni precenti prima di essere oggetto di rimozione automatica, per i dati di log e altri file temporanei.
