# check that all add up correctly

# folder=/Users/rbawden/Documents/data/parallel/OpenSubtitles2016/de-en_2000-2016/subcorpora/line_numbers
# folder=/Users/rbawden/Documents/work/tag-questions-opensubs/subcorpora/fr-en/line_numbers
# suffix=list

folder=$1 # linenumber folder
dataset=$2 # train, dev1, dev2 or test
langpair=$3

suffix=$dataset.list

tag=$folder/en_tag_questions.$suffix.$langpair
gramtag=$folder/en_tag_questions_gram.$suffix.$langpair
misctag=$folder/en_tag_questions_misc.$suffix.$langpair
grampostag=$folder/en_tag_questions_gram-postag.$suffix.$langpair
gramnegtag=$folder/en_tag_questions_gram-negtag.$suffix.$langpair
gramposanchor=$folder/en_tag_questions_gram-posanchor.$suffix.$langpair
gramneganchor=$folder/en_tag_questions_gram-neganchor.$suffix.$langpair
gramnegtagposanchor=$folder/en_tag_questions_gram-negtag-posanchor.$suffix.$langpair
gramnegtagneganchor=$folder/en_tag_questions_gram-negtag-neganchor.$suffix.$langpair
grampostagposanchor=$folder/en_tag_questions_gram-postag-posanchor.$suffix.$langpair
grampostagneganchor=$folder/en_tag_questions_gram-postag-neganchor.$suffix.$langpair
misctagpos=$folder/en_tag_questions_misc-posanchor.$suffix.$langpair
misctagneg=$folder/en_tag_questions_misc-neganchor.$suffix.$langpair


big=`wc -l $tag | tr -s " " | cut -d" " -f2`
small1=`wc -l $gramtag | tr -s " " | cut -d" " -f2`
small2=`wc -l $misctag | tr -s " " | cut -d" " -f2`

if [ $((big)) -ne $((small1+small2))  ]; then
	>&2 echo "(ERROR) gramtag + misctag <> tag (ERROR)"
	exit 1
else
	echo "gramtag + misctag = tag (GOOD)"
fi


big=`wc -l $gramtag | tr -s " " | cut -d" " -f2`
small1=`wc -l $grampostag | tr -s " " | cut -d" " -f2`
small2=`wc -l $gramnegtag | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small1+small2))  ]; then
	>&2 echo "(ERROR) grampostag + gramnegtag <> gramtag (ERROR)"
	exit 1
else
	echo "grampostag + gramnegtag = gramtag (GOOD)"
fi



big=`wc -l $misctag | tr -s " " | cut -d" " -f2`
small1=`wc -l $misctagpos | tr -s " " | cut -d" " -f2`
small2=`wc -l $misctagneg | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small1+small2))  ]; then
	>&2 echo "(ERROR) misctagpos + misctagneg <> misctag (ERROR)"
	exit 1
else
	echo "misctagpos + miscnegtag = misctag (GOOD)"
fi
	
big=`wc -l $gramtag | tr -s " " | cut -d" " -f2`
small1=`wc -l $gramposanchor | tr -s " " | cut -d" " -f2`
small2=`wc -l $gramneganchor | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small1+small2))  ]; then
	>&2 echo "(ERROR) gramposanchor + gramneganchor <> gramtag (ERROR)"
	exit 1
else
	echo "gramposanchor + gramneganchor = gramtag (GOOD)"
fi

big=`wc -l $gramtag | tr -s " " | cut -d" " -f2`
small1=`wc -l $gramnegtagposanchor | tr -s " " | cut -d" " -f2`
small2=`wc -l $gramnegtagneganchor | tr -s " " | cut -d" " -f2`
small3=`wc -l $grampostagneganchor | tr -s " " | cut -d" " -f2`
small4=`wc -l $grampostagposanchor | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small1+small2+small3+small4))  ]; then
	>&2 echo "(ERROR) grampospos + gramposneg + gramnegpos + gramnegneg <> gramtag (ERROR)"
	exit 1
else
	echo "grampospos + gramposneg + gramnegpos + gramnegneg = gramtag (GOOD)"
fi

big=`wc -l $gramneganchor | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small2+small3))  ]; then
	>&2 echo "(ERROR) gramnegpos + gramnegneg <> gramtag_neganchor (ERROR)"
	exit 1
else
	echo "gramnegpos + gramnegneg = gramtag_neganchor (GOOD)"
fi

big=`wc -l $gramposanchor | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small4+small1))  ]; then
	>&2 echo "(ERROR) grampospos + gramposneg <> gramtag_posanchor (ERROR)"
	exit 1
else
	echo "grampospos + gramposneg = gramtag_posanchor (GOOD)"
fi

big=`wc -l $grampostag | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small3+small4))  ]; then
	>&2 echo "(ERROR) grampospos + gramnegpos <> gramtag_postag (ERROR)"
	exit 1
else
	echo "grampospos + gramnegpos = gramtag_postag (GOOD)"
fi

big=`wc -l $gramnegtag | tr -s " " | cut -d" " -f2`
if [ $((big)) -ne $((small2+small1))  ]; then
	>&2 echo "(ERROR) gramposneg + gramnegneg <> gramtag_negtag (ERROR)"
	exit 1
else
	echo "gramposneg + gramnegneg = gramtag_negtag (GOOD)"
fi



