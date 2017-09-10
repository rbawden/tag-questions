# classify as producing a tag or not
import re, argparse, os, marshal
from math import log
from ast import literal_eval
import gzip
from readfile import *
from classify_tag_questions2 import get_anchor_and_tag, get_en_aux, get_en_pros, get_en_neg_words, is_en_tag

stop_words_fr = ['de', 'le', 'la', 'les', 'leur', 'du', 'des', 'et',
                 'ou', 'ni', 'ne', 'pas', 'je', 'tu', 'il', 'elle',
                 'nous', 'vous', 'ils', 'elles', 'se', "s'", "m'",
                 "t'", "n'", 'y', 'en', "d'", "l'", "j'"]


# tokenised source file (containing tags and non tags)
# def read_source_file(filename):
#     sents = []
#     with open(filename, "r", encoding="utf-8") as fp:
#         for line in fp:
#             sents.append(line.split())
#     return sents


# get vocab
def get_vocab(sents, hapax=-1):
    os.sys.stderr.write("getting vocabulary...")
    os.sys.stderr.flush()
    vocab  = {}
    for sent in sents:
        for word in sent:
            if word not in vocab: vocab[word] = 0
            vocab[word] += 1
    os.sys.stderr.write("done ("+str(len(vocab))+" words in vocabulary)\n")

    # filter very rare ones
    filt_vocab = set([])
    if hapax>0:
        os.sys.stderr.write("filtering words with occs <= "+str(hapax)+"...")
        os.sys.stderr.flush()
        for word in vocab:
            if vocab[word] <= hapax: continue
            else: filt_vocab.add(word)
        os.sys.stderr.write("done ("+str(len(filt_vocab))+" words left)\n")
    else:
        filt_vocab = set(keys(vocab))
    
    return filt_vocab


    
# get non-language specfic features

de_tags = ["nicht wahr", "nicht", "oder", "ne", "ja", "gell", "nä", "na", "ge", "nein", "was", "oder was",
           "hm", "ok(ay)?", "richtig", "w(?:ü|ue)rden Sie", "stimmt'?s", "klar", "verstanden", "he", "wie",
           "kapiert", "h[aä]h?", "echt", "eh", "oder nicht", "wei(ß|ss)t du", "oder was", "verstehst du",
           "alles klar", "in Ordnung", "wissen Sie", "verstehen Sie", "hörst du", "siehst du", "schon vergessen",
           "wisst ihr", "oder so", "oder doch", "stimmt das", "sehen Sie", "versteht ihr", "oder wie", "ist das",
           "oder \.\.\."]

fr_tags = ["n\' est \-ce pas", "non", "hein", "pas vrai", "d\' accord",
            "ou quoi", "tu ne crois pas", "tu ne trouves? pas", "c\' est ça",
            "dis", "dites", "ok", "okay", "voulez \-vous", "veux \-tu", "si",
            "oui", "alors", "tu vois", "tu ne vois pas", "vois \-tu",
            "tu crois", "crois \-tu", "souviens \-toi", "souvenez \-vous"]
    
cs_tags = ["ne", "že", "co", "vid'(te)?", "že ne", "že ?jo", "ano", "nemyslíte", "jo",
           "že ano", "nebo n[eé]", "co (tomu)? říká(š|te)", "no ne", "vid' že ne", "nemám pravdu",
           "nebo jo", "že je to tak", "nezdá se vám", "je to tak", "viď",
           "nebo snad jo", "není-liž pravda", "co tomu říkáte",
           "není to tak", "no nemám pravdu", "no řekněte", "no nemyslíte", "to je snad jasné",
           "víš o tom", "rozumíš", "nechceš", "snad", "nezdá se vám", "řekni", "ok", "okay", "okej"]

xcs_tags = ["ne", "že", "co", "vid'(te)?", "že ne", "že ?jo", "ano", "nemyslíte", "jo",
           "že ano", "nebo n[eé]", "co (tomu)? říká(š|te)", "no ne", "vid' že ne", "nemám pravdu",
           "nebo jo", "že je to tak", "nezdá se vám", "xxx?co myslí(š|te)", "je to tak",
           "nebo snad jo", "není-liž pravda", "co tomu říkáte",
           "není to tak", "no nemám pravdu", "no řekněte", "no nemyslíte", "to je snad jasné",
           "víš o tom", "xxx?všiml jste si", "xxxnevzpomínáš si",
           "xxxje to tady", "xxxmáš za co", "rozumíš", "nechceš", "xxxjakjinak", "xxxco se dá dělat",
           "xxxvidím ti to na očích", "snad", "nezdá se vám", "xxx?řekni", "xxx!vy ne"]

non_viable_anchor_cs = ["ne", "jo", "prosím", "ano", "oh", "ach", "co", "uh", "ó", "bože", "tak", "vážně",
                        "ale", "och", "no", "velmi dobře", "óó", "sakra", "áh"] # 1 word? starts with capital
    
punct_and_space = "[\.\,\:\;\/\\\+\=\)\(\-\?\!\'\"\` ]"
cs_tag_regex = re.compile("(.*?)\, ("+"|".join(cs_tags)+")( [\.\?\!\"\' ]*)?$", re.I)
cs_notanchor = re.compile("^("+"|".join(non_viable_anchor_cs)+"|"+"|".join(cs_tags)+"|"+punct_and_space+")*$")
fr_tag_regex = re.compile("(.*?)\, ("+"|".join(fr_tags)+") \?", re.I)
de_tag_regex = re.compile("(.*?)\, ("+"|".join(de_tags)+") \?", re.I)

caps = "A-ZÉÊÈËÏÎÌÍÔÒÖÓÛÜÙÚÂÄÀÁÝĎĚŘŠŤŮŽČ"
single_uppercase_word = re.compile("^"+punct_and_space+"*["+caps+"][^ ]*"+punct_and_space+"*")


def is_viable_anchor(anchor, lang):
    if lang=="cs":
        if re.match(cs_notanchor, anchor) or re.match(single_uppercase_word, anchor):
            return False
        else: return True

def has_tag_in_source(sent, lang):
    # print(sent)
    if lang=="cs":
        tq = re.match(cs_tag_regex, sent)
        if tq:
            anchor = tq.group(1)
            if is_viable_anchor(anchor, lang): return tq.group(2)
    elif lang=="fr":
        tq = re.match(fr_tag_regex, sent)
        if tq:
            return tq.group(2)
    elif lang=="de":
        tq = re.match(de_tag_regex, sent)
        if tq:
            return tq.group(2)
    return False


def is_a_question(sent):
    if re.match(".*? \?[\'\"\! ]*", sent): return True
    else: return False



def sort_by_len(list_str):
    list_str.sort(key = lambda x: len(x))
    return list_str

#-------------------------------------------------------
# CZECH RESOURCES AND INFO
#-------------------------------------------------------
# https://hal.archives-ouvertes.fr/hal-00911083/document
# can echo the verb of the question...
cs_reply = ["ano", "ne", "prosím", "promiňte", "děkuj[iu]", "ok", "fajn",
            "dob[řr][ée]", "samozřejmě", "jistě", "rozhodně ne", "jo", "te jo", "ale jo",
            "žádném případě","samozřejmě že ne", "ovšem ?že ne", "ale ne", "ale a?no",
            "rozhodně", "určitě", "no"]
    
cs_suffix = ["n?u", "[jn]?e[sš]", "[jnš]?e", "[jn]?eme", "[jn]?ete", "n?ou", "[ňjí]?me", "[jňí]?te", "[jn]?i", "n?ěme", "n?ěte",
             "n?a", "n?ouc", "n?ouce", "iž", "ení", "(?<!ů)l", "en", "íte", "í[ms]?", "ň", "[ěe]?jí", "jíce", "j", "ě", "íc[e]",
             "[eě]j[tm]?e", "[aeě]jíce?", "i", "á[m]"]
    
# cs_prefix = ["ne"]

# cs_verblist = read_ftl("/Users/rbawden/Documents/data/lexica/lexicon-de.ftl", "verb")
parallel_cs_re = re.compile("(^|.*? )([^ ]+)("+"|".join(cs_suffix)+") .*? \? ### (?:(?:[^ ]+ ){0,2})?((ne)?\\2)("+"|".join(cs_suffix)+")( .*?[^\?]$|$)")
no_cs_verb=["pane", "stane", "kapitáne", "poledne", "maine", "on-line", "online", "offline", "akne", "mne", "žene", "pravdu", "spolu", "znovu", "dobře", "kardinál","ráje"]
#-------------------------------------------------------

en_reply = ["ye+a*h", "yes", "no+", "na+h+", "o+k(a+y+)?", "of course", "well", "certainly", "sure", "definitely",
            "I agree", "well yes", "well no", "never", "no way"]

contr_en = ["\'d", "\'s", "ai", "\'ll", "\'d", "'\re"]
parallel_en_re = re.compile(".*? \? ### (?:[^ ]+ ){0,1}(?:\, )?("+"|".join(get_en_pros())+") ((?:"+"|".join(get_en_neg_words())+") )?("+"|".join(contr_en)+"|"+"|".join(get_en_aux())+")( (?:"+"|".join(get_en_neg_words())+"))?( |$)", re.I)


#-------------------------------------------------------
# GERMAN RESOURCES AND INFO
#-------------------------------------------------------
# de_verblist = read_ftl("/Users/rbawden/Documents/data/lexica/lexicon-de.ftl", "verb", True)
de_reply = ["ja", "doch", "oh ja", "ach ja", "au ja", "klar", "allerdings",
            "natürlich", "selbstverständlich", "echt", "wirklich", "nein", "ok", "o\.k\.",
            "okay"]
#-------------------------------------------------------
# FRENCH RESOURCES AND INFO
#-------------------------------------------------------
    
fr_reply = ["oui", "ouais", "ok", "okay", "non", "certes", "non", "bah oui", "bah non"]


def reply_parallel(sent, nextsent, lang, verblist):
    both = sent+" ### "+nextsent

    # print(sent)
    # print(nextsent)

    if lang[0:2]=="cs":
        par_match = re.match(parallel_cs_re, both)
        if par_match:
            if (par_match.group(2)+par_match.group(3)).strip() in verblist:
                if par_match.group(5):
                    ["hasParallelReplyCS", "parallelCSVerbA-"+par_match.group(2)+par_match.group(3),
                     "parallelCSVerbB-"+par_match.group(4)+par_match.group(6), "parallelCSReplyNeg"]
                else: 
                    return ["hasParallelReplyCS", "parallelCSVerbA-"+par_match.group(2)+par_match.group(3),
                            "parallelCSVerbB-"+par_match.group(4)+par_match.group(6)]
    if lang[0:2]=="de":
        src_verblemmas = []
        src_verbtoks = []
        tgt_verbtoks = []
        tgtverb2srctokid = []
        
        for t, tok in enumerate(sent.split()):
            if tok in verblist:
                src_verblemmas.append(verblist[tok])
                if t>0: src_verbtoks.append((sent.split()[t-1], tok))
                else: src_verbtoks.append(("$BEGIN", tok))

        if len(src_verbtoks)==0: return 
                    
        setlemmas = set([lem for lemlist in src_verblemmas for lem in lemlist])

        for t, tok in enumerate(nextsent.split()):
            # if a verb and appeared (in any form) in source sentence
            if tok in verblist and set(verblist[tok]).intersection(setlemmas)!=0:
                lemmas = set(verblist[tok])

                for l, lem in enumerate(src_verblemmas):
                    # if matches this source lemma
                    if len(set(lem).intersection(lemmas))!=0:
                        # print(set(lem).intersection(lemmas))
                        
                        tgtverb2srctokid.append(l)
                        if t>0: tgt_verbtoks.append((nextsent.split()[t-1], tok))
                        else: tgt_verbtoks.append(("$BEGIN", tok))
                        break # only take first one (maybe change later)

        # print("*     "+str(tgt_verbtoks))
        # print(tgtverb2srctokid)
        if len(tgt_verbtoks)>0:
            # print(src_verbtoks)
            # print(src_verblemmas)
            # print(tgt_verbtoks)
            # print(tgtverb2srctokid)
            # print(src_verbtoks[tgtverb2srctokid[0]])
                
            return ["hasParallelReplyDE", "parallelDEVerbA-"+src_verbtoks[tgtverb2srctokid[0]][1],
                    "parallelDEVerbB-"+tgt_verbtoks[0][1], "parallelDEPrecA-"+src_verbtoks[tgtverb2srctokid[0]][0],
                    "parallelDEPrecB-"+tgt_verbtoks[0][0]]

                
    elif lang[0:2]=="en":
        par_match = re.match(parallel_en_re, both)
        if par_match:
            if par_match.group(2) or par_match.group(4): neg="1"
            else: neg="0"
            return ["hasParallelReplyEN", "parallelVerbNnA-"+par_match.group(1), "parallelVerbENB-"+par_match.group(3), neg]

    return None

def has_reply(sent, nextsent, lang):
    if lang[0:2]=="cs":
        for c in cs_reply:
            if re.match(c+"( |$)", nextsent):
                c = re.sub("[ \?\*\+\[\]]", "—", c)
                return c
        return "NA"
    elif lang[0:2]=="de":
        for d in de_reply:
            if re.match(d+"( |$)", nextsent):
                d = re.sub("[ \?\*\+\[\]]", "—", d)
                return d
        return "NA"
    elif lang[0:2]=="fr":
        for f in fr_reply:
            if re.match(f+"( |$)", nextsent):
                f = re.sub("[ \?\*\+\[\]]", "—", f)
                return f
        return "NA"
    elif lang[0:2]=="en":
        for e in en_reply:
            if re.match(e+"( |$)", nextsent):
                e = re.sub("[ \?\*\+\[\]]", "—", e)
                return e
        return "NA"    
    else:
        exit("Language "+lang+" not recognised")



def get_features_gram(sent, gwords, gram=1, featnum=0, sourcesent=True):
    sent = "$BEGIN$ "*(gram-1)+sent+" $END$"*(gram-1)
    #print(sent)
    splitsent = sent.split(" ")
    gramsent = [tuple(splitsent[w:w+gram]) for w in range(len(splitsent)-gram+1)]
    
    #x= ["T" if g in gramsent else "False" for i, g in enumerate(gwords)]


    if sourcesent: x = ["gram-"+str(gram)+"-"+"_".join(g) for g in gwords if g in gramsent]
    else: x = ["gramTgt-"+str(gram)+"-"+"_".join(g) for g in gwords if g in gramsent]

    # print(x)
    # input()
    #for g in gwords:
        #print(g)
        #if g in gramsent:
        #    print(str(g)+"yes")
        #    input()
        #else: print(str(g))
    #input()
    return x


def read_filminfo(filename):
    films = []
    if "gz" in filename:
        fp = gzip.open(filename, "rt")
    else:
        fp = open(filename, "r")
    for line in fp.readlines():
        film2info = {}
        line = line.split("\t")
        # print(line)
        film2info["filmnum"] = line[0]
        film2info["firstline"] = line[1]
        film2info["lastline"] = line[2]
        film2info["year"] = line[4]
        film2info["originallanguage"] = line[6]
        film2info["genre"] = line[7]
        films.append(film2info)
        # print(film2info)
        # input()
    fp.close()
    return films
        

def read_datasetinfo(filename):
    dataset2info = {}
    with open(filename) as fp:
        for i, line in enumerate(fp.readlines()):
            if i==0: continue
            line = line.split(":")
            linenums = line[1].split("(")[0]
            dataset2info[line[0].strip()] = (int(linenums.split("-")[0]), int(linenums.split("-")[1]))
    return dataset2info


def merge_filminfo_datasetinfo(films, dataset2info, dataset):

    # special manoevure for split set
    if dataset=="dev1DEV":
        start_set, _ = dataset2info["dev1"]
        end_set= start_set+2043618
    elif dataset=="dev1TEST":
        _, end_set = dataset2info["dev1"]
        start_set = end_set-2043619
    else:
        start_set, end_set = dataset2info[dataset]
        
    linenum = 1
    lines2filminfo = {}
    # print(dataset2info)
    for film in films:
        if int(film["firstline"]) >= start_set and int(film["lastline"]) <= end_set:
            numlines = int(film["lastline"])-int(film["firstline"])
            lines2filminfo[(linenum, linenum+numlines)] = {"genre" :film["genre"],
                                                           "originallanguage": film["originallanguage"],
                                                           "year": film["year"]}
            linenum += numlines
            # print(film)
            # print(lines2filminfo)
            # input()
    return lines2filminfo

def strip_punct(en):
    # os.sys.stderr.write("["+str(en)+"]\n")
    en = re.sub("^[ \'\"\-\,\.\:\;\`\)\(]+", "", en)
    en = re.sub("[ \'\"\-\,\.\:\;\`\)\(]+$", "", en)
    return en

pron_aux_re = re.compile("(?:^|.*?)("+"|".join(get_en_pros())+") (?:("+"|".join(get_en_neg_words())+") )?("+"|".join(get_en_aux())+")(?: ("+"|".join(get_en_neg_words())+"))?", re.I)
last_pron = re.compile("(?:^|.*?)("+"|".join(get_en_pros())+") ([^ ]+)(?!.*? ("+"|".join(get_en_pros())+")( |$))", re.I)
last_aux = re.compile("(?:^|.*?)("+"|".join(get_en_aux())+")(?!.*? ("+"|".join(get_en_aux())+")( |$))", re.I)

def get_info_pron_aux(line):
    x = []
    pron_aux_match = re.match(pron_aux_re, line)
    if pron_aux_match:
        x.append(pron_aux_match.group(1))
    pron_match = re.match(last_pron, line)
    if pron_match:
        x.append(pron_match.group(1))
        x.append(pron_match.group(2))
    aux_match = re.match(last_aux, line)
    if aux_match:
        x.append(pron_match.group(1))
    return x

# 6 features
def get_anchor_features(line, featnum):
    x = []
    # pronoun and auxiliary (can be neg)
    pron_aux_match = re.match(pron_aux_re, line)
    if pron_aux_match:
        x.append("lastAuxPronPron-"+pron_aux_match.group(1).lower())
        x.append("lastAuxPronAux-"+pron_aux_match.group(3).lower())
        if pron_aux_match.group(2) or pron_aux_match.group(4):
            x.append("lastAuxPronNeg")

    # last pronoun
    pron_match = re.match(last_pron, line)
    if pron_match:
        x.append("lastPronPron-"+pron_match.group(1).lower().replace("'","'"))
        x.append("lastPronVerb-"+pron_match.group(2).lower().replace("'","'"))

    # last auxiliary
    aux_match = re.match(last_aux, line)
    if aux_match:
        x.append("lastAuxAux-"+aux_match.group(1).lower())

    return x, featnum+6    
    
   
#----------------------------------------------------------------
def get_features(dataset_folder, main_folder, ftl_lexicon, lang_pair, dataset, tagtype):

    langsrc = lang_pair.split("-")[0]
    langtgt = lang_pair.split("-")[1]
    if dataset_folder[-1]=="/": dataset_folder = dataset_folder[:-1]
    if main_folder[-1]=="/": main_folder = main_folder[:-1]    
    # if langsrc=="fr" and tagtype=="real":
    #     filename_preproc_fr="ref."+dataset+".incomplete.fr-en.fr"
    #     filename_trans_fr="pred."+dataset+".incomplete.fr-en.en"
    # else:
    filename_preproc = dataset+".truecased."+lang_pair+"."+langsrc+".gz"
    if tagtype == "real":
        # filename_preproc_fr = ".raw.precleaned.birecoded.cleaned.noblank.melttok.truecased.2000-2016"
        # filename_preproc = ".raw.nocr.cleaned.noblank.melttok.truecased.2000-2016"
        # filename_trans_fr = filename_preproc_fr+".2000-2016"
        # filename_trans
        # =".raw.nocr.cleaned.noblank.preproc.amunmt.postproc.melttok.2000-2016"
        filename_trans = dataset+".translated.melttok."+lang_pair+"."+langtgt+".gz"
    
    #----------------------------------------------
    os.sys.stderr.write("Preparing feature data\n")
    # different data and files necessary
    
    # if lang_pair=="fr-en":

    #     if tagtype=="real":
    #         uni_sents = read_source_file(dataset_folder+"/"+filename_preproc_fr) # source file
    #         uni_translations = read_source_file(dataset_folder+"/"+lang_pair+"/"+filename_trans_fr) # translated file
    #     else:
    #         uni_sents = read_source_file(dataset_folder+"/"+filename_preproc_fr+".fr") # source file
    #         if tagtype=="real" and "dev" in dataset:
    #             uni_translations = read_source_file(main_folder+"/translations/"+lang_pair+"/"+filename_trans_fr+"."+lang_pair+".en") # translated file
    
    uni_sents = read_source_file(dataset_folder+"/"+filename_preproc) # source file
    if tagtype == "real":
        uni_translations = read_source_file(main_folder+"/classify/"+lang_pair+"/baseline/"+dataset+".all.finaltranslations."+lang_pair+"."+langtgt+".gz") #main_folder+"/translations/"+lang_pair+"/"+filename_trans) # translated file
        
    #----------------------------------------------
    # tag_lines = read_tag_file(tagfile, len(uni_sents))
    # if langsrc=="fr" and tagtype=="real":
        # tagtypes = read_text_file(dataset_folder+"/gold/"+dataset+".gold."+tagtype+"."+lang_pair)
    # else:    
    tagtypes = read_text_file(main_folder+"/classify/"+lang_pair+"/gold/"+dataset+"."+tagtype+"."+lang_pair+".gz")
    # filminfo = read_filminfo(dataset_folder+"/filminfo.final.list.gz")
    # dataset_info = read_datasetinfo(dataset_folder+"/datasets.info")
    # lines2filminfo = merge_filminfo_datasetinfo(filminfo, dataset_info, dataset)
    
    #----------------------------------------------
    # gtest files
    srcg = "trainsmall"
    trgg = "trainsmall"
    uni_g = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+srcg+".1g."+lang_pair+"."+langsrc+".gz", 500)
    bi_g = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+srcg+".2g."+lang_pair+"."+langsrc+".gz", 500)
    tri_g = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+srcg+".3g."+lang_pair+"."+langsrc+".gz", 500)
    if tagtype=="real":
        uni_g_trans = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+trgg+".1g.trans."+lang_pair+"."+langtgt+".gz", 500)
        bi_g_trans = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+trgg+".2g.trans."+lang_pair+"."+langtgt+".gz", 500)
        tri_g_trans = read_g_file(main_folder+"/classify/"+lang_pair+"/gtests/gtest."+trgg+".3g.trans."+lang_pair+"."+langtgt+".gz", 500)

    # extra things to load
    if langsrc[0:2]=="cs": list_replies = sort_by_len(cs_reply)
    verblist = None
    if ftl_lexicon:
        if langsrc[0:2]=="cs": verblist = read_ftl(ftl_lexicon, "verb")
        elif langsrc[0:2]=="de": verblist = read_ftl(ftl_lexicon, "verb", True)
    #--------------------------------------------
    os.sys.stderr.write("Writing features\n")
    for i, (uni_sent, gold) in enumerate(zip(uni_sents, tagtypes)):
        if i%1000==0: os.sys.stderr.write("\r   "+str(i))

        sent = " ".join(uni_sent)

        # replace : chars
        sent = sent.replace(":", "-")
        
        if tagtype=="real":
            uni_trans = uni_translations[i]
            trans = " ".join(uni_trans)
            trans = trans.replace(":", "-")
        if i < len(uni_sents)-1:
            nextsent = " ".join(uni_sents[i+1]).replace(":", "-")
            if tagtype=="real":
                uni_sent = uni_translations[i]
                nexttrans = " ".join(uni_translations[i+1])
        else:
            nextsent="NA"
            nexttrans = "NA"

        #------------------------------------------------
        # FEATURES START HERE
        #------------------------------------------------
        x = []


        # FIRST CLASSIFIER
        if True:
            #------------------------------------------------
            # 0: gold
            #------------------------------------------------
            if tagtype=="tagnottag":
                if str(gold)=='True': x = ["1"]
                else: x = ["-1"]
            else :
                tag = str(gold).replace(" ", "_").replace("'", "-")
                if tag.strip()=="okay": tag="ok"
                x = [tag]       
            #------------------------------------------------
            # 1             : tagInSrc
            #------------------------------------------------
            tagSrc = has_tag_in_source(sent, langsrc)
            if tagSrc!=False:
                tagSrc = re.sub("[\:\?\* \']", "-", tagSrc)
                x.append("hasTaginSrc-"+tagSrc)

            #------------------------------------------------
            # 2             : isAQuestion
            #------------------------------------------------
            if is_a_question(sent): x.append("isAQuestion")

            #------------------------------------------------
            #    3 - 502    : g2-uni-500-fromTrain
            #  502 - 1003   : g2-uni-500-fromTrain
            # 1003 - 1502   : g2-uni-500-fromTrain
            #------------------------------------------------
            prefix=' '+srcg
            x.append(prefix.join(get_features_gram(sent, uni_g, 1, 3)))
            x.append(prefix.join(get_features_gram(sent, bi_g, 2, 503)))
            x.append(prefix.join(get_features_gram(sent, tri_g, 3, 1003)))

            #os.sys.stderr.write(str(x)+"\n")
            #input()

            for i in range(len(x[-3:])):
                if len(x[-3+i]) > 0:
                    x[-3+i] = prefix+x[-3+i]

            #os.sys.stderr.write(str(x)+"\n")
            #input()
                    
            # first words source
            # if len(sent.split())>0:
            #     x.append("firstWordSrc"+sent.lower().split()[0])
            # if len(sent.split())>1:
            #     x.append("first2WordsSrc-"+"_".join(sent.lower().split()[0:2]).replace(" ", "_").replace("'", "-"))
            # if len(sent.split())>2:
            #     x.append("first3WordsSrc-"+"_".join(sent.lower().split()[0:3]).replace(" ", "_").replace("'", "-"))
            # if len(sent.split())>3:
            #     x.append("first4WordsSrc-"+"_".join(sent.lower().split()[0:4]).replace(" ", "_").replace("'", "-"))

             
            #------------------------------------------------
            # 1504 - 1507    : parallelReply
            #------------------------------------------------
            parallel = reply_parallel(sent, nextsent, langsrc, verblist)
            if parallel:
                x.extend(parallel)
    
            #------------------------------------------------
            # 1508           : certainReply
            #------------------------------------------------
            reply = has_reply(sent, nextsent, langsrc)
            if reply!="NA":
                x.append("hasCertainReply"+langsrc+"-"+reply)


        if tagtype=="real":
            #------------------------------------------------
            # 1509 - 2008    : g2-unitrans-500-fromTrain
            # 2010 - 2509    : g2-bitrans-500-fromTrain
            # 2511 - 3010    : g2-tritrans-500-fromTrain
            #------------------------------------------------
            prefix=' '+trgg
            x.append(prefix.join(get_features_gram(trans, uni_g_trans, 1, 1509, False)))
            x.append(prefix.join(get_features_gram(trans, bi_g_trans, 2, 2010, False)))
            x.append(prefix.join(get_features_gram(trans, tri_g_trans, 3, 2511, False)))        
    
            # prefix first
            for i in range(len(x[-3:])):
                if len(x[-3+i]) > 0:
                    x[-3+i] = prefix+x[-3+i]

            #------------------------------------------------
            # 3012           : isAQuestionTrans
            #------------------------------------------------
            if is_a_question(trans): x.append("isAQuestionTrans")
    
            #------------------------------------------------
            # 3013           : certainReplyTrans
            #------------------------------------------------
            reply = has_reply(sent, nextsent, "en")
            if reply!="NA":
                x.append("hasReplyTrans")
    
            #------------------------------------------------
            # 3014 - 3017    : parallelReplyTrans
            #------------------------------------------------            
            parallel = reply_parallel(trans, nexttrans, "en", verblist)
            if parallel:
                x.extend(parallel)
    
            #------------------------------------------------
            # 3018 - 3025    : anchorTrans
            #------------------------------------------------ 
            if is_en_tag(trans):
                anchor, tag = get_anchor_and_tag(trans)
                anchor = strip_punct(anchor)
                tag = strip_punct(tag)
    
                anchor_features, featnum = get_anchor_features(anchor, 3018) # 6 features
                if len(anchor_features)>0:
                    x.append(" ".join(anchor_features))
    
                #------------------------------------------------
                # 3026       : tagTrans
                #------------------------------------------------ 
                x.append("tagTrans-"+tag.replace(" ", "_"))
    
            #------------------------------------------------
            # 3027 - 3029    : firstWordsTrans
            #------------------------------------------------             
            if len(trans.split())>0:
                x.append("firstWordTrans"+trans.lower().split()[0])
            if len(trans.split())>1:
                x.append("first2WordsTrans-"+"_".join(trans.lower().split()[0:2]).replace(" ", "_").replace("'", "-"))
            if len(trans.split())>2:
                x.append("first3WordsTrans-"+"_".join(trans.lower().split()[0:3]).replace(" ", "_").replace("'", "-"))
            if len(trans.split())>3:
                x.append("first4WordsTrans-"+"_".join(trans.lower().split()[0:4]).replace(" ", "_").replace("'", "-"))
    
            #------------------------------------------------
            # 3030           : firstClassifier
            #------------------------------------------------            
            # DO NOT USE THIS FEATURE FOR ANOTHER VALUE
    
            
        # PRINT OUT
        print(" ".join(x))
        # input()
    os.sys.stderr.write("\n")

            
if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    # argparser.add_argument("source_file")
    # argparser.add_argument("taglinefile")
    # argparser.add_argument("-g", nargs=3, help="ngram files from gtest", metavar=('uni', 'bi', 'tri'), required=True)
    argparser.add_argument("dataset_folder")
    argparser.add_argument("main_folder")
    argparser.add_argument("ftl_lexicon", default=None)
    argparser.add_argument("-l", choices=["de-en", "fr-en", "cs-en", "fr2000-en2000", "cs2000-en2000", "de2000-en2000"], required=True)
    argparser.add_argument("-d", choices=["train", "dev1", "dev2", "test", "trainsmall", "devsmall", "testsmall"], required=True)
    argparser.add_argument("-t", choices=["tagnottag", "fine", "finer", "real"], required=True)
    args = argparser.parse_args()

    # source_sents = read_source_file(args.source_file)
    # tag_lines = read_tag_file(args.taglinefile, len(source_sents))
    
    
    #uni, bi, tri = tuple(args.g[0:3])

    if args.ftl_lexicon=="None": args.ftl_lexicon = None
    
    get_features(args.dataset_folder, args.main_folder, args.ftl_lexicon, args.l, args.d, args.t)
    
    # get_features(args.source_file, args.taglinefile, lang, uni, bi, tri)

    # os.sys.stderr.write("Writing output\n")
    # for d in data:
        # d = [str(x) for x in d]
        # os.sys.stdout.write("|".join(d)+"\n")
    # gtest(source_sents, tag_lines)

    

    # get_langspec_features(source_sents, lang)    
    # vocab = get_vocab(source_sents, 50)

    



