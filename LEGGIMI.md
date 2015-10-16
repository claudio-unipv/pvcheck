# pvcheck
un tool per la verifica automatica di programmi

Il tool richiede Python (provato con la versione 3.4) e la sua esecuzione non richiede alcun tipo di installazione
(basta copiare lo script in una direcotry da cui possa essere eseguito).

È invocabile passando come parametri:
- il file che contiene il caso di test;
- il nome dell'eseguibile da verificare;
- eventuali altri argomenti da passare all'eseguibile.

Ad esempio, dopo aver compilato l'esempio 'program.c', è possibile
provare lo script digitando il comando:

```
./pvcheck esempio.test ./program 3
```

dove "3" è un argomento da passare a 'program' (il programma
d'esempio accetta come argomento i numeri da 0 a 8, producendo vari
comportamenti in modo da poter verificare le funzionalità dello
script.

È anche possibile eseguire test multipli opportunamente definiti in
uno stesso file (una "suite" di test):

```
./pvcheck esempio2.test ./program2
```    

Il formato del file di test è abbastanza semplice.  I file di
esempio contiene dei commenti che lo descrivono brevemente.
