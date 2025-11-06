class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error: expected word")
        return self.s[start:self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception(f"Parsing error: expected {literal}")
        self.i += 1

    def peek_literal(self, literal) -> bool:
        return self.i < len(self.s) and self.s[self.i] == literal

    def pair(self):
        self.whitespace()
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val

    def body(self):
        pairs = {}
        while self.i < len(self.s):
            if self.peek_literal("}"):
                break
            prop, val = self.pair()
            pairs[prop] = val
            self.whitespace()
            self.literal(";")
            self.whitespace()
        return pairs

    # TODO
    def selector(self):
        main = self.word()
        self.whitespace()
        if self.peek_literal('.'):
            self.literal('.')
            main += '.' + self.word()
        if self.peek_literal(':'):
            self.literal(':')
            main += ':' + self.word()
        return main

    def style(self):
        elems = []
        while self.i < len(self.s):
            self.whitespace()
            name = self.selector()
            self.whitespace()
            self.literal("{")
            self.whitespace()
            pairs = self.body()
            self.whitespace()
            self.literal("}")
            self.whitespace()
            elems.append((name, pairs))
        return elems


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    style = load_file("files/style.css")
    elems = CSSParser(style).style()
    for name, pairs in elems:
        print(name)
        print(pairs)
