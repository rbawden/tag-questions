from classify_tag_questions2 import *
from readfile import *
import argparse, re
import spacy
import nltk

# could be different from the one that works for reference tags
# (translation produces slightly different results)
def get_anchor_tag(sentence):
    sentence = sentence.strip()
    gram_reg_anch_tag = re.compile("(.+?)(?: ,)? (("+"|".join(get_en_aux())+") (n.t )?("+"|".join(get_en_pros())+")( n.t)?[ \?\!\.\:\;\-\"\']*)$", re.I)
    anch_tag = re.match(gram_reg_anch_tag, sentence.lower())
    # lex_anch_tag = re.match(get_regex_en_special_tags())

    anchor, tag = None, None
    if anch_tag:
        anchor = anch_tag.group(1)
        tag = anch_tag.group(2)
    else:
        anchor = sentence
        tag = "none"
    return anchor, tag

contractions = ["'?m", "'s", "'re", "'as", "'?d", "'ve", "'ll", "gonna", "going to"]

def has_preceding(toks, tagged, idx, what, can_precede):
    for t in range(idx-1, -1, -1):
        tag, tok = tagged[t], toks[t]
        if re.match("^"+what+"$", tag):
            return t
        if len([c for c in can_precede if re.match("^"+c+"$", tag)])==0: return -1
    return -1

def has_following(toks, tagged, idx, what, can_follow=None):
    for t in range(idx+1, len(toks)):
        tag, tok = tagged[t], toks[t]
        if re.match("^"+what+"$", tag): return t
        if len([c for c in can_follow if re.match("^"+c+"$", tag)])==0: return -1
    return -1     
            
def has_subj(toks, tagged, idx_verb):

    if toks[idx_verb].lower() in ["is", "has", "does", "can"]: return True
    if idx_verb>0 and "PRP" == tagged[idx_verb-1]: return True
    if idx_verb>0 and tagged[idx_verb-1] == "NNP": return True
    if has_preceding(toks, tagged, idx_verb, "EX", ["MD", "LS", "``", "RB"])!=-1: return True
    if has_preceding(toks, tagged, idx_verb, "PRP", ["MD", "LS", "``", "RB", "CD", "NNS"])!=-1: return True
    if has_preceding(toks, tagged, idx_verb, "DT", ["MD", "LS", "``", "RB"])!=-1: return True
    if has_preceding(toks, tagged, idx_verb, "NNS?", ["MD", "LS", "``", "RB"])!=-1: return True

    if idx_verb+1 < len(toks) and \
      toks[idx_verb+1].lower() in ["he", "she", "it", "they", "I", "i", "we", "you"]: return True
        
    return False


def get_subj(toks, tagged, idx_verb):
    if idx_verb>0 and "PRP" == tagged[idx_verb-1]: return idx_verb-1, toks[idx_verb-1]
    if idx_verb>0 and tagged[idx_verb-1] == "NNP": return idx_verb-1, toks[idx_verb-1]
    t = has_preceding(toks, tagged, idx_verb, "PRP", ["MD", "LS", "``", "''", "RB", "NNS", "CD"])
    if t!=-1: return t, toks[t]
    t = has_preceding(toks, tagged, idx_verb, "NNS?", ["MD", "LS", "``", "''", "RB"])
    if t!=-1: return t, toks[t]
    t = has_preceding(toks, tagged, idx_verb, "EX", ["MD", "LS", "``", "''", "RB"])
    if t!=-1: return t, toks[t]
    t = has_preceding(toks, tagged, idx_verb, "DT", ["MD", "LS", "``", "''", "RB"])
    if t!=-1: return t, toks[t]

    # following subj (interrogative)
    if idx_verb+1 < len(toks) and \
      toks[idx_verb+1].lower() in ["he", "she", "it", "they", "i", "we", "you", "that", "this", "these", "those", "there"]:
        return idx_verb+1, toks[idx_verb+1].lower()
    
    return -1, None # default = None

# a number of identifiable imperatives
def imperative(anchor, toks, tagged):

    idx_verb = None
    for t, tag in enumerate(tagged):
        if tag=="VB" and not (t==0 and toks[t] in ["see", "look"]):
            idx_verb=t
            break
    if idx_verb==None: return False
    
    if tagged[0] == "VB": return True
    if has_subj(toks, tagged, idx_verb)!=-1: return False
    return True
    
def get_all_aux(withDo = True):
    all_aux = get_en_aux()+contractions
    if withDo: return all_aux
    return [aux for aux in all_aux if aux not in ["do", "does"]]

def compare_tags(tagged, findtags):
    if len(tagged)<len(findtags): return False
    for i, tag in enumerate(findtags):
        if not re.match("^"+tag+"$", tagged[i]): return False
    return True
                        

def is_neg(toks, tagged, idx_verb, idx_pro):

    # interrogative, always pos
    if idx_pro > idx_verb: return True

    # begins with you
    # if toks[0]=='so': return True
    
    negs=["not", "n't", "'t", "neither", "no", "never", "anymore", "nae"]
    if idx_verb > 0 and toks[idx_verb-1] in negs:
        return True
    if idx_verb < len(tagged)-1 and toks[idx_verb+1] in negs: return True
        
    # print(idx_verb)
    # print("not neg")
    return False

def idx_aux(toks):
    # start from last comma (in anchor)
    if "," in toks: last_comma = [c for c, comma in enumerate(toks) if comma in [","]][-1]
    else: last_comma = 0

    for t, tok in enumerate(toks):
        if t < last_comma: continue
        if re.match("^("+"|".join(get_all_aux())+")$", tok.lower()):
            return t

    # don't look at commas if haven't found yet
    for t, tok in enumerate(toks):
        if re.match("^("+"|".join(get_all_aux())+")$", tok.lower()):
            return t
    return None


def raising(toks):
    # utterances started with X thinks that.. (neg raising preds)
    preds = ["think.+?", "suppos.+", "assum.+", "imagin.+", "believ.+", "seem.*", "guess.*"]
    # if has one of these preds and there is a following pronoun
    if re.match("^("+"|".join(preds)+")$", toks[first_verb].lower()) and len([t for t in pro if t > first_verb])>0:
        idx_pro = [t for t in pro if t > first_verb][0]
        idx_verb = has_following(toks, tagged, idx_pro, "(V.+|MD)", ["RB"])
        # print(toks[idx_verb])
        subj, verb = toks[idx_pro], toks[idx_verb]
        aux = "do" # approximation
    return subj, idx_verb, verb, aux, idx_pro

    
def predictTag(anchor, toks, tagged, lemmas, guys, gals):

    # let us / let 's (before detecting auxiliaries)
    if re.match("(^|.*? )let [\'u]s ", anchor.lower()):
        return "shall_we"

    # you know / you think
    if "you know" in anchor.lower(): return "do_n't_you"
    elif "you think" in anchor.lower(): return "do_n't_you"
    elif "you do n't think" in anchor.lower(): return "do_you"
    # you do, do you? etc..
    for pro in ["I", "you", "we", "he", "she", "it"]:
        if pro in ["anyone", "one", "there", "she", "it", "he"]: v = "does"
        else: v = "do"
        if re.match("([^ ] ){,3}"+pro+" "+v+" *$", anchor.lower()): return pro+"_"+v

    # imperatives and not an aux (other than do at beginning)
    # request = ["bring", "get", "fetch", "close", "open", "move", "pass"]
    # if imperative(anchor, toks, tagged) and re.match("^("+"|".join(request)+")$", toks[0]):
        # return "would_you"
    if imperative(anchor.lower(), toks, tagged) and \
       (toks[0] in ["do", "does"] or not re.match("^("+"|".join(get_all_aux())+")$", toks[0].lower())):
        return "will_you"
    
    idx_verb = idx_aux(toks)

    pro = [t for t, tok in enumerate(toks) if re.match("^("+"|".join(get_en_pros())+")$", tok.lower())]
    first_verb = has_following(toks, tagged, -1, "V.+", [".+"])


    # is it sth like 'I thnk
    # utterances started with X thinks that.. (neg raising preds)
    preds = ["think.+?", "suppos.+", "assum.+", "imagin.+", "believ.+", "seem.*", "guess.*"]
    # if has one of these preds and there is a following pronoun
    if re.match("^("+"|".join(preds)+")$", toks[first_verb].lower()) and len([t for t in pro if t > first_verb])>0:
        idx_pro = [t for t in pro if t > first_verb][0]
        idx_verb = has_following(toks, tagged, idx_pro, "(V.+|MD)", ["RB"])
        # print(toks[idx_verb])
        subj, verb = toks[idx_pro], toks[idx_verb]
        aux = "do" # approximation
    
    
    # if more than one auxiliary, take first
    elif idx_verb!=None:
        aux = toks[idx_verb]
        # print("getting subject")
        idx_pro, subj = get_subj(toks, tagged, idx_verb)
        # print(subj)
            
    # if a pronoun is present, take the first one
    elif len(pro)>0:
        idx_pro = pro[0]
        idx_verb = has_following(toks, tagged, idx_pro, "(V.+|MD)", ["RB"])
        subj, verb = toks[idx_pro], toks[idx_verb]
        aux = "do" # approximation

    # elif first_verb!=1:
    #     aux = toks[first_verb]
    #     subj = get_subj(toks, tagged, first_verb)
    #     if subj==-1: subj=None
    #     idx_verb = first_verb

    else:
        return "DUNNO"

    beginning = [] #["so"]
    if not is_neg(toks, tagged, idx_verb, idx_pro) and toks[0] not in beginning: neg="_n't"
    else: neg=""

    # print(subj, aux)
    # get modified pronoun, aux and neg
    subj = predict_prosubj(subj, aux, idx_verb, idx_pro, tagged, neg, guys, gals)

    if subj is None: subj=""
    subj, aux = get_aux(aux, subj, toks, tagged, idx_verb, neg)
    neg = get_neg(neg, aux, toks, tagged, subj)
    return aux+neg+"_"+subj       

    
    # numaux = len(re.findall("(^| )("+"|".join(get_all_aux())+")( |$)", anchor, re.I))
    # if numaux==1:
    #     subj_aux = re.match(".*?([^ ,\.]*?)(?: ("+"|".join(get_en_neg_words())+"))? ("+"|".join(get_all_aux())+")(?: ("+"|".join(get_en_neg_words())+"))?", anchor, re.I)
    #     if subj_aux:
    #         subj = subj_aux.group(1)
    #         aux = subj_aux.group(3)

    #         # detect negation in anchor clause
    #         if subj_aux.group(2) or subj_aux.group(4):neg=""
    #         else: neg="_n't"

    #         # get modified pronoun, aux and neg
    #         subj = predict_prosubj(subj, aux, neg)
    #         aux = get_aux(aux, neg)
    #         # neg = get_neg(neg, aux, subj)
    #         return aux+neg+"_"+subj
    # elif numaux>1:
    #     # take first
    #     subj_aux = re.findall(".*?([^ ,\.]*?)(?: ("+"|".join(get_en_neg_words())+"))? ("+"|".join(get_all_aux())+")(?: ("+"|".join(get_en_neg_words())+"))?", anchor, re.I)[0]
    #     if subj_aux:
    #         subj = subj_aux[0]
    #         aux = subj_aux[2]

    #         # detect negation in anchor clause
    #         if subj_aux[1] or subj_aux[3]:neg=""
    #         else: neg="_n't"

    #         # get modified pronoun, aux and neg
    #         subj = predict_prosubj(subj, aux, neg)
    #         aux = get_aux(aux, neg)
    #         # neg = get_neg(neg, aux, subj)

    #         return aux+neg+"_"+subj
    # else:
    #     numpro = len(re.findall("(^| )("+"|".join(get_en_pros())+") (?:("+"|".join(get_en_neg_words())+") )?([^ ]+?)(?: ("+"|".join(get_en_neg_words())+") )?( |$)", anchor, re.I))
    #     if numpro>0:
    #         subj_verb = re.match("(^|.+? )("+"|".join(get_en_pros())+") (?:("+"|".join(get_en_neg_words())+") )?([^ ]+?)(?: ("+"|".join(get_en_neg_words())+") )?( |$)", anchor, re.I)
    #         if subj_verb:
    #             subj = subj_verb.group(2)
    #             aux = subj_verb.group(4)
    #             if aux not in get_en_aux():
    #                 if subj in ["she", "he", "it", "there"]: aux = "does"
    #                 else: aux = "do"
    #             if subj_verb.group(3) or subj_verb.group(5): neg=""
    #             else: neg="_n't"

    #             # get modified pronoun, aux and neg
    #             subj = predict_prosubj(subj, aux, neg)
    #             aux = get_aux(aux, neg)
    #             return aux+neg+"_"+subj
    #     # else:
    #         # print(anchor)
    #         # input()
    #         # if re.match("(^| )("+"|".join(get_en_neg_words())+")( |$)", anchor): return "is_it"
    #         # else: return "is_n't_it"

            
    #     # look for pronouns
    #     # print(anchor)
    #     # input()
    #     # if len(anchor.split())>3: return "is_n't_it"

    # return "DUNNO"

def get_aux(aux, subj, toks, tagged, idx_verb, neg=False):
    aux = aux.lower()

    # stop=False
    # if subj=="it" and aux=="do":
    #    print(subj, aux)
    #    stop=True

    
    # correct grammatical errors...
    if subj.lower() in ["you", "they"]:
        if aux=="is": aux="are"
        elif aux=="was": aux="were"
        elif aux=="has": aux="have"
        elif aux=="does": aux="do"
    elif subj.lower() in ["i", "I"]:
        if aux in ["is", "are"]: aux="am"
        elif aux=="has": aux="have"
        elif aux=="does": aux="do"
    elif subj.lower() in ["we"]:
        if aux in ["is", "am"]: aux="are"
        elif aux =="does": aux="do"
        elif aux =="has": aux="have"
    elif subj.lower() in ["it", "he", "she", "there", "anyone", "one"]:
        if aux=="are": aux="is"
        elif aux=="were": aux="was"
        elif aux=="have": aux="has"
        elif aux=="do": aux="does"

    # if stop and aux=="do":
    #     print(subj, aux)
    #     input()
            
    # normal cases
    if aux in ["is", "'s", "s"]:
        if aux =="is": return subj, "is"
        elif has_following(toks, tagged, idx_verb, "VB[ND]", ["RB"])!=-1: return subj, "has"
        else: return subj, "is"
    elif aux =="ca": return subj, "can"
    elif aux in ["am", "'m", "m"] and neg: return "i", "are"
    elif aux in ["am", "'m", "m"]: return "i", "am"
    elif aux in ["are", "'re", "re"]: return subj, "are"
    elif aux in ["would", "'d", "d"]: return subj, "would" # could be had too
    elif aux in ["will", "'ll", "ll"]: return subj, "will"
    elif aux in ["ai"] and subj in ["I", "they", "we", "you"]: return subj, "are" # could be many other auxiliaries
    elif aux in ["ai"] and subj in ["he", "she", "it"]: return subj, "is"
    elif aux in ["do", "need"]: return subj, "do" # not often need in both anchor and aux
    else:

        # have -> do
        
        if aux in ["has", "have", "ve", "'ve", "'s", "s"] and \
           (has_following(toks, tagged, idx_verb, "VB[ND]", can_follow=["RB"])==-1):
            if subj.lower() in ["i", "you", "we", "they"]:
                return subj, "do"
            else: return subj, "does"
                
        elif aux in ["have", "'ve", "ve", "s", "'s"]:
            if subj.lower() in ["i", "you", "we", "they"]: return subj, "have"
            else: return subj, "has"
        
        for refaux in get_all_aux():
            if re.match("^"+refaux+"$", aux):                
                return subj, aux
        if subj.lower() in ["i", "you", "we", "they"]: return subj, "do"
        else: return subj, "does"


def get_neg(neg, aux, toks, tagged, subj):
    # if subj=="there" and aux=="are": return "_n't"
    if False: 1
    # if len(toks)>1 and toks[0]=="you" and re.match("^("+"|".join(get_all_aux())+")$", toks[1]): return ""
    else: return neg

def initial_verb(anchor, toks, tagged):
    1
        
def predict_prosubj(subj, aux, idx_verb, idx_subj, tagged, neg, guys, gals):
    # print(subj)
    # if subject is empty - beginning of sentence
    
    if not subj and idx_verb==0 and "V" in tagged[0] or "MD" in tagged[0]: return "you"
    elif not subj: return "it"

    # plural common nouns
    if tagged[idx_subj]=="NNS": return "they"
    
    # if subject already a pronoun, return this
    if subj not in ["one", "someone"]:
        if re.match("(^| )("+"|".join(get_en_pros())+")( |$)", subj, re.I): return subj

    # decide which form is better
    if aux.lower() in ["am"]: subj = "I"
    elif  subj.lower() in ["these", "them", "those"]: return "they"
    elif subj.lower() in ["this", "that", "it"]: return "it"
    elif subj.lower() in ["us"]: return "we"
    elif subj.lower() in ["one", "someone"]: return "it"
    elif subj.lower() in ["people", "guys", "ladies", "women", "men", "boys", "girls", "everyone", "everybody", "nobody"]: return "they"
    elif subj.lower() in ["girl", "woman", "lady", "mum", "mom", "mother",
                  "daughter", "sister", "aunt", "gran", "granny",
                  "grandmother", "grandmum"]:
        return "she"
    elif subj.lower() in ["boy", "man", "guy", "dad", "pa", "father" "dude", "son",
                  "brother", "uncle", "grandfather", "cousin", "friend"]:
        return "he"
    elif aux.lower() in ["are", "do", "have"]: return "you"
    else:
        if subj!="" and subj[0]==subj[0].upper():
            if subj.lower() in gals and subj.lower() not in guys: return "she" # or she
            elif subj.lower() in guys: return "he"
            elif re.match(".+?i[ea]$", subj.lower()): return "she"
            else: return "he"
        else:
            return "it"


        
if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("sentencefile")
    # argparser.add_argument("goldfile")
    argparser.add_argument("-c", "--classfile",  required=False, default=None) # result of first classifier

    args = argparser.parse_args()

    # nlp = spacy.load('en')

    guy_list = read_list("/Users/rbawden/Documents/work/tag-questions-opensubs/resources/guys.list")
    gal_list = read_list("/Users/rbawden/Documents/work/tag-questions-opensubs/resources/gals.list")
    # goldlabels = read_list(args.goldfile)

    correct, total = 0, 0
    sents = read_text_file(args.sentencefile)

    goldlabels = ["gram"]*len(sents)
    if args.classfile: classes = read_list(args.classfile)
    else: classes = ["gram"]*len(goldlabels)


    assert(len(sents)==len(goldlabels)==len(classes))
    
    for i, (sent, gold) in enumerate(zip(sents, goldlabels)):

        if classes[i] != "gram" or sent.strip()=="":
            print(classes[i])
            continue

        # otherwise it is a gram!
        sent = retokenise(sent)
        anchor, tag = get_anchor_tag(sent)
        tag = gold # compare to gold label

        # tag and tokenise
        # tag_lem = nlp(anchor)
        
        toks = nltk.word_tokenize(anchor)
        tagged = nltk.pos_tag(toks)
        tagged = [t[1] for t in tagged]
                
        # toks = [word.text for word in tag_lem]
        # tagged = [word.tag_ for word in tag_lem]
        # print(tagged)
        # lemmas = [word.lemma_ for word in tag_lem]

        
        taghat = predictTag(anchor, toks, tagged, [], guy_list, gal_list)

        # if classes[i]!="none":
        #     print(str(i+1)+" : "+sent)
        #     print(gold)
        #     os.sys.stderr.write(taghat+"\n")
        #     input()
        
        if taghat!="DUNNO":
            total+=1
            # if "will" in taghat:
            #     if taghat.lower()=="_".join(tag.strip().strip("?").lower().split()):
            #         print("\tP = "+taghat+" : "+tag)
            #     else:
            #         print("\tP = "+taghat+" : WRONG "+tag)
            # continue


            tag = "_".join(re.sub("(^[\"\'\.\!\? ]+|[\"\'\.\!\? ]+$)", "", tag.lower()).split())
            taghat = taghat.lower()
            taghat = taghat.replace("'", "-")
            
            if taghat==tag:
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif tag.replace("ai_n-t", "is_n-t")==taghat:
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif tag.replace("ai_n-t", "are_n't")==taghat:
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif tag.replace("ai_n-t", "has_n-t")==taghat:
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif tag.replace("ai_n-t", "have_n-t")==taghat:
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif tag.replace("okay", "ok")==taghat.replace("okay", "ok"):
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif taghat=="does_n-t_it" and tag=="do_n-t_it":
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            elif taghat+"_not" == tag.replace("_", "_n-t_").replace("_n-t_not", "_not"):
                # print("\tP = "+taghat+" : "+tag)
                correct+=1
            # else:
                # print(sent)
                # print(tagged)
                # print("\tP = "+taghat+" -> WRONG ("+tag+")")
                # input()
                # taghat="none"

            print(taghat)

        else:
            # total +=1
            taghat = "none"
            print(taghat)

        # if tag!="none":
            # os.sys.stderr.write(sent+":"+taghat+":"+tag+"\n")
        
        
    os.sys.stderr.write("total number of sentences = "+str(len(sents))+"\n")
    os.sys.stderr.write("number of grammatical tags predicted = "+str(total)+"\n")
    
    if total!=0: os.sys.stderr.write("precision on those considered gram = "+str(correct/total)+"\n")
    else: os.sys.stderr.write(str(0)+"\n")



