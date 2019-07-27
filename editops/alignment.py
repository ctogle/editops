"""Text alignment based analysis object oriented interface"""
from collections import defaultdict, Counter
from .editops import editops, editdistance


class Alignment:
    """An interface for analyzing a pair of unicode strings which provides
    character/word level alignments with useful visual representations.
    Faster computations of WER/CER are provided when a full alignment is
    otherwise unnecessary.
    """


    @staticmethod
    def _color_texts():
        """Provide functions to color code text"""
        from colored import fg, bg, attr
        def make_color_function(color):
            def add_color(text):
                a = attr(1) if text.isupper() else attr(0)
                return '%s%s%s%s%s' % (a, fg(0), bg(color), text, attr(0))
            return add_color
        return [make_color_function(i) for i in (1, 214, 220, 226, 154, 40)]


    @staticmethod
    def _repr_aligned_word_pair(s, t, colors=False, empty='*', fill='_'):
        """Compute visually useful representations of the aligned word pair (s, t)"""
        if s['correct'] and t['correct']:
            s, t = s['text'], t['text']
            if colors:
                s = colors[5](s)
                t = colors[5](t)
        else:
            if s['text'] is None:
                #t = t['text'].upper()
                t = t['text']
                s = empty * len(t)
                if colors:
                    s = colors[3](s)
                    t = colors[1](t)
            elif t['text'] is None:
                #s = s['text'].upper()
                s = s['text']
                t = empty * len(s)
                if colors:
                    s = colors[1](s)
                    t = colors[3](t)
            else:
                #s, t = s['text'].upper(), t['text'].upper()
                s, t = s['text'], t['text']
                m, n = len(s), len(t)
                if m > n:
                    t += fill * (m - n)
                elif m < n:
                    s += fill * (n - m)
                if colors:
                    s = colors[1](s)
                    t = colors[1](t)
        return s, t


    def __repr__(self):
        """Return a string showing a visually palatable alignment"""
        if not hasattr(self, '_s_align'):
            self._align()
        for s, t in self:
            s['repr'], t['repr'] = self._repr_aligned_word_pair(s, t,
                colors=self._color_fs, empty=self.empty, fill=self.fill)
        s, t = zip(*[(s['repr'], t['repr']) for s, t in self])
        gap = ' ' if self.word_level else ''
        return '\n'.join((gap.join(s), gap.join(t)))

    
    def __iter__(self):
        """Yield each word pair in the alignment"""
        if not hasattr(self, '_s_align'):
            self._align()
        for s, t in zip(self._s_align, self._t_align):
            yield (s, t)


    def __init__(self, s, t, weights=None, default_weight=1.0, m=2, n=8,
                 word_level=True, empty='*', fill='_', color=False):
        self.s = s
        self.t = t
        self._m = m
        self._n = n
        if weights is None:
            weights = defaultdict((lambda : default_weight))
        elif not isinstance(weights, defaultdict):
            weights = defaultdict((lambda : default_weight), weights)
        self.weights = weights
        self.word_level = word_level        
        self.empty = empty
        self.fill = fill
        self.color = color
        if color:
            self._color_fs = self._color_texts()
        else:
            self._color_fs = None


    @staticmethod
    def _compute_f(D, I, S):
        """Computes a factor `f` to reconcile that replacement errors are less detrimental 
        than insertion/deletion errors.

            - f is on [0.5, 1]
            - f == 0.5 -> all replacements
            - f == 1 -> all non-replacements
            - f * (D_S + I_S) = (S + D + I), where D_S and I_S include contributions from 
              replacements.

        Args:
            D (int): Number of deletion errors (false negatives).
            I (int): Number of insertion errors (false positives).
            S (int): Number of replacement errors (false positive/negatives pairs).

        Returns:
            float: A factor `f` which is 0.5 when all errors are replacements and 1.0
            when all errors are not replacements.

        """
        return 1 - ((S / (I + D)) if (I or D) else 0)
        
    
    @staticmethod
    def _weighted_counts(correct, deleted, inserted, weights):
        """Compute weighted counts of hits, deletions, and insertions"""
        wH, wD, wI = 0, 0, 0
        for token in set(correct + deleted + inserted):
            w = weights[token] if weights is not None else 1
            wH += w * correct.count(token)
            wD += w * deleted.count(token)
            wI += w * inserted.count(token)
        return wH, wD, wI        


    @staticmethod
    def _count_consecutive_f(seq, f):
        """Compute the maximum number of consecutive items in a
        sequence which return True some criterion function f."""
        counter = 0
        greatest = 0
        for j, item in enumerate(seq):
            if f(item):
                counter += 1
            else:
                if counter > greatest:
                    greatest = counter
                counter = 0
        if counter > greatest:
            greatest = counter
        return greatest


    @staticmethod
    def _mn_grams(seq, m, n):
        """Compute a list of n-grams found in a sequence of tokens for a range of orders.
        
        Args:
            tokens (seq): A sequence of tokens.
            m (int): The minimum order of gram to extract.
            n (int): The maximum order of gram to extract.

        Returns:
            list: List of n-grams found.

        """
        grams = []
        for o in range(m, n + 1):
            for p in range(o, len(seq) + 1):
                grams.append(tuple(seq[p - o:p]))
        return grams


    def _align(self):
        """Compute a full alignment and store associated analysis"""
        if self.word_level:
            s_words = self.s.split()
            t_words = self.t.split()
        else:
            s_words = list(self.s)
            t_words = list(self.t)

        words = set(s_words + t_words)
        w2c = dict((w, chr(j)) for j, w in enumerate(words))
        s_chars = [w2c[w] for w in s_words]
        t_chars = [w2c[w] for w in t_words]
        state = s_words[:]
        s, t = ''.join(s_chars), ''.join(t_chars)
        s_align = [dict(text=c, correct=True) for c in s_words]
        t_align = [dict(text=c, correct=True) for c in t_words]
        deleted, inserted = [], []
        D, I, S = 0, 0, 0
        for opt, spos, dpos in editops(s, t):
            if opt == 'delete':
                inserted.append(state.pop(spos + I - D))
                s_align[spos + I]['correct'] = False
                t_align.insert(dpos + D, dict(text=None, correct=False))
                D += 1
            elif opt == 'insert':
                deleted.append(t_words[dpos])
                state.insert(spos + I - D, t_words[dpos])
                s_align.insert(spos + I, dict(text=None, correct=False))
                t_align[spos + I]['correct'] = False
                I += 1
            elif opt == 'replace':
                inserted.append(state[spos + I - D])
                deleted.append(t_words[dpos])
                state[spos + I - D] = t_words[dpos]
                s_align[spos + I]['correct'] = False
                t_align[spos + I]['correct'] = False
                S += 1
            else:
                raise ValueError('unexpected edit operation "%s"' % opt)

        self._s_words = s_words
        self._t_words = t_words
        self._s_align = s_align
        self._t_align = t_align
        self._correct = [s['text'] for s in s_align if s['correct']]
        self._deleted = deleted
        self._inserted = inserted
        self._incorrect = deleted + inserted
        self._consecutive_correct  = self._count_consecutive_f(s_align,
                                                               lambda t: t['correct'])
        self._consecutive_deleted  = self._count_consecutive_f(s_align,
                                                               lambda t: t['text'] is None)
        self._consecutive_inserted = self._count_consecutive_f(t_align,
                                                               lambda t: t['text'] is None)
        # switch counts of insertions/deletions to remain consistent
        # (counted insertion/deletion opertions, which are deletion/insertion mistakes)
        self.H, self.I, self.D, self.S = len(self._correct), D, I, S
        self.N = self.H + S
        self.N1 = len(t_words)
        self.N2 = len(s_words)

        if self._n >= self._m:
            # NOTE: by default the gram calculation is ignored (default n < m)
            self._incorrect_ngrams = self._mn_grams(t_words, self._m, self._n)
            valid_gram = lambda gram: all(w['correct'] for w in gram)
            aligned_grams = self._mn_grams(s_align, self._m, self._n)
            self._correct_ngrams = list(filter(valid_gram, aligned_grams))
            for i, cg in enumerate(self._correct_ngrams):
                cg = tuple(w['text'] for w in cg)
                self._correct_ngrams[i] = cg
                self._incorrect_ngrams.remove(cg)
        else:
            self._incorrect_ngrams = None
            self._correct_ngrams = None

        if self.word_level:
            self._word_level_analysis()


    def _word_level_analysis(self):
        """Compute all word level metrics via alignment"""
        if not hasattr(self, '_s_align'):
            self.word_level = True
            self._align()

        D_S, I_S = len(self._deleted), len(self._inserted)
        f = self._compute_f(D_S, I_S, self.S)
        wH, wD_S, wI_S = self._weighted_counts(
            self._correct, self._deleted, self._inserted, self.weights)

        if self.N1 == 0:
            # NOTE: these are technically approximate (N1 == 0 -> WER == +inf)
            self._WER  = 100.0 * f * ( D_S +  I_S)
            self._SWER = 100.0 * f * (wD_S + wI_S)
        else:
            self._WER  = 100.0 * f * ( D_S +  I_S) / self.N1
            self._SWER = 100.0 * f * (wD_S + wI_S) / self.N1

        if self.N1 == 0 and self.N2 == 0:
            self._NWER  = None
            self._SNWER = None
        else:
            self._NWER  = 100 * f * ( D_S +  I_S) / max(self.N1, self.N2)
            self._SNWER = 100 * f * (wD_S + wI_S) / max(self.N1, self.N2)

        if any((self.H, D_S, I_S)):
            self._MER  = 100 * f * ( D_S +  I_S) / (self.H + f * ( D_S +  I_S))
        else:
            self._MER  = None
        if any((wH, wD_S, wI_S)):
            self._SMER = 100 * f * (wD_S + wI_S) / (    wH + f * (wD_S + wI_S))
        else:
            self._SMER = None

        if not (self.N1 == 0 or self.N2 == 0):
            self._WIL  = 100 * (1 - self.H ** 2 / (self.N1 * self.N2))
            self._SWIL = 100 * (1 -     wH ** 2 / (self.N1 * self.N2))
        else:
            self._WIL  = None
            self._SWIL = None


    def mirror_editops(self, u):
        """Mirror editops of alignment on sequence u
        (compute v, where v is to u as t is to s)"""
        if not hasattr(self, '_s_align'):
            self._align()
        u, v = u[:], []
        for s, t in self:
            if not s['text'] is None:
                o = u.pop(0)
            if not t['text'] is None:
                v.append(o)
        return v

    
    @property
    def alignment(self):
        return self.__repr__()


    @property
    def word_distance(self):
        if not hasattr(self, '_word_distance'):
            s_words = self.s.split()
            t_words = self.t.split()
            words = set(s_words + t_words)
            w2c = dict((w, chr(j)) for j, w in enumerate(words))
            s_chars = [w2c[w] for w in s_words]
            t_chars = [w2c[w] for w in t_words]
            s, t = ''.join(s_chars), ''.join(t_chars)
            self._word_distance = editdistance(s, t)
            self._N1_word = len(t_words)
        return self._word_distance

    
    @property
    def WER(self):
        """Word error rate"""
        if not hasattr(self, '_WER'):
            edits = self.word_distance
            # NOTE: this is technically approximate (N1 == 0 -> WER == +inf)
            self._WER = 100.0 * (edits if self._N1_word == 0 else edits / self._N1_word)
        return self._WER


    @property
    def N1_word(self):
        if not hasattr(self, '_N1_word'):
            edits = self.word_distance
        return self._N1_word


    @property
    def SWER(self):
        """Salient word error rate"""
        if not hasattr(self, '_SWER'):
            self._word_level_analysis()
        return self._SWER


    @property
    def NWER(self):
        """Normalized word error rate"""
        if not hasattr(self, '_NWER'):
            self._word_level_analysis()
        return self._NWER


    @property
    def SNWER(self):
        """Salient normalized word error rate"""
        if not hasattr(self, '_SNWER'):
            self._word_level_analysis()
        return self._SNWER


    @property
    def MER(self):
        """Match error rate"""
        if not hasattr(self, '_MER'):
            self._word_level_analysis()
        return self._MER


    @property
    def SMER(self):
        """Salient match error rate"""
        if not hasattr(self, '_SMER'):
            self._word_level_analysis()
        return self._SMER


    @property
    def WIL(self):
        """Word information loss"""
        if not hasattr(self, '_WIL'):
            self._word_level_analysis()
        return self._WIL


    @property
    def SWIL(self):
        """Salient word information loss"""
        if not hasattr(self, '_SWIL'):
            self._word_level_analysis()
        return self._SWIL
    

    @property
    def char_distance(self):
        if not hasattr(self, '_char_distance'):
            s, t = ''.join(self.s.split()), ''.join(self.t.split())
            self._char_distance = editdistance(s, t)
            self._N1_char = len(t)
        return self._char_distance

    
    @property
    def CER(self):
        "Character error rate"
        if not hasattr(self, '_CER'):
            edits = self.char_distance
            # NOTE: this is technically approximate (N1 == 0 -> CER == +inf)
            self._CER = 100.0 * (edits if self._N1_char == 0 else edits / self._N1_char)
        return self._CER


    @property
    def N1_char(self):
        if not hasattr(self, '_N1_char'):
            edits = self.char_distance
        return self._N1_char


    @property
    def n_consecutive_correct(self):
        if not hasattr(self, '_consecutive_correct'):
            self._align()
        return self._consecutive_correct


    @property
    def n_consecutive_deleted(self):
        if not hasattr(self, '_consecutive_deleted'):
            self._align()
        return self._consecutive_deleted


    @property
    def n_consecutive_inserted(self):
        if not hasattr(self, '_consecutive_inserted'):
            self._align()
        return self._consecutive_inserted


    @property
    def analysis(self):
        """Provide full word level analysis as a dictionary"""
        if not self.word_level or not hasattr(self, '_s_align'):
            self._word_level_analysis()

        # compute colorless, padded representation of alignment
        s_aligned, t_aligned = [], []
        for u, v in self:
            u, v = self._repr_aligned_word_pair(u, v,
                    empty=self.empty, fill=self.fill)
            s_aligned.append(u)
            t_aligned.append(v)
        s_aligned, t_aligned = ' '.join(s_aligned), ' '.join(t_aligned)

        analysis = {
            'n_consecutive_correct': self._consecutive_correct,
            'n_consecutive_deleted': self._consecutive_deleted,
            'n_consecutive_inserted': self._consecutive_inserted, 
            'correct_grams': self._correct_ngrams, 
            'incorrect_grams': self._incorrect_ngrams, 
            'correct'  : self._correct, 
            'incorrect': (self._deleted + self._inserted), 
            'deleted'  : self._deleted, 
            'inserted' : self._inserted, 
            'aligned_hypothesis': s_aligned,
            'aligned_reference' : t_aligned,
            'hypothesis': self.s,
            'reference' : self.t,
            'H': self.H, 'S': self.S, 'D': self.D, 'I': self.I,
            'N1': self.N1, 'N2': self.N2, 'N': self.N,
            'CER': self.CER,
            'WER' : self.WER,  'SWER' : self.SWER,
            'NWER': self.NWER, 'SNWER': self.SNWER,
            'MER' : self.MER,  'SMER' : self.SMER,
            'WIL' : self.WIL,  'SWIL' : self.SWIL,
        }
        return analysis


    @classmethod
    def aggregate(cls, hyps, refs, **kws):
        """FIXME
        Aggregate word and n-gram specific statistics from a set of analyses on
        many hypothesis references pairs.

        Args:
            analyses (seq): Sequence of analysis results from `analyze`.

        Returns:
            2-element tuple: Lists of statistics for words and n-grams where
            each element in each list contains aggregated statistics for a single
            word or n-gram observed in `analyses`.

            Each entry in the list of word statistics includes:
                - correct (int): Number of true positives for the word.
                - incorrect (int): Number of false positives and negatives for the word.
                - deleted (int): Number of false negatives for the word.
                - inserted (int): Number of false positives for the word.
                - total (int): `correct` + `incorrect` for the word.
                - errorrate (float): `incorrect` / `total` for the word.
                - precision (float): `correct` / (`correct` + `inserted`)
                - recall (float): `correct` / (`correct` + `deleted`)
                - f_measure (float): 2 * `precision` * `recall` / (`precision` + `recall`)

            Each entry in the list of n-gram (n > 1) statistics includes:
                - correct_grams (int): Number of true positives for the n-gram.
                - incorrect_grams (int): Number of false positives and negatives for the n-gram.
                - gram_total (int): `correct_grams` + `incorrect_grams` for the n-gram.
                - gram_errorrate (float): `incorrect_grams` / `gram_total` for the n-gram.

        """
        analyses = [cls(h, r, **kws).analysis for h, r in zip(hyps, refs)]

        counts = {
            'correct': Counter(),
            'incorrect': Counter(),
            'deleted': Counter(),
            'inserted': Counter(),
            'correct_grams': Counter(),
            'incorrect_grams': Counter(),
        }
        keys = tuple(counts.keys())
        for e in analyses:
            for k in keys:
                counts[k].update(e[k])

        totals = Counter()
        lexicon = set()
        for c in ('correct', 'incorrect'):
            totals += counts[c]
            for w in counts[c]:
                lexicon.add(w)
        counts['total'] = totals

        gram_totals = Counter()
        gram_lexicon = set()
        for c in ('correct_grams', 'incorrect_grams'):
            gram_totals += counts[c]
            for g in counts[c]:
                gram_lexicon.add(g)
        counts['gram_total'] = gram_totals

        rates, precisions, recalls, f_0s = {}, {}, {}, {}
        for w in lexicon:
            rates[w] = counts['incorrect'][w] / counts['total'][w]
            if counts['correct'][w] > 0 or counts['inserted'][w] > 0:
                precisions[w] = counts['correct'][w] / (counts['correct'][w] + counts['inserted'][w])
            else:
                precisions[w] = -1.0
            if counts['correct'][w] > 0 or counts['deleted'][w] > 0:
                recalls[w] = counts['correct'][w] / (counts['correct'][w] + counts['deleted'][w])
            else:
                recalls[w] = -1.0
            if precisions[w] > 0 or recalls[w] > 0:
                f_0s[w] = 2 * precisions[w] * recalls[w] / (precisions[w] + recalls[w])
            else:
                f_0s[w] = -1.0

        counts['errorrate'] = rates
        counts['precision'], counts['recall'] = precisions, recalls
        counts['f_measure'] = f_0s

        gram_rates = {}
        for g in gram_lexicon:
            gram_rates[g] = counts['incorrect_grams'][g] / counts['gram_total'][g]
        counts['gram_errorrate'] = gram_rates

        for w in lexicon:
            assert(counts['total'][w] == (counts['correct'][w] + counts['incorrect'][w]))
            assert(counts['incorrect'][w] == (counts['deleted'][w] + counts['inserted'][w]))
            assert(0.0 <= counts['errorrate'][w] <= 1.0)
        assert(len(lexicon) == len(list(totals.keys())))

        for g in gram_lexicon:
            assert(counts['gram_total'][g] == (counts['correct_grams'][g] + counts['incorrect_grams'][g]))
            assert(0.0 <= counts['gram_errorrate'][g] <= 1.0)
        assert(len(gram_lexicon) == len(list(gram_totals.keys())))

        labels = list(counts.keys())
        gram_labels = [l for l in labels if 'gram' in l]
        word_labels = [l for l in labels if not l in gram_labels]

        words = []
        for word in lexicon:
            entry = {'word': word}
            for label in word_labels:
                entry[label] = counts[label][word] if word in counts[label] else 0
            words.append(entry)
        words = sorted(words, key=(lambda w: w['total']), reverse=True)

        grams = []
        for gram in gram_lexicon:
            entry = {'gram': gram}
            for label in gram_labels:
                entry[label] = counts[label][gram] if gram in counts[label] else 0
            grams.append(entry)
        grams = sorted(grams, key=(lambda g: g['gram_total']), reverse=True)

        return analyses, words, grams
