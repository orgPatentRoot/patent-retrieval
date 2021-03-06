#!/usr/bin/python
import sys
import getopt
from collections import defaultdict
import string
import pickle
import nltk

stemmer = nltk.stem.porter.PorterStemmer()

try:
    from lxml import etree
    print("running with lxml.etree")
except ImportError:
    try:
    # Python 2.5+
        import xml.etree.cElementTree as etree
        print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
        # Python 2.5+
            import xml.etree.ElementTree as etree
            print("running with ElementTree on Python 2.5+")
        except ImportError:
            print("Failed to import ElementTree from any known place")
            sys.exit()

sys.path.append("lib")
import gensim

#-------------------------------------------------------------------------------

class Query(object):
    def __init__(self, dict_filename, post_filename, queries_filename, output_filename):
        self.query_filename = queries_filename
        self.output_filename = output_filename

        # open files produced by index
        self.dictionary = pickle.load(open(dict_filename, 'r'))
        self.topic_model = pickle.load(open(post_filename, 'r'))
        self.patent_mapping = pickle.load(open("temp-patent_mapping", 'r'))
        self.index = gensim.similarities.Similarity.load("temp-similarity_index")

        print self.dictionary, self.topic_model, self.patent_mapping, self.index

        self.stopwords = pickle.load(open("temp-stopwords", 'r'))
        query_stopwords = set(["relevant", "documents", "describe"])
        self.stopwords = self.stopwords.union(query_stopwords)

        self.query_bag = self.parse_query() # query to bag of words
        self.query_vector = self.topic_model[self.query_bag] # bag of words to vector
        
        self.results() # run vector through Similarity, return sorted list of results

    def parse_query(self):
        tokens = []

        with open(self.query_filename) as f:

            xml = etree.parse(f)

            for element in xml.iter():
                token_generator = gensim.utils.tokenize(element.text, lowercase = True)
                for token in token_generator:
                    if token not in self.stopwords:
                        tokens.append(stemmer.stem(token))

        return self.dictionary.doc2bow(tokens)

    def find_topic(self): # experimental
        return self.topic_model.print_topic(self.query_vector)

    def results(self):
        sims = self.index[self.query_vector]
        sims = sorted(enumerate(sims), key=lambda item: -item[1])
        with open(self.output_filename, 'w') as f:
            for doc_num, similarity in sims:
                if (similarity > 0.0):
                    f.write(self.patent_mapping[doc_num] + " ")
                    # f.write(self.patent_mapping[doc_num] + ", similarity = " + str(similarity) + "\n")


def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries_filename -o output-file-of-results"

dict_filename = post_filename = queries_filename = output_filename = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except:
    usage()
    sys.exit(2)
        
for o, a in opts:
    if o == '-d':
        dict_filename = a
    elif o == '-p':
        post_filename = a
    elif o == '-q':
        queries_filename = a
    elif o == '-o':
        output_filename = a
    else:
        assert False, "unhandled option"
if dict_filename == None or post_filename == None or queries_filename == None or output_filename == None:
    usage()
    sys.exit(2)


my_query = Query(dict_filename, post_filename, queries_filename, output_filename)