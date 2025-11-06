from calliopy.gui.ui import _create_element


class UIParser:
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
            raise Exception("Parsing error")
        return self.s[start:self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    def read_until(self, literal):
        start = self.i
        while self.i < len(self.s) and self.s[self.i] != literal:
            self.i += 1
        return self.s[start:self.i]

    def peek_literal(self, literal) -> bool:
        return self.i < len(self.s) and self.s[self.i] == literal

    def attrs(self):
        attrs = {}
        while not self.peek_literal('>'):
            self.whitespace()
            name = self.word()
            self.literal('=')
            char = "'"
            if self.peek_literal('"'):
                char = '"'
            self.literal(char)
            value = self.read_until(char)
            self.literal(char)
            attrs[name] = value
        return attrs

    def tag(self):
        closing = False
        self.literal('<')
        if self.peek_literal('/'):
            self.literal('/')
            closing = True
        tag = self.word()
        self.whitespace()
        attrs = self.attrs()
        self.literal('>')
        return closing, tag, attrs

    def body(self, style=None, dispatcher=None):
        stack = []
        root = None

        while self.i < len(self.s):
            self.whitespace()
            if self.peek_literal('<'):
                closing, tag, attrs = self.tag()
                if closing:
                    elem = stack.pop()
                    if not stack:
                        root = elem
                    else:
                        stack[-1].children.append(elem)
                else:
                    classes = attrs.get('class', [])
                    if type(classes) is str:
                        classes = classes.split()
                    src = attrs.get('src')
                    action = attrs.get('onclick')
                    elem = _create_element(
                            tag, style, classes, src, dispatcher, action
                    )
                    stack.append(elem)
            else:
                text = self.read_until('<').strip()
                if stack:
                    stack[-1].text = text

        return root


if __name__ == "__main__":
    def load_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    text = load_file("files/layout.ui")
    tag = UIParser(text).body()
    tag.print()
