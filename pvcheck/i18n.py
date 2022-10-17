# -*- coding: utf-8 -*-

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
import sys
import atexit


############################################################
# Translation function
############################################################

def translate(text):
    """Translate the text in the current language."""
    try:
        return _strings[text]
    except KeyError:
        pass
    # try removing the last char since translation loading strips the end spaces
    try:
        return _strings[text[:-1]] + text[-1]
    except KeyError:
        _missing_translation.add(text)
        s = (text if len(text) < 15 else text[:15] + "...")
        print("[TT] Warning: missing translation for '%s'" % s, file=sys.stderr)
        return text


############################################################
# Extra functions
############################################################

def register_translation(english_text, language, translation):
    """Function to add translations from other modules."""
    if _lang == language:
        _strings[english_text] = translation
    elif _lang == "en":
        _strings[english_text] = english_text


############################################################
# Application messages
############################################################

_strings = {}
_missing_translation = set()
_lang = 'en'

_translations = {
    'it': {
        "Run tests to verify the correctness of a program.": "Esegue dei test per verificare la correttezza di un programma.",
        "set the verbosity level, where the level must be an integer between 0 (minimum) and 4 (maximum). The default value is 3.": "imposto il livello di verbosità.  Il livello deve essere un valore intero tra 0 (minimo) e 3 (massimo).  Il default è 2.",
        "set how many seconds it should be waited for the termination of the program.  The default is 10 seconds.": "imposta per quanti secondi bisogna attendere la terminazione del programma.  Il default è pari a 10 secondi.",
        "cut the output of the program to a maximum of L lines.  The default is 10000.": "taglia l'output del programma ad un massimo di L linee.  Il default è 10000.",
        "reports up to N errors per section (default 4).": "riporta fino ad un massimo di N errori per sezione (default 4).",
        "uses the specified configuration file.": "utilizza il file di configurazione specificato.",
        "enable or disable colored output (default AUTO).": "abilita o disabilita l'output colorato (default AUTO).",
        "use Valgrind (if installed) to check memory usage.": "utilizza Valgrind (se installato) per controllare l'utilizzo della memoria.",
        "select the output type.": "seleziona il tipo di output.",
        "specify the name of the file used for logging.  The default is ~/.pvcheck.log.": "specifica il nome del file usato per il logging. Il default è ~/.pvcheck.log.",
        "print this message and exit.": "stampa questo messaggio ed esce.",
        "list all the available tests.": "mostra tutti i test disponibili.",
        "run only the selected test.": "esegue solo il test indicato.",
        "export in a file the input arguments from the selected test.": "salva in un file gli argomenti di input dal test indicato.",
        "ERROR": "ERRORE",
        "OK": "OK",
        "WARNING!": "ATTENZIONE!",
        "COMMAND LINE": "RIGA DI COMANDO",
        "<temp.file>": "<file temp.>",
        "INPUT": "INPUT",
        "Input:": "Input:",
        "OUTPUT": "OUTPUT",
        "TEMPORARY FILE": "FILE TEMPORANEO",
        "TEST": "TEST",
        "line %d": " riga %d",
        "(expected '%s'": " (atteso '%s'",
        ", got '%s')": "ottenuto '%s')",
        "unexpected line '%s'": "riga inattesa '%s'",
        "missing line (expected '%s')": "riga mancante (atteso '%s')",
        "wrong number of lines (expected %d, got %d)": "numero di righe errato (atteso %d, ottenuto %d)",
        "line %d is wrong  (expected '%s', got '%s')": "riga %d errata  (atteso '%s', ottenuto '%s')",
        "The first %d lines matched correctly": "Le prime %d righe sono corrette",
        "(... plus other %d errors ...)": "(... più altri %d errori ...)",
        "ACTUAL OUTPUT": "OUTPUT EFFETTIVO",
        "EXPECTED OUTPUT": "OUTPUT ATTESO",
        "detailed comparison": "confronto dettagliato",
        "<nothing>": "<niente>",
        "missing section": "sezione mancante",
        "empty section": "sezione vuota",
        "extra section": "sezione extra",
        "Invalid parameter": "Parametro non valido",
        "Invalid parameter ('%s')": "Parametro non valido ('%s')",
        "Invalid parameter ('%d')": "Parametro non valido('%d')",
        "Invalid parameter ('%f')": "Parametro non valido('%f')",
        "TIMEOUT EXPIRED: PROCESS TERMINATED": "TEMPO LIMITE SCADUTO: PROCESSO TERMINATO",
        "TOO MANY OUTPUT LINES": "TROPPE LINEE DI OUTPUT",
        "PROCESS ENDED WITH A FAILURE": "PROCESSO TERMINATO CON UN FALLIMENTO",
        "(SEGMENTATION FAULT)": "(SEGMENTATION FAULT)",
        "(ERROR CODE {status})": "(CODICE D'ERRORE {status})",
        "FAILED TO RUN THE FILE '{progname}'": "IMPOSSIBILE ESEGUIRE IL FILE '{progname}'",
        "(the file does not exist)": "(file inesistente)",
        "(... plus other %d lines ...)": "(... più altre %d righe ...)",
        "SUMMARY": "RIEPILOGO",
        "Summary": "Riepilogo",
        "summary": "riepilogo",
        "successes": "successi",
        "Successes": "Successi",
        "warnings": "avvertimenti",
        "Warnings": "Avvertimenti",
        "errors": "errori",
        "Errors": "Errori",
        "<program>": "<programma>",
        "CODE": "CODICE",
        "TOTAL": "TOTALE",
        "Test number %d doesn't exist.": "Il test numero %d non esiste.",
        "Use './pvcheck info' to list all the available tests.": "Utilizza './pvcheck info' per vedere tutti i test disponibili.",
        "Error: Can't export test number %d.": "Errore: Impossibile esportare il test numero %d.",
        "file containing the tests to be performed (default pvcheck.test).": "file contenente i test da eseguire (default pvcheck.test).",
        "file containing the tests to be performed.": "file contenente i test da eseguire.",
        "program to be tested.": "programma da testare.",
        "any arguments of the program to be tested.": "eventuali argomenti del programma da testare.",
        "[run|info|export] --help for command help (default=run)": "[run|info|export] --help per l'help di un comando (default=run)",
        "test a program.": "testa un programma.",
        "Test Result": "Risultato Test",
        "positional arguments": "argomenti posizionali",
        "optional arguments": "argomenti opzionali",
        "show this help message and exit": "mostra questo messaggio ed esce",
        "show program's version number and exit": "mostra la versione del programma ed esce",
        "unrecognized arguments: %s'": "argomento %s non riconosciuto",
        "not allowed with argument %s": "l'argomento %s non é consentito",
        "ignored explicit argument %r": "ignorato l'argomento esplicito %r",
        "too few arguments": "troppi pochi argomenti ",
        "argument %s is required": "é necessario l'argomento %s",
        "one of the arguments %s is required": "é necessario uno dei seguenti argomenti %s",
        "expected one argument": "atteso un argomento",
        "expected at most one argument": "atteso al piú un argomento",
        "expected at least one argument": "atteso almeno un argomento",
        "expected %s argument(s)": "atteso argomento %s",
        "ambiguous option: %s could match %s": "opzione ambigua: %s puó coincidere con %s",
        "unexpected option string: %s": "opzione string non attesa: %s",
        "%r is not callable": "%r non é chiamabile",
        "invalid %s value: %r": "non valido %s valore: %r",
        "invalid choice: %r (choose from %s)": "scelta non valida: %r (i parametri disponibili sono %s)",
        "%s: error: %s": "%s: errore: %s",
        "unrecognized arguments: %s": "argomento non riconosciuto: %s",
        "Command line: %s": "Riga di comando: %s",
        "FAILED TO RUN THE FILE '{progname}' the file does not exist)": "ERRORE NELL'ESECUZIONE DEL FILE '{progname}' il file non esiste)",
        "Lines %d-%d/%d": "Righe %d-%d/%d",
        "PROCESS ENDED WITH A FAILURE (SEGMENTATION FAULT)": "IL PROCESSO E` TERMINATO CON UN FALLIMENTO (SEGMENTATION FAULT)",
        "PROGRAM'S OUTPUT:": "OUTPUT DEL PROGRAMMA:",
        "SUMMARY:": "SOMMARIO:",
        "TEMP_FILE": "FILE_TEMPORANEO",
        "Temporary file:": "File temporaneo:",
        "Test case %d of %d (%s)": "Caso di test %d di %d (%s) ",
        "Test title: %s": "Titolo del test: %s",
        "[Press 'h' for help]": "[Premere 'h' per l'aiuto]",
        "enables the interactive mode.": "abilita la modalita` interattiva.",
        "expected": "atteso",
        "missing line": "riga mancante",
        "passes": "passati",
        "this line was not expected": "questa riga e` inattesa",
        "TEST RUNNING": "TEST IN ESECUZIONE",
        "TEST COMPLETED": "TEST TERMINATO",
        "section [%s] is missing": "sezione [%s] non trovata",
        "execution failed": "esecuzione fallita",
        "%(prog)s: error: %(message)s\n": "%(prog)s: errore: %(message)s\n",
        "the following arguments are required: %s": "i seguenti argomenti sono richiesti: %s",
        "usage: ": "utilizzo: ",
        'file containing the tests to be exported.': "file contenente i test da salvare.",
        "number of the test to export as returned by the 'info' command.": "numero del test da salvare come restituito dal comando 'info'."
    }
}


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
            _strings = {k: k for k in t}
            break


_install_lang()


@atexit.register
def _save_missing_translations():
    if _missing_translation:
        import pprint
        with open('missing_translations.txt', 'wt') as f:
            d = dict.fromkeys(_missing_translation, "")
            pprint.pprint({_lang: d}, stream=f)
