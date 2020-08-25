""" from https://github.com/keithito/tacotron """

"""
Defines the set of symbols used in text input to the model.

The default is a set of ASCII characters that works well for English or text that has been run through Unidecode. For other data, you can modify _characters. See TRAINING_DATA.md for details. """
from text import cmudict

_pad = "_"
_punctuation = "!'(),.:;? "
_special = "-"
_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
start_tok = "*"
end_tok = "`"
# Loop for adding Hindi characters.
# for i in range(2304, 2432) :
#    _letters+=chr(i)

# Prepend "@" to ARPAbet symbols to ensure uniqueness (some are the same as uppercase letters):
_arpabet = ["@" + s for s in cmudict.valid_symbols]

# Export all symbols:
symbols = (
    [_pad, start_tok, end_tok]
    + list(_special)
    + list(_punctuation)
    + list(_letters)
    + _arpabet
)
