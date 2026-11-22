from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO

        # Recupero dal database tutte le relazioni tra escursioni e punti di interesse
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()

        # Scorro una alla volta tutte le relazioni ottenute dal database
        for relazione in relazioni:
            # Estraggo dalla relazione l'ID dell'escursione
            id_escursione = relazione['id_escursione']
            # Estraggo dalla relazione l'ID del punto di interesse
            id_punto_interesse = relazione['id_punto_interesse']

            # Cerco nel dizionario dei punti di interesse l'oggetto corrispondente all'ID appena estratto
            punto_interesse = self.punti_interesse_map[id_punto_interesse]

            # Cerco nel dizionario delle escursioni l'oggetto corrispondente all'ID appena estratto
            escursione = self.escursioni_map[id_escursione]

            # Aggiungo il punto di interesse all'insieme dei punti dell'escursione
            escursione.punti_interesse.add(punto_interesse)

            # Aggiungo l'escursione all'insieme delle escursioni del punto di interesse
            punto_interesse.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        # Seleziono le escursioni appartenenti al parco scelto
        lista_escursione = []

        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                lista_escursione.append(escursione)

        # Inizializzo i parametri della ricorsione
        pacchetto_parziale = []
        durata_corrente = 0
        costo_corrente = 0
        valore_corrente = 0
        punti_usati = set()
        start_index = 0
        self._ricorsione(
            lista_escursione,
            start_index,
            pacchetto_parziale,
            durata_corrente,
            costo_corrente,
            valore_corrente,
            punti_usati,
            max_giorni,
            max_budget
        )
        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, lista_escursione: list, start_index: int,
                    pacchetto_parziale: list, durata_corrente: int,
                    costo_corrente: float, valore_corrente: int,
                    punti_usati: set, max_giorni, max_budget):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        # Scorro le escursioni a partire dall'indice iniziale
        for i in range(start_index, len(lista_escursione)):

            # Recupero l'escursione corrente
            escursione = lista_escursione[i]

            # Controllo il limite massimo di giorni
            if max_giorni is not None:
                if durata_corrente + escursione.durata_giorni > max_giorni:
                    continue

            # Controllo il limite massimo di budget
            if max_budget is not None:
                if costo_corrente + escursione.costo > max_budget:
                    continue

            # Recupero i punti di interesse dell'escursione
            punti_escursione = escursione.punti_interesse

            # Controllo che nessun punto sia già stato utilizzato
            if not punti_usati.isdisjoint(punti_escursione):
                continue

            # Aggiungo l'escursione al pacchetto parziale
            pacchetto_parziale.append(escursione)

            # Aggiungo i punti di interesse ai punti già utilizzati
            punti_usati.update(punti_escursione)

            # Calcolo il valore dei punti di interesse dell'escursione
            valore_escursione = 0
            for punto in punti_escursione:
                valore_escursione += punto.voto_visitatori

            # Richiamo ricorsivamente la funzione
            self._ricorsione(
                lista_escursione,
                i + 1,
                pacchetto_parziale,
                durata_corrente + escursione.durata_giorni,
                costo_corrente + escursione.costo,
                valore_corrente + valore_escursione,
                punti_usati,
                max_giorni,
                max_budget
            )

            # Rimuovo l'escursione per provare altre combinazioni
            pacchetto_parziale.pop()

            # Rimuovo i suoi punti di interesse da quelli utilizzati
            punti_usati.difference_update(punti_escursione)
