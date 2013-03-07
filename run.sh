# training CRF-based NER
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -trainFile data/zh.ner.train.samples -serializeTo ner/models/zh.ner.ser.gz -prop ner/models/zh.ner.prop 
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -trainFile data/en.ner.train.samples -serializeTo ner/models/en.ner.ser.gz -prop ner/models/en.ner.prop 

# predict NER results
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier ner/models/zh.ner.ser.gz -testFile data/zh.ner.test.samples > data/zh.ner.test.crf.out
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier ner/models/en.ner.ser.gz -testFile data/en.ner.test.samples > data/en.ner.test.crf.out

# predict NER probabilities
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier ner/models/zh.ner.ser.gz -testFile data/zh.ner.test.samples -printProbs > data/zh.ner.test.crf.probs
java -mx4g -cp ner/stanford-ner-2012-11-11/stanford-ner.jar edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier ner/models/en.ner.ser.gz -testFile data/en.ner.test.samples -printProbs > data/en.ner.test.crf.probs

# calculate PMI scores
cut -f1,3 data/zh.ner.test.crf.out > data/zh.ner.test.crf.2col.out
cut -f1,3 data/en.ner.test.crf.out > data/en.ner.test.crf.2col.out
python scripts/pmi-calc.py data/zh.ner.test.crf.2col.out data/en.ner.test.crf.2col.out data/HMM.t0.8.align > ilp/crf.pmi

# bilingual NER with ILP
python ilp/ilp-soft-2.py data/zh.ner.test.crf.probs data/en.ner.test.crf.probs data/HMM.align.soft 0.5 ilp/crf.pmi > data/zh.ner.test.bi_ilp.out 2> data/en.ner.test.bi_ilp.out

# evaluation
cut -f2 data/zh.ner.test.bi_ilp.out > data/zh.ner.test.bi_ilp.1col.out
cut -f2 data/en.ner.test.bi_ilp.out > data/en.ner.test.bi_ilp.1col.out
paste data/zh.ner.test.samples data/zh.ner.test.bi_ilp.1col.out > data/zh.ner.test.bi_ilp.3col.out
paste data/en.ner.test.samples data/en.ner.test.bi_ilp.1col.out > data/en.ner.test.bi_ilp.3col.out

echo 'Chinese CRF Performance'
perl scripts/conlleval.pl -d '\t' < data/zh.ner.test.crf.out
echo 'English CRF Performance'
perl scripts/conlleval.pl -d '\t' < data/en.ner.test.crf.out

echo 'Chinese Bi_ILP Performance'
perl scripts/conlleval.pl -d '\t' < data/zh.ner.test.bi_ilp.3col.out
echo 'English Bi_ILP Performance'
perl scripts/conlleval.pl -d '\t' < data/en.ner.test.bi_ilp.3col.out


