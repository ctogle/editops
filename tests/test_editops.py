from editops import editops, editdistance


def test_editops():
    assert editops('x', 'x') == []
    assert editops('xxyy', 'x') == [('delete', 1, 1), ('delete', 2, 1), ('delete', 3, 1)]
    assert editops('xz', 'xyx') == [('insert', 1, 1), ('replace', 1, 2)]
    assert editops('x', 'y') == [('replace', 0, 0)]
    assert editops('yz', 'x') == [('delete', 0, 0), ('replace', 1, 0)]
    assert editops('abcd', 'dcd') == [('delete', 0, 0), ('replace', 1, 0)]
    assert editops('abcd', 'addcd') == [('insert', 1, 1), ('replace', 1, 2)]
    assert editops('œπ31% ^', ' πU312%') == [('replace', 0, 0), ('insert', 2, 2),
                           ('delete', 4, 5), ('replace', 5, 5), ('replace', 6, 6)]


def test_editdistance():
    assert editdistance('x', 'x') == 0
    assert editdistance('xxyy', 'x') == 3
    assert editdistance('xz', 'xyx') == 2
    assert editdistance('x', 'y') == 1
    assert editdistance('yz', 'x') == 2
    assert editdistance('abcd', 'dcd') == 2
    assert editdistance('abcd', 'addcd') == 2
    assert editdistance('œπ31% ^', ' πU312%') == 5


if __name__ == '__main__':
    test_editops()
    test_editdistance()
