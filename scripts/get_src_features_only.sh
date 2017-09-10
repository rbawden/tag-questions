#!/bin/bash

perl -CS -Mutf8 -pe "s/blaaah\S+//g;"

# perl -CS -Mutf8 -pe "s/firstWordTrans\S+//g; s/first2WordsTrans\S+//g; s/first3WordsTrans\S+//g; s/first4WordsTrans\S+//g; s/tagTrans\S+//g; s/lastAux\S+//g; s/lastPron\S+//g; s/hasParallelReplyEN\S*?//g; s/hasParallelVerbNnA\S*?//g; s/hasParallelVerbENB\S*?//g; s/hasReplyTrans\S*?//g; s/isAQuestionTrans\S*?//g; s/hasParallelVerbENB\S*?//g; s/gramTgt\S+//g; s/.+?gramTgt\S+//g"

# perl -CS -Mutf8 -pe "s/firstWordTrans\S+//g; s/first2WordsTrans\S+//g; s/first3WordsTrans\S+//g; s/first4WordsTrans\S+//g; s/tagTrans\S+//g; s/lastAux\S+//g; s/lastPron\S+//g; s/hasParallelReplyEN\S*?//g; s/hasParallelVerbNnA\S*?//g; s/hasParallelVerbENB\S*?//g; s/hasReplyTrans\S*?//g; s/isAQuestionTrans\S*?//g; s/hasParallelVerbENB\S*?//g; s/gramTgt\S+//g"


