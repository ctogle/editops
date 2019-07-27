from editops import Alignment


def test_repr():
    a, b = 'version of a string one', 'another version of it'
    assert Alignment(a, b).__repr__() == ('******* version of a string one\n'
                                          'another version of * ****** it_')

    a, b = 'abcdhijkmnp', 'acdefgijkp'
    assert Alignment(a, b, word_level=False).__repr__() == ('abcd**hijkmnp\n'
                                                            'a*cdefgijk**p')


def test_weights():
    a, b = 'version of a string one', 'another version of it'

    # salient errors are unaffected when all weights are 1
    analysis = Alignment(a, b, weights={}, default_weight=1).analysis
    assert analysis['WER'] == analysis['SWER']
    assert analysis['NWER'] == analysis['SNWER']
    assert analysis['MER'] == analysis['SMER']
    assert analysis['WIL'] == analysis['SWIL']

    # 0 weighting of correct word does not affect SWER/SNWER
    # 0 weighting of correct word increases SMER
    # 0 weighting of correct word increases SWIL
    analysis = Alignment(a, b, weights={'of': 0}, default_weight=1).analysis
    assert analysis['WER'] == analysis['SWER']
    assert analysis['NWER'] == analysis['SNWER']
    assert analysis['MER'] < analysis['SMER']
    assert analysis['WIL'] < analysis['SWIL']

    # 0 weighting of incorrect word decreases SWER/SNWER
    # 0 weighting of incorrect word decreases SMER
    # 0 weighting of incorrect word does not affect SWIL
    analysis = Alignment(a, b, weights={'another': 0}, default_weight=1).analysis
    assert analysis['WER'] > analysis['SWER']
    assert analysis['NWER'] > analysis['SNWER']
    assert analysis['MER'] > analysis['SMER']
    assert analysis['WIL'] == analysis['SWIL']

    # SWER/SNWER is 0 when all weights are 0
    # SMER is None (undefined) when all weights are 0
    # SWIL is 100 when all weights are 0 
    analysis = Alignment(a, b, weights={}, default_weight=0).analysis
    assert analysis['WER'] > analysis['SWER'] and analysis['SWER'] == 0
    assert analysis['NWER'] > analysis['SNWER'] and analysis['SWER'] == 0
    assert analysis['MER'] > 0 and analysis['SMER'] == None
    assert analysis['WIL'] < analysis['SWIL'] and analysis['SWIL'] == 100


def test_word_level_analysis():
    """Examples taken from table 1 from:

    https://pdfs.semanticscholar.org/a3b6/4b62563a27fafbc846597846fc427e863621.pdf 
    """
    analysis = Alignment('x', 'x').analysis
    assert analysis['hypothesis'] == 'x'
    assert analysis['reference'] == 'x'
    assert analysis['H'] == 1
    assert analysis['S'] == 0
    assert analysis['D'] == 0
    assert analysis['I'] == 0
    assert analysis['WER'] == 0
    assert analysis['MER'] == 0
    assert analysis['WIL'] == 0
    assert analysis['N1'] == 1
    assert analysis['N2'] == 1
    assert analysis['NWER'] == analysis['WER'] * (analysis['N1'] / max(analysis['N1'], analysis['N2']))
    assert analysis['CER'] == analysis['WER']
    assert analysis['SWER'] == analysis['WER']
    assert analysis['SNWER'] == analysis['NWER']
    assert analysis['SMER'] == analysis['MER']
    assert analysis['SWIL'] == analysis['WIL']

    analysis = Alignment('x x y y', 'x').analysis
    assert analysis['hypothesis'] == 'x x y y'
    assert analysis['reference'] == 'x'
    assert analysis['H'] == 1
    assert analysis['S'] == 0
    assert analysis['D'] == 0
    assert analysis['I'] == 3
    assert analysis['WER'] == 300
    assert analysis['MER'] == 75
    assert analysis['WIL'] == 75
    assert analysis['N1'] == 1
    assert analysis['N2'] == 4
    assert analysis['NWER'] == analysis['WER'] * (analysis['N1'] / max(analysis['N1'], analysis['N2']))
    assert analysis['CER'] == analysis['WER']
    assert analysis['SWER'] == analysis['WER']
    assert analysis['SNWER'] == analysis['NWER']
    assert analysis['SMER'] == analysis['MER']
    assert analysis['SWIL'] == analysis['WIL']

    analysis = Alignment('x z', 'x y x').analysis
    assert analysis['hypothesis'] == 'x z'
    assert analysis['reference'] == 'x y x'
    assert analysis['H'] == 1
    assert analysis['S'] == 1
    assert analysis['D'] == 1
    assert analysis['I'] == 0
    assert round(analysis['WER'], 0) == 67
    assert round(analysis['MER'], 0) == 67
    assert round(analysis['WIL'], 0) == 83
    assert analysis['N1'] == 3
    assert analysis['N2'] == 2
    assert analysis['NWER'] == analysis['WER'] * (analysis['N1'] / max(analysis['N1'], analysis['N2']))
    assert round(analysis['CER'], 0) == round(analysis['WER'], 0)
    assert analysis['SWER'] == analysis['WER']
    assert analysis['SNWER'] == analysis['NWER']
    assert analysis['SMER'] == analysis['MER']
    assert analysis['SWIL'] == analysis['WIL']

    analysis = Alignment('x', 'y').analysis
    assert analysis['hypothesis'] == 'x'
    assert analysis['reference'] == 'y'
    assert analysis['H'] == 0
    assert analysis['S'] == 1
    assert analysis['D'] == 0
    assert analysis['I'] == 0
    assert analysis['WER'] == 100
    assert analysis['MER'] == 100
    assert analysis['WIL'] == 100
    assert analysis['N1'] == 1
    assert analysis['N2'] == 1
    assert analysis['NWER'] == analysis['WER'] * (analysis['N1'] / max(analysis['N1'], analysis['N2']))
    assert analysis['CER'] == analysis['WER']
    assert analysis['SWER'] == analysis['WER']
    assert analysis['SNWER'] == analysis['NWER']
    assert analysis['SMER'] == analysis['MER']
    assert analysis['SWIL'] == analysis['WIL']

    analysis = Alignment('y z', 'x').analysis
    assert analysis['hypothesis'] == 'y z'
    assert analysis['reference'] == 'x'
    assert analysis['H'] == 0
    assert analysis['S'] == 1
    assert analysis['D'] == 0
    assert analysis['I'] == 1
    assert analysis['WER'] == 200
    assert analysis['MER'] == 100
    assert analysis['WIL'] == 100
    assert analysis['N1'] == 1
    assert analysis['N2'] == 2
    assert analysis['NWER'] == analysis['WER'] * (analysis['N1'] / max(analysis['N1'], analysis['N2']))
    assert analysis['CER'] == analysis['WER']
    assert analysis['SWER'] == analysis['WER']
    assert analysis['SNWER'] == analysis['NWER']
    assert analysis['SMER'] == analysis['MER']
    assert analysis['SWIL'] == analysis['WIL']


if __name__ == '__main__':
    test_repr()
    test_weights()
    test_word_level_analysis()
