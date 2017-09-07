# README #


Steps to recreate English TQ corpus annotations:

## Data preparation ##
1. **Download OpenSubtitles raw data:**
    * *raw* data for the language pair (separate files) [from Opus](http://opus.lingfil.uu.se/OpenSubtitles2016.php) - untokenised corpus files
    * the sentence alignment file for the language pair, named *alignments.src-trg.xml.gz* (to be placed alongside the 'raw' directory)
    
    >      OpenSubtitles2016/
    >       |
    >       +---- raw/
    >       |      |
    >       |      +---- en-fr/
    >       |      |
    >       |      +---- ...
    >       |
    >       +---- alignments.en-fr.xml.gz

2. **Install pre-processing tools**
    * MElt tokeniser/tagger [(Link)](https://gforge.inria.fr/frs/download.php/file/36209/melt-2.0b12.tar.gz)
    * mosesdecoder (for truecasing) [(Link)](https://github.com/moses-smt/mosesdecoder)

3. **Change the paths in datasets/generic-makefile to correspond to your own paths**
    * OSDIR=/path/to/OpenSubtitles2016/raw
    * TRUECASINGDIR=/path/to/mosesdecoder/scripts/recaser
    * MAINDIR=path/to/tag-questions-opensubs

4. **Prepare true-casing data**
    * concatenate Europarl and Ted-talks data (full monolingual datasets) where available for the language
    * replace &#160; by space
    * tokenise with MElt: `MElt -l {en, fr, de, cs} -t -x -no_s -M -K`
    * change the path in the language-specific Makefile to the pre-processed data used for truecasing

4. **Extract parallel corpus**
    * ```cd datasets/langpair``` (e.g. de-en, fr-en, cs-en)    
    * `make extract`

5. **Pre-process data**
    * ```cd datasets/langpair``` (e.g. de-en, fr-en, cs-en)
    * change the path in the language-specific Makefile. Truecasing data must be a single file for each language, tokenised (with MElt) and cleaned using the clean_subs.py script)
    * Preprocessing (cleaning, blank line removal, tokenisation, truecasing and division into sets): ```make preprocess```



## Annotate tag questions ##
1. `cd subcorpora/langpair`
2. `make annotate` (to get line number of each type of tag question)
3. `make getsentences` (to extract the sentences corresponding to the line numbers)

## Translate senten
1. Store translations in ```translations/langpair```
