"""
LDA Model
=========

Introduces Gensim's LDA model and demonstrates its use on the NIPS corpus.

"""
import copy
import csv
import logging
import time
from statistics import mean

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

import helper

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.CRITICAL)

###############################################################################
# The purpose of this tutorial is to demonstrate training an LDA model and
# obtaining good results.
#
# In this tutorial we will:
#
# * Load data.
# * Pre-process data.
# * Transform documents to a vectorized form.
# * Train an LDA model.
#
# This tutorial will **not**:
#
# * Explain how Latent Dirichlet Allocation works
# * Explain how the LDA model performs inference
# * Teach you how to use Gensim's LDA implementation in its entirety
#
# If you are not familiar with the LDA model or how to use it in Gensim, I
# suggest you read up on that before continuing with this tutorial. Basic
# understanding of the LDA model should suffice. Examples:
#
# * `Introduction to Latent Dirichlet Allocation <http://blog.echen.me/2011/08/22/introduction-to-latent-dirichlet-allocation>`_
# * Gensim tutorial: :ref:`sphx_glr_auto_examples_core_run_topics_and_transformations.py`
# * Gensim's LDA model API docs: :py:class:`gensim.models.LdaModel`
#
# I would also encourage you to consider each step when applying the model to
# your data, instead of just blindly applying my solution. The different steps
# will depend on your data and possibly your goal with the model.
#
# Data
# ----
#
# I have used a corpus of NIPS papers in this tutorial, but if you're following
# this tutorial just to learn about LDA I encourage you to consider picking a
# corpus on a subject that you are familiar with. Qualitatively evaluating the
# output of an LDA model is challenging and can require you to understand the
# subject matter of your corpus (depending on your goal with the model).
#
# NIPS (Neural Information Processing Systems) is a machine learning conference
# so the subject matter should be well suited for most of the target audience
# of this tutorial.  You can download the original data from Sam Roweis'
# `website <http://www.cs.nyu.edu/~roweis/data.html>`_.  The code below will
# also do that for you.
#
# .. Important::
#     The corpus contains 1740 documents, and not particularly long ones.
#     So keep in mind that this tutorial is not geared towards efficiency, and be
#     careful before applying the code to a large dataset.
#

import io
import os.path
import re
import tarfile

import smart_open
from wordcloud import STOPWORDS
from itertools import combinations

def extract_documents(url='https://cs.nyu.edu/~roweis/data/nips12raw_str602.tgz'):
    fname = url.split('/')[-1]

    # Download the file to local storage first.
    # We can't read it on the fly because of
    # https://github.com/RaRe-Technologies/smart_open/issues/331
    if not os.path.isfile(fname):
        with smart_open.open(url, "rb") as fin:
            with smart_open.open(fname, 'wb') as fout:
                while True:
                    buf = fin.read(io.DEFAULT_BUFFER_SIZE)
                    if not buf:
                        break
                    fout.write(buf)

    with tarfile.open(fname, mode='r:gz') as tar:
        # Ignore directory entries, as well as files like README, etc.
        files = [
            m for m in tar.getmembers()
            if m.isfile() and re.search(r'nipstxt/nips\d+/\d+\.txt', m.name)
        ]
        for member in sorted(files, key=lambda x: x.name):
            member_bytes = tar.extractfile(member).read()
            yield member_bytes.decode('utf-8', errors='replace')

stopset = set(
        ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
         "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
         "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
         "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
         "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
         "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
         "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
         "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such","only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
         "should", "now", 've', 'let', 'll','re',"etc"])
negationstopset=set(['aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn','mustn', 'nan', 'negative', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn', "no", "nor", "not"])


def getStopwords(stopset):
    stopwords = set(STOPWORDS)
    stopwords.update(stopset)
    return stopwords


def computetopacc(top_topics):
    comb = combinations(range(len(top_topics)), 2)
    countdiff=[]
    combins=list(comb)
    nwords=len(top_topics[0][0])
    for i in combins:
        top1=[w[1] for w in ((top_topics[i[0]])[:-1])[0]]
        top2 = [w[1] for w in ((top_topics[i[1]])[:-1])[0]]
        # postag=nltk.pos_tag([w[1] for w in tops])
        countcommon=0
        for w in top1:
            if w in top2:
                countcommon+=1
        countdiff.append(nwords-countcommon)
    return mean(countdiff)/nwords

cc=[]
def savemodel(model,keyword,emotion,corpus):
    if not os.path.exists('resources/gensim/' + keyword + '_' + emotion.lower() + '/'):
        os.makedirs('resources/gensim/' + keyword + '_' + emotion.lower() + '/')
    model.save('resources/gensim/' + keyword + '_' + emotion.lower() + '/' + keyword + '_' + emotion.lower())
    csv_file = open('resources/gensim/' + keyword + '_' + emotion.lower() + '/' + keyword + '_' + emotion.lower()+'.csv', mode='w', encoding="utf8",
                    newline='\n')
    for top in model.top_topics(corpus):
        writer = csv.writer(csv_file, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        l=top[0]
        l.append(top[1])
        writer.writerow(l)
    csv_file.close()


def do(originfile):
    keywords = helper.getKeywords(originfile)
    for emotion in ['Good', 'Bad']:
        print("begin " + emotion)
        for keyword in keywords.keys():
            start_time = time.time()
            print(keyword)
            raw_corpus = helper.getRawCorpus(
                csv_file=open('resources/csvs/' + keyword + '_' + emotion.lower() + '.csv', mode='r',
                              encoding="utf8", newline='\n'), all=True)
            print("starting preprocessing")
            corpus=helper.preprocessRawCorpus(raw_corpus[:1000],thresholdcountpernation=100)

            ###############################################################################
            # So we have a list of 1740 documents, where each document is a Unicode string.
            # If you're thinking about using your own corpus, then you need to make sure
            # that it's in the same format (list of Unicode strings) before proceeding
            # with the rest of this tutorial.
            #

            ###############################################################################
            # Pre-process and vectorize the documents
            # ---------------------------------------
            #
            # As part of preprocessing, we will:
            #
            # * Tokenize (split the documents into tokens).
            # * Lemmatize the tokens.
            # * Compute bigrams.
            # * Compute a bag-of-words representation of the data.
            #
            # First we tokenize the text using a regular expression tokenizer from NLTK. We
            # remove numeric tokens and tokens that are only a single character, as they
            # don't tend to be useful, and the dataset contains a lot of them.
            #
            # .. Important::
            #
            #    This tutorial uses the nltk library for preprocessing, although you can
            #    replace it with something else if you want.
            #

            # Tokenize the documents.
            from nltk.tokenize import RegexpTokenizer

            # Split the documents into tokens.

            stopwords = getStopwords(stopset)
            stwfromtfidf = list(TfidfVectorizer(stop_words='english').get_stop_words())
            stopwords = set(list(stopwords) + stwfromtfidf)
            for w in negationstopset:
                stopwords.add(w)

            tokenizer = RegexpTokenizer(r'\w+')
            print("starting tokenization")
            for idx in range(len(corpus)):
                corpus[idx] = corpus[idx].lower()  # Convert to lowercase.
                corpus[idx] = tokenizer.tokenize(corpus[idx])  # Split into words.
                corpus[idx]=[tok for tok in corpus[idx] if tok not in stopwords]
            # Remove numbers, but not words that contain numbers.
            corpus = [[token for token in doc if not token.isnumeric()] for doc in corpus]

            # Remove words that are shorter than 3 characters.
            corpus = [[token for token in doc if len(token) > 2] for doc in corpus]

            ###############################################################################
            # We use the WordNet lemmatizer from NLTK. A lemmatizer is preferred over a
            # stemmer in this case because it produces more readable words. Output that is
            # easy to read is very desirable in topic modelling.
            #

            # Lemmatize the documents.
            from nltk.stem.wordnet import WordNetLemmatizer

            print("starting lemmatization")
            lemmatizer = WordNetLemmatizer()
            corpus = [[lemmatizer.lemmatize(token) for token in doc] for doc in corpus]

            ###############################################################################
            # We find bigrams in the documents. Bigrams are sets of two adjacent words.
            # Using bigrams we can get phrases like "machine_learning" in our output
            # (spaces are replaced with underscores); without bigrams we would only get
            # "machine" and "learning".
            #
            # Note that in the code below, we find bigrams and then add them to the
            # original data, because we would like to keep the words "machine" and
            # "learning" as well as the bigram "machine_learning".
            #
            # .. Important::
            #     Computing n-grams of large dataset can be very computationally
            #     and memory intensive.
            #


            # Compute bigrams.
            from gensim.models import Phrases
            print("doing bigrams")
            # Add bigrams and trigrams to docs (only ones that appear 20 times or more).
            bigram = Phrases(corpus, min_count=20)
            for idx in range(len(corpus)):
                for token in bigram[corpus[idx]]:
                    if '_' in token:
                        # Token is a bigram, add to document.
                        corpus[idx].append(token)
            ###############################################################################
            # We remove rare words and common words based on their *document frequency*.
            # Below we remove words that appear in less than 20 documents or in more than
            # 50% of the documents. Consider trying to remove words only based on their
            # frequency, or maybe combining that with this approach.
            #

            # Remove rare and common tokens.
            from gensim.corpora import Dictionary

            # Create a dictionary representation of the documents.
            dictionary = Dictionary(corpus)

            # Filter out words that occur less than 20 documents, or more than 50% of the documents.
            #dictionary.filter_extremes(no_below=20, no_above=0.5)
            print("filtering extremes")
            dictionary.filter_extremes(no_below=0, no_above=0.5)

            ###############################################################################
            # Finally, we transform the documents to a vectorized form. We simply compute
            # the frequency of each word, including the bigrams.
            #

            # Bag-of-words representation of the documents.
            print("converting to vectors with doc2bow")
            corpus = [dictionary.doc2bow(doc) for doc in corpus]

            ###############################################################################
            # Let's see how many tokens and documents we have to train on.
            #

            print('Number of unique tokens: %d' % len(dictionary))
            print('Number of documents: %d' % len(corpus))

            ###############################################################################
            # Training
            # --------
            #
            # We are ready to train the LDA model. We will first discuss how to set some of
            # the training parameters.
            #
            # First of all, the elephant in the room: how many topics do I need? There is
            # really no easy answer for this, it will depend on both your data and your
            # application. I have used 10 topics here because I wanted to have a few topics
            # that I could interpret and "label", and because that turned out to give me
            # reasonably good results. You might not need to interpret all your topics, so
            # you could use a large number of topics, for example 100.
            #
            # ``chunksize`` controls how many documents are processed at a time in the
            # training algorithm. Increasing chunksize will speed up training, at least as
            # long as the chunk of documents easily fit into memory. I've set ``chunksize =
            # 2000``, which is more than the amount of documents, so I process all the
            # data in one go. Chunksize can however influence the quality of the model, as
            # discussed in Hoffman and co-authors [2], but the difference was not
            # substantial in this case.
            #
            # ``passes`` controls how often we train the model on the entire corpus.
            # Another word for passes might be "epochs". ``iterations`` is somewhat
            # technical, but essentially it controls how often we repeat a particular loop
            # over each document. It is important to set the number of "passes" and
            # "iterations" high enough.
            #
            # I suggest the following way to choose iterations and passes. First, enable
            # logging (as described in many Gensim tutorials), and set ``eval_every = 1``
            # in ``LdaModel``. When training the model look for a line in the log that
            # looks something like this::
            #
            #    2016-06-21 15:40:06,753 - gensim.models.ldamodel - DEBUG - 68/1566 documents converged within 400 iterations
            #
            # If you set ``passes = 20`` you will see this line 20 times. Make sure that by
            # the final passes, most of the documents have converged. So you want to choose
            # both passes and iterations to be high enough for this to happen.
            #
            # We set ``alpha = 'auto'`` and ``eta = 'auto'``. Again this is somewhat
            # technical, but essentially we are automatically learning two parameters in
            # the model that we usually would have to specify explicitly.
            #


            # Train LDA model.
            from gensim.models import LdaModel

            bestacc=-1
            bestmodel=None
            print("starting training and checking with different number of topics")
            for numt in range(2,21):

                # Set training parameters.
                num_topics = numt
                chunksize = 2000
                passes = 20
                iterations = 400
                eval_every = None  # Don't evaluate model perplexity, takes too much time.

                # Make a index to word dictionary.
                temp = dictionary[0]  # This is only to "load" the dictionary.
                id2word = dictionary.id2token

                model = LdaModel(
                    corpus=corpus,
                    id2word=id2word,
                    chunksize=chunksize,
                    alpha='auto',
                    eta='auto',
                    iterations=iterations,
                    num_topics=num_topics,
                    passes=passes,
                    eval_every=eval_every
                )

                ###############################################################################
                # We can compute the topic coherence of each topic. Below we display the
                # average topic coherence and print the topics in order of topic coherence.
                #
                # Note that we use the "Umass" topic coherence measure here (see
                # :py:func:`gensim.models.ldamodel.LdaModel.top_topics`), Gensim has recently
                # obtained an implementation of the "AKSW" topic coherence measure (see
                # accompanying blog post, http://rare-technologies.com/what-is-topic-coherence/).
                #
                # If you are familiar with the subject of the articles in this dataset, you can
                # see that the topics below make a lot of sense. However, they are not without
                # flaws. We can see that there is substantial overlap between some topics,
                # others are hard to interpret, and most of them have at least some terms that
                # seem out of place. If you were able to do better, feel free to share your
                # methods on the blog at http://rare-technologies.com/lda-training-tips/ !
                #

                top_topics = model.top_topics(corpus)  # , num_words=20)
                acc=computetopacc(top_topics)
                if acc>bestacc:
                    print("found better model with number of topics: "+str(model.num_topics))
                    bestacc=acc
                    bestmodel=copy.deepcopy(model)
                # Average topic coherence is the sum of topic coherences of all topics, divided by the number of topics.
                avg_topic_coherence = sum([t[1] for t in top_topics]) / num_topics
                cc.append(avg_topic_coherence)
                print('Average topic coherence: %.4f.' % avg_topic_coherence)
            savemodel(bestmodel, keyword, emotion, corpus)
            print(str(time.time() - start_time)+' seconds to compute '+keyword+' '+emotion)

    ###############################################################################
    # Things to experiment with
    # -------------------------
    #
    # * ``no_above`` and ``no_below`` parameters in ``filter_extremes`` method.
    # * Adding trigrams or even higher order n-grams.
    # * Consider whether using a hold-out set or cross-validation is the way to go for you.
    # * Try other datasets.
    #
    # Where to go from here
    # ---------------------
    #
    # * Check out a RaRe blog post on the AKSW topic coherence measure (http://rare-technologies.com/what-is-topic-coherence/).
    # * pyLDAvis (https://pyldavis.readthedocs.io/en/latest/index.html).
    # * Read some more Gensim tutorials (https://github.com/RaRe-Technologies/gensim/blob/develop/tutorials.md#tutorials).
    # * If you haven't already, read [1] and [2] (see references).
    #
    # References
    # ----------
    #
    # 1. "Latent Dirichlet Allocation", Blei et al. 2003.
    # 2. "Online Learning for Latent Dirichlet Allocation", Hoffman et al. 2010.
    #