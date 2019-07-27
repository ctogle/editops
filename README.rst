=======
editops
=======

Character and word alignment based analysis of unicode string pairs using Levenshtein edit distance and operations.

Lazily evaluated OO interface avoids full alignment calculation until necessary while cheaply providing typical 
error measures (word and character error rates) or more obscure measures (e.g. word information loss, match error rate).

Computes saliency-weighted analogs of word level error measures.

Aggregates word/n-gram level statistics (e.g. precision, recall).

Prints visually useful representations.

------------
Installation
------------

Installs via pip:

.. code-block:: bash

    git clone https://github.com/ctogle/editops
    cd editops
    pip install .


-----
Usage
-----

CLI
----

- Prints weighted average of WER/CER over all samples
- Input can be text or files containing text (--hyp and --ref)
- Handles 1+ pairs of strings to compare (--lines option)
- Optionally displays full alignment/WER/CER for each sample (--verbose)
- Optionally stores full analysis in jsonl output file (--output)

.. code-block:: bash

    python -m editops.analyze --help


Python
----

.. code-block:: python

    hyp = "i'm just a string!"
    ref = "i'm also just a string?"
    from editops import Alignment
    a = Alignment(hyp, ref, color=True)
    print(a)
    print(a.CER, a.WER, a.NWER, a.MER, a.WIL)


-----------
Performance
-----------

The speed of the edit distance calculation is compared to other available python libraries.

* `edit_distance <https://pypi.org/project/Edit_Distance/>`_
* `pylev <https://pypi.org/project/pylev/>`_
* `pyxdameraulevenshtein <https://pypi.org/project/pyxDamerauLevenshtein/>`_
* `python-Levenshtein <https://pypi.org/project/python-Levenshtein/>`_
* `editdistance <https://pypi.org/project/editdistance/>`_

.. code-block:: python

    a = 'fsffvfdsbbdfvvdavavavavavava'
    b = 'fvdaabavvvvvadvdvavavadfsfsdafvvav'

    from edit_distance import SequenceMatcher
    %timeit SequenceMatcher(a=a, b=b).distance()
    # 1000 loops, best of 3: 1.18 ms per loop

    from pylev import levenshtein as pylev_distance
    %timeit pylev_distance(a, b)
    # 1000 loops, best of 3: 260 µs per loop

    from pyxdameraulevenshtein import damerau_levenshtein_distance as pyxdameraulevenshtein_distance
    %timeit pyxdameraulevenshtein_distance(a, b)
    # 10000 loops, best of 3: 73.6 µs per loop

    from Levenshtein import distance as levenshtein_distance
    %timeit levenshtein_distance(a, b)
    # 100000 loops, best of 3: 2.02 µs per loop

    from editdistance import eval as editdistance_distance
    %timeit editdistance_distance(a, b)
    # 1000000 loops, best of 3: 1.79 µs per loop

    from editops import editdistance as editops_distance
    %timeit editops_distance(a, b)
    # 100000 loops, best of 3: 6.38 µs per loop


The edit distance calculation of `editops` is faster than that of all but `python-Levenshtein` and `editdistance`, 
though `editops` also exposes the set of edit operations via the method `editops`. 
`python-Levenshtein` and `edit_distance` expose this information, though `editops` is significantly faster 
than `edit_distance` and more liberally licensed than `python-Levenshtein`.

.. code-block:: python

    a = 'fsffvfdsbbdfvvdavavavavavava'
    b = 'fvdaabavvvvvadvdvavavadfsfsdafvvav'

    from edit_distance import SequenceMatcher
    %timeit SequenceMatcher(a=a, b=b).get_opcodes()
    # 1000 loops, best of 3: 1.64 ms per loop

    from Levenshtein import editops as levenshtein_editops
    %timeit levenshtein_editops(a, b)
    # 100000 loops, best of 3: 3.22 µs per loop

    from editops import editops as editops_editops
    %timeit editops_editops(a, b)
    # 100000 loops, best of 3: 7.56 µs per loop

