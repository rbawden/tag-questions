#!/usr/bin/python3
# coding: utf-8
import gzip, re
import os
import argparse


# retokenise badly tokenised contractions
def retokenise(line):
    line = re.sub("("+"|".join(get_en_aux())+")n 't", r"\1 n't", line)
    # print(line)
    return line

def get_en_tags():
    return re.compile("(^|.*, )(("+"|".join(get_en_aux())+") (?:n.t )?"+"("+"|".join(get_en_pros())+")(?: not)?[ \?\!\.\"\'\-\:\;]*?) *$", re.I)

# must match this
def get_en_neg_tags():
    # case sensitive
    # cannot_precede = "(?:.(?!\\b"+"\\b|\\b".join(["or", "what", "where", "why", "when", "how", "that", "this", "it", "and", "but", "just", "definitely"])+"\\b))*"
    contr_spec = "("+"|".join(get_en_aux())+") n.t ("+"|".join(get_en_pros())+") \? *$"
    noncontr_spec = "("+"|".join(get_en_aux())+") ("+"|".join(get_en_pros())+") not \? *$"
    contr = ", ("+"|".join(get_en_aux())+") n.t ("+"|".join(get_en_pros())+")[ \?\!\.\"\'\-\:\;]+$"
    noncontr = ", ("+"|".join(get_en_aux())+") ("+"|".join(get_en_pros())+") not[ \?\!\.\"\'\-\:\;]+? *$"
    return re.compile("^(.*? )("+contr+"|"+noncontr+"|"+contr_spec+"|"+noncontr_spec+")", re.I)

# mustn't match this
def inv_en_neg_tags():
    preceding = "(\\b"+"\\b|\\b".join(["or", "what", "where", "why", "when", "how", "that", "this", "it", "and", "but", "just", "definitely"])+"\\b)"
    contr = "("+"|".join(get_en_aux())+")[\,\.\-\"\'\`\:\; ]* n.t ("+"|".join(get_en_pros())+")[ \?\!\.\"\'\-\:\;]+? *$"
    noncontr = "("+"|".join(get_en_aux())+")[\,\.\-\"\'\`\:\; ]*("+"|".join(get_en_pros())+") not[ \?\!\.\"\'\-\:\;]+? *$"
    return re.compile("^.*?"+preceding+" ("+contr+"|"+noncontr+")$", re.I)
    

def get_en_pros():
    return ["I", "you", "[h\']e", "thee", "ye", "yer", "she+", "we", "one", "they", "it", "i\'", "there", "someone", "anyone"]

def get_en_aux():
    return ["have", "had", "has", "might", "may", "will", "would", "could",
              "can", "must", "should", "shall", "ought", "do", "does", "did",
              "am", "are", "is", "was", "were", "had", "ai", "dare", "need"]

def get_fr_tag_phrases():
    fr_tag_phrases = ["n\' est \-ce pas", "non", "hein", "pas vrai", "d\' accord",
                      "ou quoi", "tu ne crois pas", "tu ne trouves? pas", "c\' est ça",
                      "dis", "dites", "ok", "okay", "voulez \-vous", "veux \-tu", "si",
                      "oui", "alors", "tu vois", "tu ne vois pas", "vois \-tu",
                      "tu crois", "crois \-tu", "souviens \-toi", "souvenez \-vous"]
    return fr_tag_phrases

def get_en_not_permitted():
    en_not_permitted = ["^.*?(is you|do it|have one|are he|are she|is not you|have it|is not you|not you) *[\.\!\? \'\"\;\:\-]*$", "^.*?\.( ?\.)+[ \?\.\"\']*$"]
    return en_not_permitted

def get_regex_en_special_tags():
    # return re.compile(".+ (inni.|\, right \?|eh \?|\, see \?|\, remember \?|\, you know \?|\, or what \?)[ \"\'\?\.]*$", re.I)
    return re.compile("^(.+) ((?:inn+i.|\, ri+ght \?|e+h+ \?|\, see+ \?|\, remember \?|\, you know \?|\, or what \?|\, ye+a+h+ \?|\, aye|\, you see|\, like|\, ok(ay)? \?|do n't y..? think \?|\, correct \?|\, all right|\, alright)[ \"\'\?\!\.\-\;\:]*)$", re.I)

def get_en_neg_words():
    return ["n[\'o]t", "never", "no longer", "nobody", "nowhere", "nothin[^ ]?", "no[- ]?one",
            "none", "[h\']ardly", "rarely", "scarcely", "seldom", "barely", "neither",
            "nor", "ne\'er", "[^ ]*nae", "nuffin[^ ]?", "can ?nae", "nowt", " no ", "absolutely no"] # removed 'no' - treat separately

# special case of are giving is (for collectives such as 'the team is happy, aren't they?')
# 'I'm here, aren't I', so are -> 'm
def get_aux_verb_regex(aux_verb):
    contractions = {"am": "([\'a]m|ai)",
                    "is": "([\'i]s|ai)",
                    "ai": "(ai|is|am|are|\'re)", # ain't you/it/I/we etc.
                    "are": "([a\']re|ai|re|[a\']m|theyre|your\'?e)",
                    "has": "([h\']as|\'?s|ai)",
                    "have": "('ve|have|ai|has)", # for collectives, e.g. the team has done blah blah, haven't they?
                    "would": "(wou[lI]d|\'d|is|will)",
                    "should": "shou[lI]d",
                    "will": "(will|\'ll|gonna|going to)",
                    "were": "(were|\'re|are|was)",
                    "was": "(was|were)",
                    "did": "do",
                    "do": "(do|does|have|got)", # change of interlocutor (he doesn't, do you?)
            }
    if aux_verb.lower() in contractions:
        return contractions[aux_verb.lower()]
    else: return aux_verb.lower()

def get_neg_raising_preds(): # and others -> need to refine
    return ["believe(s?|ing|d)", "suppos(es?|ing)", "think(s|ing)?", "likely", "seem(s|ed)?", "ought", "gonna", "going to",
            "it (w?.s|were) like", "guess(es|ed|ing)?", "thought", "happen to", "imagin(es?|ed|ing)"]

def get_neg_neg_raising_preds(): # and others
    return ["it 's not like", "it is n't like"]


def tagpro2auxpro_regex(pro):
    pros = {"I": "[\bIi\b]",
            "we": "(?!(s?he|they|there))[^ ]+",
            "you": "(you|we|she|it|he|I|they)", # can have change of interlocutor, 3rd -> 2nd person
            "there": "there",
            "it": "([il]t|this|that|[^ ]+)",
            "they":"(they|[^ ]+|people)",
            "he": "[^ ]+",
            "she": "[^ ]+"} 

    if pro in pros: return pros[pro]
    else: return "("+pro+"|[^ ]+|)"
    

def is_viable_anchor(anchor, tag):
    nonviable = re.compile("[\'\"\.\,\:\;\` \/\\\(\)]*((yeah|ok(ay)?|er*|[oôau0ûq]+h+|well|of course|yes|no|hey|[uh]m+|so|sorry|o[iy]|hell|but|why|no|please|and|aye|oh) )+[\'\"\.\,\:\;\` \/\\\(\)]*$", re.I)
    empty = re.compile("([\'\"\.\,\:\;\`\?\!\- ]|[^a-z0-9])*$", re.I)
    
    if re.match(nonviable, anchor): return False
    if re.match(empty, anchor): return False
    return True


    

#=================== General functions ===================
def print_my_line(i, is_en_type, is_fr_type, search_en, search_fr, strict):
        # Both en and fr question
        if search_en and search_fr and is_en_type and is_fr_type:
            os.sys.stdout.write(str(i+1)+"\n")
            
        # Either en question or fr question but not both
        elif strict and search_en and not search_fr and \
          is_en_type and not is_fr_type:
          os.sys.stdout.write(str(i+1)+"\n")
          
        elif strict and search_fr and not search_en and \
          is_fr_type and not is_en_type:
          os.sys.stdout.write(str(i+1)+"\n")
          
        # Either en question or fr question   
        elif not strict and search_en and not search_fr and is_en_type:
            os.sys.stdout.write(str(i+1)+"\n")
            
        elif not strict and search_fr and not search_en and is_fr_type:
            os.sys.stdout.write(str(i+1)+"\n")

#=================== Tag question functions ===================

en_tags = get_en_tags() #re.compile("(^|.*\, )("+"|".join(get_en_aux())+") (n.t )?"+"("+"|".join(get_en_pros())+")( not)?[ \?\.\"\']*$", re.I)
en_neg_tags = get_en_neg_tags()
en_neg_tags_inv = inv_en_neg_tags()
en_special_tags = get_regex_en_special_tags()
en_non_tag = re.compile("("+"|".join(get_en_not_permitted())+")", re.I)
fr_tags = re.compile("(.*?)\, ("+"|".join(get_fr_tag_phrases())+") \?", re.I)

# is a tag question or not (grammatical or miscellaneous)
def is_en_tag(line):
    if is_en_gram_tag(line):
        return True
    if is_en_gram_tag_negtag(line):
        return True
    if is_en_misc_tag(line):
        return True
    return False 


# is a tag question (grammatical)
def is_en_gram_tag(line):
    # must not match this
    if re.match(en_non_tag, line):
        return False
    if re.match(en_neg_tags_inv, line):
        return False
    
    # can match this
    # if is_en_gram_tag_negtag(line) or is_en_gram_tag_postag(line):
    if re.match(en_neg_tags, line) or re.match(en_tags, line):

        # check anchors
        anchor, tag = get_anchor_and_tag(line)
        if not anchor: return False
        # does the anchor contain something that confirms that it is a tag question?
        if not is_viable_anchor(anchor, tag): return False
        
        return True
    return False # default


def is_en_gram_tag_negtag(line):
    
    # must not match this
    if re.match(en_non_tag, line):
        return False
    if re.match(en_neg_tags_inv, line):
        return False
    
    # must match this
    if is_en_gram_tag(line) and re.match(en_neg_tags, line):

         # check anchors
        anchor, tag = get_anchor_and_tag(line)
        if not anchor: return False
        # does the anchor contain something that confirms that it is a tag question?
        if not is_viable_anchor(anchor, tag): return False

        return True
    return False # default

    
def is_en_gram_tag_postag(line):
    yes = (is_en_gram_tag(line) and not is_en_gram_tag_negtag(line))

    # if "n't ?" in line and not yes:
      # print(line)
    
    return yes
    
    
# is a tag question (miscellaneous)
def is_en_misc_tag(line):
    # must not match this
    if re.match(en_non_tag, line):
        return False
    # can match this
    if re.match(en_special_tags, line):

        anchor, tag = get_anchor_and_tag(line)
        if not anchor: return False
        # does the anchor contain something that confirms that it is a tag question?
        if is_viable_anchor(anchor, tag):
            return True
    return False # default

# is a French tag question
def is_fr_tag(line):
    if re.match(fr_tags, line):
        
        
        return True
    return False


def get_anchor_and_tag(line):
    anchor_tag_match = re.match(get_en_tags(), line)
    anchor_neg_tag_match = re.match(en_neg_tags, line)
    anchor_special_tag_match = re.match(en_special_tags, line)
    
    if anchor_tag_match:
        anchor = anchor_tag_match.group(1)
        tag = anchor_tag_match.group(2)
    elif anchor_special_tag_match:
        anchor = anchor_special_tag_match.group(1)
        tag = anchor_special_tag_match.group(2)
    elif anchor_neg_tag_match:
        anchor = anchor_neg_tag_match.group(1)
        tag = anchor_neg_tag_match.group(2)
    else:
        anchor, tag = None, None
        # os.sys.stderr.write(line)
    # print(tag)
    # input()
        
    if anchor: return anchor.strip(), tag.strip()
    else: return anchor, tag
        
def get_auxverb_tagpro(line):
    anchor_tag_match = re.match(en_tags, line)
    anchor_neg_tag_match = re.match(en_neg_tags, line)
    anchor_special_tag_match = re.match(en_special_tags, line)
        
    if anchor_tag_match:
        tagpro = anchor_tag_match.group(4)
        auxverb = anchor_tag_match.group(3)
    elif anchor_special_tag_match:
        tagpro = None
        auxverb = None
    elif anchor_neg_tag_match:
        auxverb = anchor_neg_tag_match.group(4)
        tagpro = anchor_neg_tag_match.group(3)
    else:
        auxverb, tagpro = None, None
        os.sys.stderr.write(line)

    # os.sys.stderr.write(auxverb+" "+tagpro+"\n")
    if auxverb: return auxverb.strip(), tagpro.strip()  
    else: return auxverb, tagpro

# all tag questions
def tag_questions(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_tag(en): found_en = True
            
        # French
        found_fr = False
        # if search_fr and is_fr_tag(fr): found_fr = True

        # check anchors
        # if search_en: anchor, tag = get_anchor_and_tag(en)
        # if not anchor: continue 

        # does the anchor contain something that confirms that it is a tag question?
        # if search_en and not is_viable_anchor(anchor, tag):
            # continue
          
        # Send to print function
        if found_en or found_fr:
            print_my_line(i, found_en, found_fr, search_en, search_fr, strict)

# grammatical tag questions
def gramtag_questions(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)

        # English
        found_en = False
        if search_en and is_en_gram_tag(en): found_en = True
            
        # French
        found_fr = False
        if search_fr and is_fr_tag(fr): found_fr = True

        # check anchors
        if search_en: anchor, tag = get_anchor_and_tag(en)
        if not anchor: continue 

        # does the anchor contain something that confirms that it is a tag question?
        if search_en and not is_viable_anchor(anchor, tag):
            continue
          
        # Send to print function
        if found_en or found_fr:
            print_my_line(i, found_en, found_fr, search_en, search_fr, strict)

# miscellaneous tag questions
def misctag_questions(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_misc_tag(en): found_en = True
            
        # French
        found_fr = False
        if search_fr and is_fr_tag(fr): found_fr = True

        # check anchors
        if search_en: anchor, tag = get_anchor_and_tag(en)
        if not anchor: continue 

        # does the anchor contain something that confirms that it is a tag question?
        if search_en and not is_viable_anchor(anchor, tag):
            continue
          
        # Send to print function
        if found_en or found_fr:
            print_my_line(i, found_en, found_fr, search_en, search_fr, strict) 


a_no_negwords = re.compile("^.*?("+"|".join(get_en_neg_words())+") ?", re.I)

adverbs = ["really", "certainly", "definitely", "surely", "often", "mostly", "possibly", "potentially", "maybe", "even"]
adv_re = "( ("+"|".join(adverbs)+") )"
                
def is_negative_anchor(anchor, aux_verb, tag_pro):
    return is_positive_anchor(anchor, aux_verb, tag_pro, True)

def is_positive_anchor(anchor, aux_verb, tag_pro, neg=False):
    # doesn't contain any negative words
    # os.sys.stderr.write(anchor+"\n")
    if not re.match(a_no_negwords, anchor):
        # print(anchor)
        # print(aux_verb)
        # os.sys.stderr.write("no neg words whatsoever\n")
        if not neg: return True
        else: return False

    # contains a negative word
    else:
        if not tag_pro: tag_pro=""
        if not aux_verb: aux_verb=""

        # print(anchor)

        # input()
        # if "you 've never been" in anchor:
            # print("|"+anchor+"|")
            # print("|"+aux_verb+"|")
            # print("|"+tag_pro+"|")
            # print("^(.*? )?("+"|".join(get_en_pros())+") (("+"|".join(get_en_aux())+") ?)?("+"|".join(get_en_neg_words())+") ?([^\.\, ])? ("+"|".join(get_neg_raising_preds())+")( [^ ]+)")
            # print(re.match("^(.*? )?("+"|".join(get_en_pros())+") (("+"|".join(get_en_aux())+") )?("+"|".join(get_en_neg_words())+") ?([^\.\, ])? ("+"|".join(get_neg_raising_preds())+")( [^ ]+)", anchor, re.I))

            # input()
        # print(re.match("^(|.*? )?"+tag_pro+" (([^ ]+ )("+"|".join(get_en_neg_words())+"| no"+tag_pro+")( [^ ]+)* *)", anchor, re.I))
        # print(^(.*? )?(?!(who|if|when|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+" ?("+"|".join(get_en_neg_words())+") "+get_aux_verb_regex(aux_verb)+" ?(?!"+get_aux_verb_regex(aux_verb)+")")
        # print(re.match("^(.*? )?(?!(who|if|when|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+" ?("+"|".join(get_en_neg_words())+") "+get_aux_verb_regex(aux_verb)+" ?(?!"+get_aux_verb_regex(aux_verb)+")", anchor))
        # print(re.match("^(.*? )?(?!(who|if|when|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+" ?"+get_aux_verb_regex(aux_verb)+" ?("+"|".join(get_en_neg_words())+") ?(?!.*? "+get_aux_verb_regex(aux_verb)+"( |$))", anchor, re.I))
        #-------------------------> almost definitely negative


        # you don't think / you think, do (n't) you?
        if re.match("you do n't"+adv_re+"? ?(think|suppose|imagine|believe|know)", anchor) and tag_pro=="you" and aux_verb=="do":
            if neg: return True
        elif re.match("you (do )?"+adv_re+"?(think|suppose|imagine|believe|know)", anchor) and tag_pro=="you" and aux_verb=="do":
            if not neg: return True


        # you know..., don't you?
        elif re.match("(^|.*?[ \,]*|.*? and )(you|s?he|we) (do )?knows? .*?", anchor, re.I) and aux_verb in ["do", "does", "did", None]:

            # print("you know")
            if not neg: return True

        elif re.match("(^|.*?[ \,]*|.*? and )(you|s?he|we)"+get_aux_verb_regex(aux_verb)+adv_re+"? knows? .*?", anchor, re.I) and aux_verb in ["do", "does", "did", None]: 
            if not neg: return True
        

        # only one auxiliary in the sentence and is negated
        elif re.match("(.*? )("+ "|".join(get_en_aux())+") ("+"|".join(get_en_neg_words())+")(?!.*? ("+"|".join(get_en_aux())+")( |$))", anchor, re.I):
            if neg: return True
                
        # print("here")
        # print(tag_pro)
        # print(aux_verb)
        # print("^(.*? )?(?!(who|if|when|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+" ?"+get_aux_verb_regex(aux_verb)+" ?"+adv_re+"?("+"|".join(get_en_neg_words())+"| no) ?(?!.*? "+tagpro2auxpro_regex(tag_pro)+" "+get_aux_verb_regex(aux_verb)+"( |$))")#, anchor, re.I))
        
        # negated auxiliary in the anchor (of equivalent form to the auxiliary in the tag question). if several, take last one
        elif re.match("^(.*? )?(?!(who|if|when|why|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+" ?"+get_aux_verb_regex(aux_verb)+" ?"+adv_re+"?("+"|".join(get_en_neg_words())+"| no) ?(?!.*? "+tagpro2auxpro_regex(tag_pro)+" "+get_aux_verb_regex(aux_verb)+"( |$))", anchor, re.I) or \
            re.match("^(.*? )?(?!(who|if|when|why|\") ?([^ ]+ )?)"+tagpro2auxpro_regex(tag_pro)+adv_re+"? ?("+"|".join(get_en_neg_words())+"| no) "+adv_re+"?"+get_aux_verb_regex(aux_verb)+" ?(?!.*? "+tagpro2auxpro_regex(tag_pro)+" "+get_aux_verb_regex(aux_verb)+"( |$))", anchor, re.I) or \
            ("cannot" in anchor and "can" in aux_verb) or ("dont" in anchor and "do" in aux_verb):
            # print("neg repeated aux")
            
            
            if neg: return True
            else: return False
            

        # negated auxiliary in the anchor (of equivalent form to the auxiliary in the tag question). if several, take last one
        elif re.match("^(.*? )?"+get_aux_verb_regex(aux_verb)+" ?("+"|".join(get_en_neg_words())+"| no) ?(?!.*? "+get_aux_verb_regex(aux_verb)+"( |$))", anchor, re.I) or \
            re.match("^(.*? )?("+"|".join(get_en_neg_words())+"| no) "+get_aux_verb_regex(aux_verb)+" ?(?!.*? "+get_aux_verb_regex(aux_verb)+"( |$))", anchor, re.I) or \
            ("cannot" in anchor and "can" in aux_verb) or ("dont" in anchor and "do" in aux_verb):
            # print("neg repeated aux")
            
            if neg: return True
            else: return False          
                
        # search for last pronoun (when verb is do) TODO
        elif aux_verb in ["do", "does", "did", ""] and aux_verb not in anchor and \
           (re.match("^(|.*? )?"+tag_pro+" ([^ ]+ )?("+"|".join(get_en_neg_words())+"| no"+tag_pro+")( [^ ]+)* *", anchor, re.I) or \
           re.match("^(|.*? )?"+tag_pro+" ("+"|".join(get_en_neg_words())+"| no"+tag_pro+") ", anchor, re.I)):
            # print("last pron")
            if neg: return True
        
                
        # certain pronouns must be repeated I -> I, and some cannot have certain pronouns corresponding, we =/= s/he/they

        
        

        # negative subject w/ they/it/there            
        # neg polarity item as subject of auxiliary
        elif re.match("(^|.*? )(no.?one|nobody|nothin.?|nuffin.?|nought|not everyone|not all|neither|no|not one|none of th..|none of it) "+get_aux_verb_regex(aux_verb)+" .*?", anchor, re.I):
            if neg: return True

        elif re.match("(^|.*? )(no.?one|nobody|nothin.?|nuffin.?|nought|not everyone|not all|neither|no|not one|none of th..|none of it) ", anchor, re.I) and \
          tag_pro in ["they", "it", "there"] and aux_verb in ["does", "did", "do"]:
          if neg: return True 

        # future tense and neg -> negative
        elif (re.match(".*?(may|will|going to) ("+"|".join(get_en_neg_words())+").*?\,? *$", anchor, re.I) or \
            re.match(".*?("+"|".join(get_en_neg_words())+") (may|will|going to).*?\,? *$", anchor, re.I)) and \
            aux_verb in ["shall", "will", "may", "might", ""]:
            if neg: return True

        # neg raising
        elif re.match("^(.*? )?("+"|".join(get_en_pros())+") (("+"|".join(get_en_aux())+") ?)?("+"|".join(get_en_neg_words())+") ?([^\.\, ])? ("+"|".join(get_neg_raising_preds())+")( [^ ]+)", anchor, re.I):# or \
            # re.match("^(.*? )?("+"|".join(get_neg_neg_raising_preds())+") ?(?!"+get_aux_verb_regex(aux_verb)+")*?"+get_aux_verb_regex(aux_verb)+"(?!"+get_aux_verb_regex(aux_verb)+")*?$", anchor, re.I) or \
            # re.match("^(.*? )?("+"|".join(get_neg_raising_preds())+")(?!"+get_aux_verb_regex(aux_verb)+")[^ ]?"+get_aux_verb_regex(aux_verb)+"(?!"+get_aux_verb_regex(aux_verb)+")*?$", anchor, re.I):
            if neg: return True

        #-------------------------> almost definitely positive
        # there is an identical auxiliary in the anchor and no negation has been detected up until now
        elif re.match("(^|.*? )"+get_aux_verb_regex(aux_verb)+" ", anchor, re.I):
            if not neg: return True

        #-----------------------------------------------------------------------
        # LESS SURE - cases where the auxiliary verb in the anchor is easy to detect                          
        # no auxiliary can be found
    
        # 'not' at the beginning of the anchor (with potentially one (changed) word before) and aux is a 'to be' form (probable ellipsis of verb) -> negative
        elif (re.match("([^ ]+ )*([\.\,])* (not|never) .*?", anchor, re.I) or \
              re.match("^(not|never) ", anchor, re.I)):# and aux_verb in ["is", "are", "am", "were", "was", "", "do", "does"]:
            if neg: return True

        # no at the beginning of the sentence and no commas or full stops after (apart from a final one)        
        elif (re.match("^no [^\,\.]+?( \,)? *$", anchor, re.I) or \
              re.match("^(nothing like|none of) .*?", anchor, re.I)) and \
            aux_verb in ["is", "will", "was"] and tag_pro in ["there", "it", ""]:
            # print("hi")
            if neg: return True

        # imperatives, "just do that...", "never just do that..." etc.
        elif (re.match("(^|.*? )just [^ \.\,]+? ("+"|".join(get_en_neg_words())+") [^\.\,]+\,?", anchor, re.I) or \
            re.match("(^|.*? )("+"|".join(get_en_neg_words())+") just [^ \.\,]+? [^\.\,]+\,?", anchor, re.I)) and \
            aux_verb in ["will", "would", "can", "could", ""] and tag_pro in ["you", ""]:
            if neg: return True

        elif re.match("(^|.*? )just [^\.\,]+\,?", anchor, re.I) and aux_verb in ["will", "would", "can", "could", ""] and tag_pro in ["you", ""]:
            if not neg: return True # pos

        # imperatives with will, would, shall
        elif re.match("^do n't", anchor) and tag_pro=="you" and aux_verb in ["shall", "will", "would"]:
            if neg: return True
            else: return False

        # imperatives, "let us do that...", "let us never do"...        
        elif re.match("(^|.*? )let .s ("+"|".join(get_en_neg_words())+") ?[^\.\,]+\,?", anchor, re.I) and aux_verb in ["will", "shall", ""] and tag_pro in ["we", ""]:
            if neg: return True
                        
        elif re.match("(^|.*? )let .s [^\.\,]+\,?", anchor, re.I) and aux_verb in ["will", "shall", ""] and tag_pro in ["we", ""]:
            if not neg: return True

        # otherwise positive
        elif not neg: return True # check!!! TODO

        # print("end")
        return False


def gramtag_posanchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)

            # os.sys.stderr.write(tag+"|"+anchor+"|"+auxverb+"|"+tagpro+"\n")
            # input()
            
            if is_positive_anchor(anchor, auxverb, tagpro):
                found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict)
                    
def gramtag_neganchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            # os.sys.stderr.write(tag+"|"+anchor+"|"+auxverb+"|"+tagpro+"\n")
            # input()

            if is_negative_anchor(anchor, auxverb, tagpro):
                # os.sys.stderr.write("negative anchor\n")
                found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict)

            
def gramtag_postag(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag_postag(en):
            found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 
            

def gramtag_negtag(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)

        # English
        found_en = False
        if search_en and is_en_gram_tag_negtag(en):
            found_en = True                       

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 

def gramtag_postagposanchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag_postag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_positive_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 
    
def gramtag_postagneganchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag_postag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_negative_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict)                         

def gramtag_negtagneganchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag_negtag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_negative_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 

def gramtag_negtagposanchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_gram_tag_negtag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_positive_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 

def misctag_posanchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_misc_tag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_positive_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict) 


def misctag_neganchor(en_file, fr_file, search_en, search_fr, strict):
    # Go through and match sentences
    for i, (en, fr) in enumerate(zip(en_file, fr_file)):
        if en.strip()=="": continue
        en = retokenise(en)
                
        # English
        found_en = False
        if search_en and is_en_misc_tag(en):
            anchor, tag = get_anchor_and_tag(en)
            auxverb, tagpro = get_auxverb_tagpro(en)
            if is_negative_anchor(anchor, auxverb, tagpro): found_en = True

        # Send to print function
        if found_en:
            print_my_line(i, found_en, False, search_en, search_fr, strict)
                                      
if __name__ =="__main__":
                   
    parser = argparse.ArgumentParser()
    parser.add_argument("english_file")
    parser.add_argument("french_file")
    parser.add_argument("fr_en_or_both", choices=["en", "fr", "both"])
    parser.add_argument("-strict", action='store_true')
    parser.add_argument("tagtype", choices = ["all", "gram", "misc", "grampostag", "gramnegtag",
                                                "grampostag-posanchor", "grampostag-neganchor",
                                                "gramnegtag-posanchor", "gramnegtag-neganchor",
                                                "gramposanchor", "gramneganchor", "miscposanchor",
                                                "miscneganchor"])
    args = parser.parse_args()

    search_en, search_fr = False, False
    if args.fr_en_or_both in ["both", "en"]: search_en = True
    if args.fr_en_or_both in ["both", "fr"]: search_fr = True

    tt = args.tagtype

    if ".gz" in args.english_file: en_file = gzip.open(args.english_file, "rt", encoding="utf-8")
    else: en_file = open(args.english_file, "rt", encoding="utf-8")

    if ".gz" in args.french_file: fr_file = gzip.open(args.french_file, "rt", encoding="utf-8")
    else: fr_file = open(args.french_file, "rt", encoding="utf-8")
        
    if tt=="all":
        tag_questions(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="gram":
        gramtag_questions(en_file, fr_file, search_en, search_fr, args.strict)  
    elif tt=="misc":
        misctag_questions(en_file, fr_file, search_en, search_fr, args.strict)
    
    elif tt=="grampostag":
        gramtag_postag(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="gramnegtag":
        gramtag_negtag(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="gramposanchor":
        gramtag_posanchor(en_file, fr_file, search_en, search_fr, args.strict) 
    elif tt=="gramneganchor":
        gramtag_neganchor(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="grampostag-posanchor":
        gramtag_postagposanchor(en_file, fr_file, search_en, search_fr, args.strict) 
    elif tt=="grampostag-neganchor":
        gramtag_postagneganchor(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="gramnegtag-neganchor":
        gramtag_negtagneganchor(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="gramnegtag-posanchor":
        gramtag_negtagposanchor(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="miscposanchor":
        misctag_posanchor(en_file, fr_file, search_en, search_fr, args.strict)
    elif tt=="miscneganchor":
        misctag_neganchor(en_file, fr_file, search_en, search_fr, args.strict)

    en_file.close()
    fr_file.close()

        
