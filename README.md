# Predictive Text Using an LLM
A simple application that provides an interface to write text using suggestions from an LLM.

Right now, it can be run by creating the `PredictiveText` class and calling `.predict()` on the resulting object.

Guide:
Call `Predictive_Text.predict` to enter interactive mode.
Interactive mode works as follows:
The model will provide a set of numbered predictions, and you can append a prediction to your prompt by entering the number of the prediction.
There are also a number of other operations which can be selected by prefixing your input with a symbol:

* `]`: Extend your prompt by the literal text following the `]`.

* `<`: Undo your previous action.  Undo history remembers the full session.

* `t`: Test an option.  Generates a series of tokens of length equal to test_n to show a possible completion from a given option.  Can be followed by either a number, to test a numbered token, literal text prefixed by `]` to test that, or nothing to see what the model predicts for your current prompt.

* `c`: Two forms, either c followed by an int or c followed by an expression of the form int:int.  Form 1 continues the current prompt for a length in tokens equal to the number provided, choosing the most likely token.  Form 2 continues the current prompt for a length in tokens equal to the first number provided, choosing the token at index equal to the second number provided, with tokens ordered in decreasing probability.  Note, form 1 is much faster, but updates the history (used for undoing) only after the full operation, whereas form 2 updates the history after each token, but is slow.

* f: Print the current prompt with formatting.

* !: Quit editing.  The constructed text will be available through the `prompt` method on the `PredictiveText` object.
