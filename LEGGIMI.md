PVCHECK: UN SEMPLICE TOOL PER LA VERIFICA AUTOMATICA
====================================================

Il tool richiede Python (provato con la versione 3.4) e si chiama
'pvcheck'.

E` invocabile passando come parametri:
- il file che contiene il caso di test;
- il nome dell'eseguibile da verificare;
- eventuali altri argomenti da passare all'eseguibile.

Ad esempio, dopo aver compilato l'esempio 'programma.c', e` possibile
provare lo script digitando il comando:

  ./pvcheck esempio.test ./programma 3

dove "3" e` un argomento da passare a 'programma' (il programma
d'esempio accetta come argomento i numeri da 0 a 8, producendo vari
comportamenti in modo da poter verificare le funzionalita` dello
script.


Un modo ancora piu` semplice di invocare lo script si puo` ottenere
rendendo eseguibile il file contente il test e facendolo iniziare con
uno "shebang" che richiami 'pvcheck'.  Fatto cio` si puo`
eseguire direttamente il caso di test come se fosse uno script:

  ./esempio.test ./programma 3


E` anche possibile eseguire test multipli opportunamente definiti in
uno stesso file (una "suite" di test):

  ./pvcheck esempio2.test ./programma2
    

Il formato del file di test e` abbastanza semplice.  I file di
esempio contiene dei commenti che lo descrivono brevemente.
