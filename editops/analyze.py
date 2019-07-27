"""Utility entry point for analyzing one or more samples
storing results on disk or printing to terminal"""
import argparse
import json
import os
import tqdm
from editops import Alignment

# TODO: support saliency weights from a file/string
# TODO: support m to n order gram checking

if __name__ == '__main__':
    description = 'Analyze pairs of strings'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--hyp', default='put an hypothesis here',
                        help='Hypothesis text for alignment (string or text file)')
    parser.add_argument('--ref', default='put a reference here',
                        help='Reference text for alignment (string or text file)')
    parser.add_argument('-l', '--lines', default=False, action='store_true',
                        help='Split the input hyp/ref text on newlines for 1 - 1 analysis')
    parser.add_argument('-o', '--output', default=None,
                        help='Optional path at which to store full alignment analysis')
    parser.add_argument('-v', '--verbose', default=False, action='store_true',
                        help='Optional print the full alignment and WER/CER for each sample')
    args = parser.parse_args()

    if os.path.isfile(args.hyp):
        with open(args.hyp, 'r') as f:
            hyp = f.read()
    else:
        hyp = args.hyp

    if os.path.isfile(args.ref):
        with open(args.ref, 'r') as f:
            ref = f.read()
    else:
        ref = args.ref

    if args.lines:
        hyps, refs = hyp.rstrip('\n').split('\n'), ref.rstrip('\n').split('\n')
        assert len(hyps) == len(refs)
    else:
        hyps, refs = [hyp.rstrip('\n')], [ref.rstrip('\n')]

    if args.output is not None:
        output = open(args.output, 'w')

    if not args.verbose:
        pbar = tqdm.tqdm(desc='analyzing', total=len(hyps))

    ref_word_count, word_edits, ref_char_count, char_edits = 0, 0, 0, 0
    for hyp, ref in zip(hyps, refs):
        a = Alignment(hyp, ref, word_level=True, color=True)
        char_edits += a.char_distance
        word_edits += a.word_distance
        ref_char_count += a.N1_char
        ref_word_count += a.N1_word

        if args.verbose:
            print(f'{a.alignment}\nWER: {a.WER:.02f}\nCER: {a.CER:.02f}')
        else:
            pbar.update(1)

        if args.output is not None:
            # TODO: support non-verbose json output?
            output.write(f'{json.dumps(a.analysis)}\n')

    if args.output is not None:
        output.close()

    if not args.verbose:
        pbar.close()

    WER = 100.0 * word_edits / ref_word_count
    CER = 100.0 * char_edits / ref_char_count
    print('=' * 50, f'\nWER: {WER:.02f}\nCER: {CER:.02f}')
