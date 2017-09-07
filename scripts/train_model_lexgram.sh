#!/bin/sh

lambda=$1
lambdalex=$2
set=$3 # prediction data
langpair=$4
scriptdir=$5
vw=$6
outputdir=$7
expdir=$8
reuse=$9 # true or false

# Train lex model
#numexamples=`wc -l $outputdir/lexexamples.fortraining.trainsmall`
#echo ">> Training lex classifier on $numexamples"
#read


if [ "$reuse" == "True" ] && [ -f "$outputdir/$lambda.$lambdalex.trainsmall.lex.$langpair" ]; then
	echo "Reloading lex model from $outputdir/$lambda.$lambdalex.trainsmall.lex.$langpair"
else
	cat $outputdir/lexexamples.fortraining.trainsmall | perl -pe "s/\'/\-/g" \
		| eval "$(python3 $scriptdir/calculate_weighting.py $outputdir/classcounts.lex.trainsmall.var.$langpair $lambdalex)" \
		| perl -pe 's/\t/ |f /' | $vw -f $outputdir/$lambda.$lambdalex.trainsmall.lex.$langpair \
									  --named_labels `cat $outputdir/named_labels.lex.trainsmall.var.$langpair` \
									  --oaa `cat $outputdir/num_labels.lex.trainsmall.var.$langpair` -q ff --l2=1e-6 --ftrl
fi



# Predict on $set set
perl -pe 's/^/ |f /' $outputdir/lexexamples.$set \
	| $vw -i $outputdir/$lambda.$lambdalex.trainsmall.lex.$langpair \
		  -t -p $outputdir/pred.$lambda.$lambdalex.$set.lex.$langpair 

# Restick lexical predictions to main predictions
python $scriptdir/restick_lex_preds.py $outputdir/pred.$lambda.$set.gramMiscNone.$langpair \
		$outputdir/pred.$lambda.$lambdalex.$set.lex.$langpair $outputdir/lexlines.$set \
		> $outputdir/pred.$lambda.$lambdalex.$set.restucklex.$langpair 

# Predict grammatical rules
python $scriptdir/rule-based.py $expdir/baseline/$set.all.finaltranslations.$langpair.en.gz \
		-c $outputdir/pred.$lambda.$lambdalex.$set.restucklex.$langpair \
		> $outputdir/pred.$lambda.$lambdalex.$set.real.final.$langpair 

# Turn into gramMiscTypeNone for evaluation
paste -d "&" $outputdir/pred.$lambda.$lambdalex.$set.restucklex.$langpair \
	  $outputdir/pred.$lambda.$lambdalex.$set.real.final.$langpair \
	| perl -pe 's/[^&\s]+&none/none&none/' \
	| perl -pe 's/([^&\s]+)&([^&\s]+)/\1/' \
		   > $outputdir/pred.$lambda.$lambdalex.$set.gramMiscTypeNone.$langpair

# Evaluate
res1=`python $scriptdir/newevaluation.py $expdir/gold/$set.real.$langpair.gz \
		$outputdir/pred.$lambda.$lambdalex.$set.real.final.$langpair -t article -noshow`

#res1=`python $scriptdir/newevaluation.py $expdir/gold/$set.gramMiscTypeNone.$langpair.gz \
#		$outputdir/pred.$lambda.$lambdalex.$set.gramMiscTypeNone.$langpair -t gramMiscTypeNone -noshow`

#res2=`python3 $scriptdir/newevaluation.py $expdir/gold/$set.real.$langpair.gz \
#		$outputdir/pred.$lambda.$lambdalex.$set.real.final.$langpair -t real -noshow`

# Print out result
echo "$lambda $lambdalex $res1 $res2"
