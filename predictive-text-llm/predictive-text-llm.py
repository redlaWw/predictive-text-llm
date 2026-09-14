import requests
import math
import typing

class PredictiveText:
    """Guide:
        This class allows you to coöperatively write text with a model.
        Call Predictive_Text.predict to enter interactive mode.
        Interactive mode works as follows:
        The model will provide a set of numbered predictions, and you can append a
        prediction to your prompt by entering the number of the prediction.
        There are also a number of other operations which can be selected by
        prefixing your input with a symbol:
            ]: Extend your prompt by the literal text following the ].
               Syntax is 
            <: Undo your previous action.  Undo history remembers the full session.
            t: Test an option.  Generates a series of tokens of length equal to test_n
               to show a possible completion from a given option.  Can be followed by
               either a number, to test a numbered token, literal text prefixed by ] to test
               that, or nothing to see what the model predicts for your current prompt.
            c: Two forms, either c followed by an int or c followed by an expression of the form int:int.
               Form 1 continues the current prompt for a length in tokens equal to the number provided,
               choosing the most likely token.
               Form 2 continues the current prompt for a length in tokens equal to the first number provided,
               choosing the token at index equal to the second number provided,
               with tokens ordered in decreasing probability.
               Note, form 1 is much faster, but updates the history (used for undoing) only after the
               full operation, whereas form 2 updates the history after each token, but is slow.
            f: Print the current prompt with formatting.
            !: Quit editing.  The function will return with the final value of your prompt.
               If you forget to assign the return value, it will be available in the global
               predictive_text_saved until the next time you call the function.
    """


    def __init__(self,
                 address: str,
                 model: str,
                 initial: str,
                 /,
                 n_candidates: int = 50,
                 n_test: int = 30,
                 auth: Optional[str] = None):
        """Arguments:
            address: http address of model
            model  : model name
            initial: initial prompt
            n_probs: number of candidates
            test_n : number of tokens for test to generate
            auth   : authorisation token 
        """
        self.__address = address
        self.__model = model
        self.__prompt = initial
        self.n_candidates = n_candidates
        self.n_test = n_test
        self.__history = [len(initial)]
        self.__load_candidates()

    # write predictions to user
    def __write_predictions(self, reload):
        if reload:
            self.__load_candidates()
        for (i, candidate) in enumerate(self.candidates):
            self.__write_user(f"{i: >4} ({math.exp(candidate["logprob"]):.4}): {candidate["token"]!r}\n")
        

    def __load_candidates(self):
        resp = requests.post(self.__address + "/completion", json = {
            "model": self.__model,
            "n_predict": 1,
            "n_probs": self.n_candidates,
            "temperature": 0,
            "prompt": self.__prompt
        })
        self.candidates = resp.json()["completion_probabilities"][0]["top_logprobs"]

    def prompt(self):
        return self.__prompt

    def __write_prompt(self):
        self.__write_user(f"{self.__prompt!r}")

    def __extend(self, next):
        self.__write_next(next)
        self.__prompt += next
        self.__history.append(len(self.__prompt))

    # extends by candidate index, rather than string
    def __extend_index(self, index):
        self.__extend(self.candidates[index]["token"])

    def __undo(self):
        self.__history.pop()
        self.__prompt = self.__prompt[:self.__history[-1]]

    def __continue(self, raw_input):
        if ':' in raw_input:
            length_str, pos_str = raw_input.split(':') # if number of values is incorrect, ValueError exception will propagate up
            length = int(length_str, 10)
            pos = int(pos_str, 10)
            continued = ""
            while True:
                self.__extend_index(pos)
                length -= 1
                if length==0: break # while True with break avoids wasteful load (which involves a http request)
                self.__load_candidates()
        else:
            length = int(raw_input, 10)
            _, completion = self.__complete(None, length)
            self.__extend(completion)
            

    def __write_user(self, text):
        print(text)

    # used to send messages to another location that is interested in the string being built
    # e.g. the user's choices could be sent across a web connection to another application
    def __write_next(self, next):
        pass

    def __input(self, prompt):
        raw_input = input(prompt)
        return raw_input.encode("latin-1", "backslashreplace").decode("unicode_escape")

    # gets a completion of length n for self.__prompt + next, returns [self.__prompt + next, completion]
    # if next is None, uses self.__prompt instead of self.__prompt + next
    def __complete(self, next, count):
        if next is None:
            prompt = self.__prompt
        else:
            prompt = self.__prompt + next

        resp = requests.post(self.__address + "/completion", json = {
            "model": self.__model,
            "n_predict": count,
            "temperature": 0,
            "prompt": prompt
        })
        return [prompt, resp.json()["content"]]

    def __test(self, cont):
        try:
            first = cont[0]
        except IndexError:
            first = None
        match first:
            case ']':
                next = cont[1:]
            case default:
                try:
                    next_int = int(cont, 10)
                    next = self.candidates[next_int]["token"]
                except ValueError:
                    next = None
        [prompt, completion] = self.__complete(next, self.n_test)
        self.__write_user(f"{prompt+completion!r}")

    def __report_error(self, e):
        self.__write_user(f"invalid input: {e}")

    def predict(self):
        refresh = False # start with refresh False so that initial candidates aren't loaded twice
        self.__write_predictions(False)
        self.__write_prompt()
        while True:
            if refresh:
                self.__load_candidates()
                self.__write_predictions(False)
                self.__write_prompt()
            refresh = True
            
            command = self.__input("> ")
            try:
                first = command[0]
                rest = command[1:]
            except IndexError as e:
                refresh = False
                self.__report_error(e)
                continue
            match first:
                case ']':
                    if len(rest)>0:
                        self.__extend(rest)
                    else:
                        refresh = False
                        self.__report_error("empty tail")
                case '!':
                    return self.__prompt
                case '<':
                    if len(self.__history)>1:
                        self.__undo()
                    else:
                        refresh = False
                        self.__report_error("no history")
                case 't':
                    refresh = False
                    self.__test(rest)
                case 'c':
                    try:
                        self.__continue(rest)
                    except ValueError as e:
                        refresh = False
                        self.__report_error(f"{e}")
                case 'f':
                    refresh = False
                    self.__write_user(self.__prompt)
                # case number
                case default:
                    try:
                        index = int(command, 10) # use full number, not rest
                        self.__extend_index(index)
                    except ValueError as e:
                        refresh = False
                        self.__report_error(e)
                    except IndexError as e:
                        refresh = False
                        self.__report_error(e)