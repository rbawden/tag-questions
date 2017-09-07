#!/bin/sh


lambda=$1
set=$2 # tuning data
langpair=$3
scriptdir=$4
vw=$5
outputdir=$6
expdir=$7
reuse=$8

modeldata=trainsmall
train=trainsmall


#| perl -pe "s/'/\-/g" |   \

#if [ "$reuse" == "True" ] && [ -f "$outputdir/$lambda.$train.gramMiscNone.$langpair" ]; then
#	echo "Reloading gram-misc-none model from $outputdir/$lambda.$train.gramMiscNone.$langpair"
#else
	echo "Training gram-misc-none model $expdir $outputdir"
	echo "python3 $scriptdir/calculate_weighting.py $expdir/model-seq/classcounts.gramMiscNone.$train.$langpair $lambda)"
	
	# Train $expdir/model-seq on dev $expdir/data (weighted according to $lambda)
	zcat $expdir/data/$modeldata.gramMiscNone.$langpair.gz | \
		eval "$(python3 $scriptdir/calculate_weighting.py $expdir/model-seq/classcounts.gramMiscNone.$train.$langpair $lambda)" | \
		perl -pe 's/\t/ |f /' | bash $scriptdir/get_src_features_only.sh | tee toto | \
		$vw -f $outputdir/$lambda.$modeldata.gramMiscNone.$langpair  \
			--named_labels `cat $expdir/model-seq/named_labels.gramMiscNone.$modeldata.$langpair` \
			--oaa `cat $expdir/model-seq/num_labels.gramMiscNone.$modeldata.$langpair` -q ff --l2=1e-6 --ftrl
#fi
	
# $expdir/predict on train set
zcat $expdir/data/$train.gramMiscNone.$langpair.gz | perl -pe 's/\s/ |f /' | bash $scriptdir/get_src_features_only.sh | \
	$vw -i $outputdir/$lambda.$modeldata.gramMiscNone.$langpair  \
		-t -p $outputdir/pred.$lambda.$train.gramMiscNone.$langpair

# $expdir/predict on $set set
perl -pe 's/^/ |f /' $outputdir/tuningtmp.$set | bash $scriptdir/get_src_features_only.sh |\
	$vw -i $outputdir/$lambda.$modeldata.gramMiscNone.$langpair \
		-t -p $outputdir/pred.$lambda.$set.gramMiscNone.$langpair

# Extract lines that are $expdir/predicted as lexical tags from train
cat $outputdir/pred.$lambda.$train.gramMiscNone.$langpair |\
	grep "^misc" -n | cut -d":" -f1 > $outputdir/lexlines.$train
python3 $scriptdir/get-these-lines-from-numbers.py $expdir/data/$train.gramMiscTypeNone.$langpair.gz \
			$outputdir/lexlines.$train > $outputdir/lexexamples.fortraining.$train 

# Extract lines that are $expdir/predicted as lexical tags from $set
cat $outputdir/pred.$lambda.$set.gramMiscNone.$langpair \
	| grep -n "^misc" - | cut -d":" -f1 > $outputdir/lexlines.$set 
python3 $scriptdir/get-these-lines-from-numbers.py $outputdir/tuningtmp.$set $outputdir/lexlines.$set \
			> $outputdir/lexexamples.$set

# Get named labels and num labels		
cat $outputdir/lexexamples.fortraining.$train | cut -d" " -f 1 | sort | uniq | perl -pe 's/\n/,/g' |\
	perl -pe 's/,$//' > $outputdir/named_labels.lex.$train.var.$langpair
cat $outputdir/named_labels.lex.$train.var.$langpair | perl -pe 's/,/\n/g' | sed -n '=' |\
	wc -l > $outputdir/num_labels.lex.$train.var.$langpair

cat $outputdir/lexexamples.fortraining.$train  | cut -d" " -f1 |\
	sort | uniq -c > $outputdir/classcounts.lex.$train.var.$langpair  ; \


