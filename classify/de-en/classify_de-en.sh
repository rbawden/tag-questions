SRC=cs
TRG=en

TAGDIR=/Users/rbawden/Documents/work/tag-questions-opensubs/
EXPDIR=$TAGDIR/classify/$SRC-$TRG  # where the experiment is kept
SCRIPTDIR=$TAGDIR/scripts
if [ $SRC == "fr" ]; then
    LEX=None
else
    LEX=/Users/rbawden/data/lexica/lexicon-$SRC.ftl.gz
fi
VW=/Users/rbawden/Documents/tools/vowpal_wabbit/vowpalwabbit/vw


# devsmall and testsmall
if [ $SRC == 'cs' ]; then
	division=2521957
    #division=2043619
elif [ $SRC == 'de' ]; then
    division=1029822
elif [ $SRC == 'fr' ]; then
	division=2519056
    #division=1630000
fi
testsetstart=$(($division+1))

# prepare all data for classification

# make directories if necessary
[ -d $EXPDIR ] || mkdir $EXPDIR

for folder in gold gtests references pred-seq pred-one model-seq model-seq/tuning \
		  model-one model-one/tuning baseline data; do
    [ -d $EXPDIR/$folder ] || mkdir $EXPDIR/$folder
done

<<COMMENT

# get gold data and postedited translations
echo "Getting gold labels"
for goldtype in tagnottag real gramMiscNone gramMiscTypeNone; do
    for set in train dev1 dev2 test; do
	if [ ! -f $EXPDIR/gold/$set.$goldtype.$SRC-$TRG.gz  ]; then
	    echo "Getting gold tags for $set ($goldtype)"
	    python3 $SCRIPTDIR/get_gold.py $set $SRC-$TRG $goldtype \
		    $TAGDIR/subcorpora/$SRC-$TRG/linenumbers \
		    $TAGDIR/datasets/$SRC-$TRG/$set.truecased.$SRC-$TRG.$TRG.gz \
		| gzip > $EXPDIR/gold/$set.$goldtype.$SRC-$TRG.gz
	fi
    done
done

for goldtype in tagnottag real gramMiscNone gramMiscTypeNone; do
    zcat $EXPDIR/gold/dev1.$goldtype.$SRC-$TRG.gz \
	 $EXPDIR/gold/dev2.$goldtype.$SRC-$TRG.gz \
	| gzip > $EXPDIR/gold/trainsmall.$goldtype.$SRC-$TRG.gz 
    zcat $EXPDIR/gold/test.$goldtype.$SRC-$TRG.gz \
    	| sed -n "$testsetstart,5000000000000p" \
	| gzip > $EXPDIR/gold/testsmall.$goldtype.$SRC-$TRG.gz
    zcat $EXPDIR/gold/test.$goldtype.$SRC-$TRG.gz \
    	| sed -n "1,${division}p" \
	| gzip > $EXPDIR/gold/devsmall.$goldtype.$SRC-$TRG.gz 
done


# line numbers for tags in small sets
for goldtype in tagnottag; do
    for set in trainsmall devsmall testsmall; do
	zcat $EXPDIR/gold/$set.$goldtype.$SRC-$TRG.gz | grep -n "True" | cut -d":" -f1 | \
	    gzip > $EXPDIR/gold/$set.$goldtype.linenumbers.$SRC-$TRG.gz
    done
done



# get datasets used
echo "Getting set datasets"
for typeproc in melttok  truecased; do
	for lang in $SRC $TRG; do
		zcat $TAGDIR/datasets/$SRC-$TRG/dev1.$typeproc.$SRC-$TRG.$lang.gz \
			 $TAGDIR/datasets/$SRC-$TRG/dev2.$typeproc.$SRC-$TRG.$lang.gz \
			| gzip > $TAGDIR/datasets/$SRC-$TRG/trainsmall.$typeproc.$SRC-$TRG.$lang.gz
		zcat $TAGDIR/datasets/$SRC-$TRG/test.$typeproc.$SRC-$TRG.$lang.gz \
			| sed -n "$testsetstart,5000000000000p" \
			| gzip > $TAGDIR/datasets/$SRC-$TRG/testsmall.$typeproc.$SRC-$TRG.$lang.gz
		zcat $TAGDIR/datasets/$SRC-$TRG/test.$typeproc.$SRC-$TRG.$lang.gz \
			| sed -n "1,${division}p" \
			| gzip > $TAGDIR/datasets/$SRC-$TRG/devsmall.$typeproc.$SRC-$TRG.$lang.gz
	done
done




# get reference translations from gold (remove question mark)
echo "Getting reference translations"
for set in train dev1 dev2 test; do
    if [ ! -f $EXPDIR/references/$set.all.$SRC-$TRG.$TRG.gz  ]; then
	python3 $SCRIPTDIR/final_translation.py \
		$TAGDIR/datasets/$SRC-$TRG/$set.truecased.$SRC-$TRG.$TRG.gz \
		$EXPDIR/gold/$set.real.$SRC-$TRG.gz \
		| gzip > $EXPDIR/references/$set.all.$SRC-$TRG.$TRG.gz
    fi
    if [ ! -f $EXPDIR/references/$set.tags.$SRC-$TRG.$TRG.gz  ]; then
	python3 $SCRIPTDIR/get-these-lines-from-numbers.py \
		$EXPDIR/references/$set.all.$SRC-$TRG.$TRG.gz \
		$TAGDIR/subcorpora/$SRC-$TRG/linenumbers/en_tag_questions.$set.list.$SRC-$TRG \
		| gzip > $EXPDIR/references/$set.tags.$SRC-$TRG.$TRG.gz
    fi
done

for subset in all; do
    zcat $EXPDIR/references/dev1.$subset.$SRC-$TRG.$TRG.gz \
	 $EXPDIR/references/dev2.$subset.$SRC-$TRG.$TRG.gz \
	  | gzip >  $EXPDIR/references/trainsmall.$subset.$SRC-$TRG.$TRG.gz
    zcat $EXPDIR/references/test.$subset.$SRC-$TRG.$TRG.gz \
	| sed -n "$testsetstart,5000000000000p" \
	| gzip > $EXPDIR/references/testsmall.$subset.$SRC-$TRG.$TRG.gz
    zcat $EXPDIR/references/test.$subset.$SRC-$TRG.$TRG.gz \
	| sed -n "1,${division}p" \
	| gzip > $EXPDIR/references/devsmall.$subset.$SRC-$TRG.$TRG.gz 
done



# get baselines - predictions and final postedited translations
echo "Getting baselines"
for set in dev1 dev2 test; do
    # baseline predictions
    python3 $SCRIPTDIR/get_gold.py $set $SRC-$TRG \
	    -baseline real $TAGDIR/subcorpora/$SRC-$TRG/linenumbers \
	    $TAGDIR/translations/$SRC-$TRG/$set.translated.melttok.$SRC-$TRG.$TRG.gz \
	| gzip > $EXPDIR/baseline/$set.pred.$SRC-$TRG.gz
    # baseline final translations
    python3 $SCRIPTDIR/final_translation.py \
	    $TAGDIR/translations/$SRC-$TRG/$set.translated.melttok.$SRC-$TRG.$TRG.gz \
	    $EXPDIR/baseline/$set.pred.$SRC-$TRG.gz \
	| gzip > $EXPDIR/baseline/$set.all.finaltranslations.$SRC-$TRG.$TRG.gz
    # just extract tags
    python3 $SCRIPTDIR/get-these-lines-from-numbers.py \
	    $EXPDIR/baseline/$set.all.finaltranslations.$SRC-$TRG.$TRG.gz \
	    $TAGDIR/subcorpora/$SRC-$TRG/linenumbers/en_tag_questions.$set.list.$SRC-$TRG \
	| gzip > $EXPDIR/baseline/$set.tags.finaltranslations.$SRC-$TRG.$TRG.gz
done

for typebaseline in pred all.finaltranslations; do
	
	lang=".$TRG" && [[ $typebaseline == pred ]]  && lang=""

	zcat $EXPDIR/baseline/dev1.$typebaseline.$SRC-$TRG$lang.gz \
	     $EXPDIR/baseline/dev2.$typebaseline.$SRC-$TRG$lang.gz \
	     | gzip >  $EXPDIR/baseline/trainsmall.$typebaseline.$SRC-$TRG$lang.gz 
	zcat $EXPDIR/baseline/test.$typebaseline.$SRC-$TRG$lang.gz \
	    | sed -n "$testsetstart,5000000000000p" \
		| gzip > $EXPDIR/baseline/testsmall.$typebaseline.$SRC-$TRG$lang.gz
	zcat $EXPDIR/baseline/test.$typebaseline.$SRC-$TRG$lang.gz \
	    | sed -n "1,${division}p" \
		| gzip > $EXPDIR/baseline/devsmall.$typebaseline.$SRC-$TRG$lang.gz 
done



# for tags
for set in trainsmall devsmall testsmall; do
	python3 $SCRIPTDIR/get-these-lines-from-numbers.py $EXPDIR/references/$set.all.$SRC-$TRG.$TRG.gz \
		$EXPDIR/gold/$set.tagnottag.linenumbers.$SRC-$TRG.gz | gzip > $EXPDIR/references/$set.tags.$SRC-$TRG.$TRG.gz

	python3 $SCRIPTDIR/get-these-lines-from-numbers.py $EXPDIR/baseline/$set.tags.finaltranslations.$SRC-$TRG.$TRG.gz \
        $EXPDIR/gold/$set.tagnottag.linenumbers.$SRC-$TRG.gz | gzip > $EXPDIR/baseline/$set.tags.finaltranslations.$SRC-$TRG.$TRG.gz
done



zcat $TAGDIR/translations/$SRC-$TRG/dev1.translated.melttok.$SRC-$TRG.$TRG.gz \
     $TAGDIR/translations/$SRC-$TRG/dev2.translated.melttok.$SRC-$TRG.$TRG.gz \
    | gzip > $TAGDIR/translations/$SRC-$TRG/trainsmall.translated.melttok.$SRC-$TRG.$TRG.gz



# do gtests and get word gtest scores
for lang in $SRC $TRG; do
    if [ "$lang" == "$TRG" ]; then
		lang=$TRG
		set=trainsmall
		corpus=$TAGDIR/translations/$SRC-$TRG/$set.translated.melttok.$SRC-$TRG.$lang.gz
		trans=.trans
    else
		lang=$SRC
		set=trainsmall
		corpus=$TAGDIR/datasets/$SRC-$TRG/$set.truecased.$SRC-$TRG.$lang.gz
		trans=""
    fi
    for gram in 1 2 3; do
		echo "Calculating gtest scores for $set.$lang ($gram-gram)"
		if [ ! -f $EXPDIR/gtests/gtest.$set.${gram}g$trans.$SRC-$TRG.$lang.gz  ]; then
			python3 $SCRIPTDIR/gtest_fromgold.py \
					$corpus \
					$EXPDIR/gold/$set.tagnottag.$SRC-$TRG.gz \
					$gram \
				| gzip > $EXPDIR/gtests/gtest.$set.${gram}g$trans.$SRC-$TRG.$lang.gz
		fi
    done
done


# zcat $EXPDIR/data/dev1.gramMiscNone.$SRC-$TRG.gz \
# 	 $EXPDIR/data/dev2.gramMiscNone.$SRC-$TRG.gz \
# 	| cut -d " " -f 2- > tmp.trainsmall
# zcat $EXPDIR/data/test.gramMiscNone.$SRC-$TRG.gz \
# 	| sed -n "$testsetstart,5000000000000p" \
# 	| cut -d " " -f 2- > tmp.trainsmall
		  
# for tagtype in real gramMiscTypeNone; do
	
# 	paste -d " " <(zcat $EXPDIR/gold/trainsmall.$tagtype.$SRC-$TRG.gz) \
# 		tmp.trainsmall | gzip >  $EXPDIR/data/trainsmall.$tagtype.$SRC-$TRG.gz 
# 	zcat $EXPDIR/data/test.gramMiscNone.$SRC-$TRG.gz \
# 	    | sed -n "$testsetstart,5000000000000p" \
# 		| gzip > $EXPDIR/data/testsmall.$tagtype.$SRC-$TRG.gz
# 	zcat $EXPDIR/data/test.gramMiscNone.$SRC-$TRG.gz \
# 	    | sed -n "1,${division}p" \
# 		| gzip > $EXPDIR/data/devsmall.$tagtype.$SRC-$TRG$.gz 
# done



# generate features:
#     - tagnottag = 1st classifier (just source features)
#     - real = 2nd classifier (source and target features)
for tagtype in real; do
    for set in trainsmall devsmall testsmall; do
	echo "Generating features for $set ($tagtype)"
	if [ "$set" != train ] || [ "$tagtype" != real ]; then
	    python3 $SCRIPTDIR/generate_features.py -l $SRC-$TRG -d $set \
		    -t $tagtype $TAGDIR/datasets/$SRC-$TRG $TAGDIR $LEX \
		| gzip > $EXPDIR/data/$set.$tagtype.$SRC-$TRG.gz
	fi
    done
done



# get data w/ labels gram/misc/none and gram/misctype/none
for tagtype in gramMiscNone gramMiscTypeNone; do
    for set in train trainsmall devsmall testsmall; do
	zcat $EXPDIR/data/$set.real.$SRC-$TRG.gz | cut -d " " -f2- > tmp.data.$$
	zcat $EXPDIR/gold/$set.$tagtype.$SRC-$TRG.gz > tmp.gold.$$
	paste -d " " tmp.gold.$$ tmp.data.$$ | gzip > $EXPDIR/data/$set.$tagtype.$SRC-$TRG.gz
	rm tmp.gold.$$ tmp.data.$$
    done
done

#COMMENT
#trainsmall devsmall
# get named labels, num labels etc.
echo "Getting label names and numbers and counts"
for tagtype in gramMiscNone gramMiscTypeNone real; do
    for set in train trainsmall; do
		zcat $EXPDIR/gold/$set.$tagtype.$SRC-$TRG.gz | sort | uniq -c > $EXPDIR/model-seq/classcounts.$tagtype.$set.$SRC-$TRG
		zcat $EXPDIR/gold/$set.$tagtype.$SRC-$TRG.gz | sort -u | perl -pe 's/\n/,/g' | perl -pe 's/,$//g' > $EXPDIR/model-seq/named_labels.$tagtype.$set.$SRC-$TRG
		cat $EXPDIR/model-seq/named_labels.$tagtype.$set.$SRC-$TRG | perl -pe 's/$/\n/' | perl -pe 's/,/\n/g'  | wc -l | perl -pe 's/^ *//' > $EXPDIR/model-seq/num_labels.$tagtype.$set.$SRC-$TRG
    done
done

#<<COMMENT

# train all-in-one model
echo "Training all-in-one model"

printf %s "" > $EXPDIR/model-one/tuningweights.devsmall.$SRC-$TRG 
zcat $EXPDIR/data/devsmall.real.$SRC-$TRG.gz  | cut -d" " -f2- > $EXPDIR/model-one/tuningtmp
for weight in 0 0.00005 0.001 ; do \
	printf %s "$weight " >> $EXPDIR/model-one/tuningweights.devsmall.$SRC-$TRG 
	zcat $EXPDIR/data/trainsmall.real.$SRC-$TRG.gz | eval "$(python3 $SCRIPTDIR/calculate_weighting.py $EXPDIR/model-seq/classcounts.real.trainsmall.$SRC-$TRG $weight)" \
		| perl -pe 's/\t/ |f /' | $VW -f $EXPDIR/model-one/tuning/$weight.trainsmall.real.$SRC-$TRG -q ff --l2=1e-6 --ftrl \
										--named_labels `cat $EXPDIR/model-seq/named_labels.real.trainsmall.$SRC-$TRG` \
										--oaa `cat $EXPDIR/model-seq/num_labels.real.trainsmall.$SRC-$TRG` ; \
	perl -pe 's/^/ |f /' $EXPDIR/model-one/tuningtmp | $VW -i $EXPDIR/model-one/tuning/$weight.trainsmall.real.$SRC-$TRG \
													-t -p $EXPDIR/model-one/tuning/pred.$weight.devsmall.real.$SRC-$TRG
	python3 $SCRIPTDIR/newevaluation.py $EXPDIR/gold/devsmall.real.$SRC-$TRG.gz \
			$EXPDIR/model-one/tuning/pred.$weight.devsmall.real.$SRC-$TRG -t article -noshow >> $EXPDIR/model-one/tuningweights.devsmall.$SRC-$TRG 
	rm $EXPDIR/model-one/tuning/pred.$weight.devsmall.real.$SRC-$TRG ; \
	rm $EXPDIR/model-one/tuning/$weight.trainsmall.real.$SRC-$TRG ; \
done 
rm $EXPDIR/model-one/tuningtmp

COMMENT

# train sequential model - predict TQ forms (none and lex and gram TQ forms)
zcat $EXPDIR/data/testsmall.gramMiscNone.$SRC-$TRG.gz  \
    | cut -d" " -f2- > $EXPDIR/model-seq/tuning/tuningtmp.testsmall

for lambda in 0 0.0001 0.001 0.01 0.25 0.5 0.75 1 ; do
    echo "************** Starting 1st weight @ $lambda **************"                                                                                                                               
    bash $SCRIPTDIR/train_model_gramMiscNone.sh \
		 $lambda testsmall $SRC-$TRG $SCRIPTDIR $VW $EXPDIR/model-seq/tuning $EXPDIR                                                                                   
    
    for lambdalex in 0 0.0001 0.001 0.01 0.25 0.5 0.75 1 ; do
		echo "****** Lex weight @ $lambdalex ******"
		bash $SCRIPTDIR/train_model_lexgram.sh \
			 $lambda $lambdalex testsmall $SRC-$TRG $SCRIPTDIR $VW \
			 $EXPDIR/model-seq/tuning $EXPDIR >> $EXPDIR/model-seq/tuningweights.testsmall.$SRC-$TRG 
		
		#rm $EXPDIR/model-seq/tuning/$lambda.$lambdalex.trainsmall.lex.$SRC-$TRG
		#rm $EXPDIR/model-seq/tuning/pred.$lambda.$lambdalex.testsmall.lex.$SRC-$TRG 
		#rm $EXPDIR/model-seq/tuning/pred.$lambda.$lambdalex.testsmall.real.final.$SRC-$TRG 
		#rm $EXPDIR/model-seq/tuning/pred.$lambda.$lambdalex.testsmall.restucklex.$SRC-$TRG 
		#rm $EXPDIR/model-seq/tuning/pred.$lambda.$lambdalex.testsmall.gramMiscTypeNone.$SRC-$TRG
    done
    #rm $EXPDIR/model-seq/tuning/$lambda.trainsmall.gramMiscNone.$SRC-$TRG 
    #rm $EXPDIR/model-seq/tuning/pred.$lambda.testsmall.gramMiscNone.$SRC-$TRG 
    #rm $EXPDIR/model-seq/tuning/pred.$lambda.trainsmall.gramMiscNone.$SRC-$TRG
    #rm $EXPDIR/model-seq/tuning/pred.$lambda.$lambdalex.testsmall.real.final.$SRC-$TRG
done 
rm $EXPDIR/model-seq/tuning/tuningtmp.testsmall $EXPDIR/model-seq/tuning/lexlines.testsmall
rm $EXPDIR/model-seq/tuning/lexlines.trainsmall
rm $EXPDIR/model-seq/tuning/lexexamples.testsmall 
rm $EXPDIR/model-seq/tuning/lexexamples.trainsmall


echo "Enter the best two weights (eg. 0.01 0.0001) into $EXPDIR/model-seq/weights.devsmall.$SRC-$TRG for model-seq"
echo "Enter the best weight into $EXPDIR/model-one/weights.devsmall.$SRC-$TRG for model-one and then press enter"
read

# make predictions


echo "Making predictions"

for set in testsmall; do

	lambdaone=$(cat $EXPDIR/model-one/weights.devsmall.$SRC-$TRG | cut -d" " -f 1)
	# model-one (retrain if necessary)
	if [ ! -f $EXPDIR/model-one/$lambdaone.trainsmall.real.$SRC-$TRG ]; then
		#zcat $EXPDIR/data/$set.gramMiscNone.$SRC-$TRG.gz  | cut -d" " -f2- > $EXPDIR/model-one/tuningtmp.$set
		zcat $EXPDIR/data/trainsmall.real.$SRC-$TRG.gz | \
			eval "$(python3 $SCRIPTDIR/calculate_weighting.py $EXPDIR/model-seq/classcounts.real.trainsmall.$SRC-$TRG $lambdaone)" \
			| perl -pe 's/\t/ |f /' | $VW -f $EXPDIR/model-one/$lambdaone.trainsmall.real.$SRC-$TRG  \
										  --named_labels `cat $EXPDIR/model-seq/named_labels.real.trainsmall.$SRC-$TRG` \
										  --oaa `cat $EXPDIR/model-seq/num_labels.real.trainsmall.$SRC-$TRG` \
										  -q ff --l2=1e-6 --ftrl
	fi
	# predict
	zcat $EXPDIR/data/$set.real.$SRC-$TRG.gz | cut -d" " -f2- | perl -pe 's/^/ |f /' \
		| $VW -i $EXPDIR/model-one/$lambdaone.trainsmall.real.$SRC-$TRG \
			  -t -p $EXPDIR/pred-one/pred.$lambdaone.$set.real.$SRC-$TRG 

	
	# model-seq
    zcat $EXPDIR/data/$set.gramMiscNone.$SRC-$TRG.gz  | cut -d" " -f2- > $EXPDIR/pred-seq/tuningtmp.$set
	lambda=$(cat $EXPDIR/model-seq/weights.devsmall.$SRC-$TRG | cut -d" " -f 1)
	lambdalex=$(cat $EXPDIR/model-seq/weights.devsmall.$SRC-$TRG | cut -d" " -f 2)

	bash $SCRIPTDIR/train_model_gramMiscNone.sh $lambda $set $SRC-$TRG $SCRIPTDIR \
		 $VW $EXPDIR/pred-seq $EXPDIR True # reuse models if they exist
	bash $SCRIPTDIR/train_model_lexgram.sh $lambda $lambdalex $set $SRC-$TRG $SCRIPTDIR \
		 VW $EXPDIR/pred-seq $EXPDIR True > $EXPDIR/pred-seq/$set.pred.$SRC-$TRG.eval # reuse trained models if they exist
	
	# remove unwanted files
	rm $EXPDIR/pred-seq/pred.$lambda.trainsmall.gramMiscNone.$SRC-$TRG \
	   $EXPDIR/pred-seq/pred.$lambda.$set.gramMiscNone.$SRC-$TRG \
	   $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.$gramMiscTypeNone.$SRC-$TRG \
	   $EXPDIR/pred-seq/lexexamples.fortraining.trainsmall \
	   $EXPDIR/pred-seq/named_labels.lex.trainsmall.var.$SRC-$TRG \
	   $EXPDIR/pred-seq/num_labels.lex.trainsmall.var.$SRC-$TRG \
	   $EXPDIR/pred-seq/classcounts.lex.trainsmall.var.$SRC-$TRG \
	   $EXPDIR/pred-seq/tuningtmp.$set $EXPDIR/model-one/tuningtmp.$set

	#rm $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.restucklex.$SRC-$TRG \

	# evaluate predictions-seq
	python $SCRIPTDIR/newevaluation.py -noshow -t real $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.real.final.$SRC-$TRG \
			> $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.real.final.$SRC-$TRG.eval.real
	
	python $SCRIPTDIR/newevaluation.py -noshow -t article $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.real.final.$SRC-$TRG \
			> $EXPDIR/pred-seq/pred.$lambda.$lambdalex.$set.real.final.$SRC-$TRG.eval.article

	# evaluate predictions-one
	python $SCRIPTDIR/newevaluation.py -noshow -t real $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/pred-one/pred.$lambdaone.$set.real.$SRC-$TRG \
			> $EXPDIR/pred-one/pred.$lambdaone.$set.real.final.$SRC-$TRG.eval.real
	
	python $SCRIPTDIR/newevaluation.py -noshow -t article $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/pred-one/pred.$lambdaone.$set.real.$SRC-$TRG \
			> $EXPDIR/pred-one/pred.$lambdaone.$set.real.final.$SRC-$TRG.eval.article
	
	# evaluate baseline
	python $SCRIPTDIR/newevaluation.py -noshow -t real $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/baseline/$set.pred.$SRC-$TRG.gz \
			> $EXPDIR/baseline/$set.pred.$SRC-$TRG.eval.real
	python $SCRIPTDIR/newevaluation.py -noshow -t article $EXPDIR/gold/$set.real.$SRC-$TRG.gz $EXPDIR/baseline/$set.pred.$SRC-$TRG.gz \
			> $EXPDIR/baseline/$set.pred.$SRC-$TRG.eval.article

done

exit

