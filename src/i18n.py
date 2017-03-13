"""Internationalization.

Use

  from i18n import translate as _

to enable string localization. In the future it would be easily
replaced by gettext since translatable strings are marked in the
same way as _("text").

Beside the translation service, this module defines the messages
used in the application, such as the help and the usage messages.
"""

import os
import atexit


############################################################
# Translation function
############################################################

def translate(text):
    """Translate the text in the current language."""
    try:
        return _strings[text]
    except KeyError:
        _missing_translation.add(text)
        s = (text if len (text) < 15 else text[:15] + "...")
        print("[TT] Warning: missing translation for '%s'" % s)
        return text


############################################################
# Application messages
############################################################

USAGE_en = ("Usage: pvcheck [OPTIONS]... TEST_FILE EXECUTABLE " +
            "[EXECUTABLE_PARAMS]...")

HELP_en = """Run tests to verify the correctness of a program.

Options:
  -v, --verbosity=L        set the verbosity level, where the level must be
                           an integer between 0 (minimum) and 4 (maximum).
                           The default value is 3.
  -t, --timeout=T          set how many seconds it should be waited for the
                           termination of the program.  The default is 10
                           seconds.
  -m, --max-errors=N       reports up to N errors per section (default 4).
  -c, --config=FILE        uses the specified configuration file.
  -C, --color=YES|NO|AUTO  enable or disable colored output (default AUTO).
  -V, --valgrind           use Valgrind (if installed) to check memory usage.
  -o, --output=RESUME|JSON|CSV select the output type.
  --list                   lists all the tests contained into a test file.
  -l, --log=FILE           specify the name of the file used for logging.  The
                           default is ~/.pvcheck.log.
  -h, --help               print this message and exit.
"""

USAGE_it = ("Utilizzo: pvcheck [OPZIONI...] " +
            "FILE_OUTPUT_ATTESO FILE_ESEGUIBILE " +
            "[PARAMETRI_ESEGUIBILE]...")

HELP_it = """Esegue dei test per verificare la correttezza di un programma.

Opzioni:
  -v, --verbosity=L        imposto il livello di verbosità.  Il livello
                           deve essere un valore intero tra 0 (minimo) e 3
                           (massimo).  Il default è 2.
  -t, --timeout=T          imposta per quanti secondi bisogna attendere
                           la terminazione del programma.  Il default è
                           pari a 10 secondi.
  -m, --max-errors=N       riporta fino ad un massimo di N errori per
                           sezione (default 4).
  -c, --config=FILE        utilizza il file di configurazione specificato.
  -C, --color=YES|NO|AUTO  abilita o disabilita l'output colorato (default
                           AUTO).
  -V, --valgrind           utilizza Valgrind (se installato) per controllare
                           l'utilizzo della memoria.
  -o, --output=RESUME|JSON|CSV seleziona il tipo di output.
  --list                   mostra i test presenti in un file di test.
  -l, --log=FILE           specifica il nome del file usato per il logging.
                           Il default è ~/.pvcheck.log.
  -h, --help               stampa questo messaggio ed esce.
"""

_strings = {}
_missing_translation = set()
_lang = 'en'

_it_strings = """
ERROR $ ERRORE
OK $ OK
WARNING! $ ATTENZIONE!
COMMAND LINE $ RIGA DI COMANDO
<temp.file> $ <file temp.>
INPUT $ INPUT
OUTPUT $ OUTPUT
TEMPORARY FILE $ FILE TEMPORANEO
TEST $ TEST
line %d $  riga %d
(expected '%s' $  (atteso '%s'
, got '%s')":  ottenuto '%s')
unexpected line '%s' $ riga inattesa '%s'
missing line (expected '%s') $ riga mancante (atteso '%s')
wrong number of lines (expected %d, got %d) $ numero di righe errato (atteso %d, ottenuto %d)
line %d is wrong  (expected '%s', got '%s') $ riga %d errata  (atteso '%s', ottenuto '%s')
The first %d lines matched correctly $ Le prime %d righe sono corrette
(... plus other %d errors ...) $ (... più altri %d errori ...)
ACTUAL OUTPUT $ OUTPUT EFFETTIVO
EXPECTED OUTPUT $ OUTPUT ATTESO
detailed comparison $ confronto dettagliato
<nothing> $ <niente>
missing section $ sezione mancante
empty section $ sezione vuota
extra section $ sezione extra
Invalid parameter ('%s') $ Parametro non valido ('%s')
TIMEOUT EXPIRED: PROCESS TERMINATED $ TEMPO LIMITE SCADUTO: PROCESSO TERMINATO
PROCESS ENDED WITH A FAILURE $ PROCESSO TERMINATO CON UN FALLIMENTO
(SEGMENTATION FAULT) $ (SEGMENTATION FAULT)
(ERROR CODE {status}) $ (CODICE D'ERRORE {status})
FAILED TO RUN THE FILE '{progname}' $ IMPOSSIBILE ESEGUIRE IL FILE '{progname}'
(the file does not exist) $ (file inesistente)
(... plus other %d lines ...) $ (... più altre %d righe ...)
SUMMARY $ RIEPILOGO
successes $ successi
warnings $ avvertimenti
errors $ errori
<program> $ <programma>
"""

_translations = {
    'it': {
        USAGE_en: USAGE_it,
        HELP_en: HELP_it
    }
}
_translations['it'].update(
    dict((a[0].strip(), a[2].strip()) for a in
         (b.partition('$') for b in _it_strings.splitlines())
         if len(a) == 3))


############################################################
# Setup and shutdown
############################################################

def _install_lang():
    global _lang
    global _strings
    _lang = os.environ.get('LANG', 'en').partition('_')[0]
    try:
        _strings = _translations[_lang]
    except KeyError:
        # Fallback to english, where the translation is the identity
        # function.
        _lang = 'en'
        for t in _translations.values():
            _strings = dict((k, k) for k in t)
            break

_install_lang()

@atexit.register
def _save_missing_translations():
    if _missing_translation:
        import pprint
        with open('missing_translations.txt', 'wt') as f:
            d = dict.fromkeys(_missing_translation, "")
            pprint.pprint({_lang:d}, stream=f)
